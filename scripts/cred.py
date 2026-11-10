#!/usr/bin/env python3
"""cred.py - the one way scripts reach a credential: by card id.

=== MODULE MANIFEST ===
WHAT  Resolver and drift audit for Nate's-kb/credential-registry.json (the card registry).
      A card is metadata only. Its machine-readable `resolver` block says where the value
      lives and how to extract it; this module does the extraction inside the calling
      process so the value never reaches agent context.
WHY   The registry existed from 2026-10-30 but nothing read it: scripts hardcoded store
      paths, new credentials got stored without cards, and a script prompted for a value
      that already had a card. Resolving only by card id makes an uncarded credential
      unusable, so carding becomes the path of least resistance. The audit catches the rest.
HOW   Stdlib only, plus `cryptography` for fernet-json cards (imported lazily).
      Registry writes take an fcntl lock and replace the file atomically.

SECURITY CONTRACT
  No command prints a credential value. There is deliberately no `get`/`value` command:
  an agent that can print a value will. Use `exec` to hand a value to a child process,
  or import resolve() from a script that sends it to a socket or SDK.

USAGE
  list                                    id | sensitivity | last_verified_live | what
  show   <id>                             full card (metadata only)
  check  <id> [--key K] [--pair N]        presence proof: length + sha256 prefix, never the value
  exec   <id> [--key K] [--pair N] [--as VAR] -- CMD ...
                                          run CMD with VAR=<value> in its environment
                                          (aws-profile cards set AWS_PROFILE instead)
  keys   <id>                             key NAMES in an env card's file (never values)
  intake <id>                             create/extend the blank KEY= intake file for an env card
  verified <id> [YYYY-MM-DD]              stamp last_verified_live after a successful live call
  audit  [--json]                         drift check: uncarded files, cards whose file is
                                          missing, unknown stores, never/stale verification

RESOLVER TYPES (card["resolver"])
  {"type": "env", "file": REL, "key": NAME}            KEY=value file; repeated keys -> --pair
  {"type": "fernet-json", "file": REL, "key_file": "~/.nathaniel/x.key", "field": "a.b"}
  {"type": "file", "file": REL}                        whole file, stripped
  {"type": "aws-profile", "profile": NAME}             SDK credential chain; exec sets AWS_PROFILE
  {"type": "external", "how": TEXT}                    resolved by another system (MCP, Amplify)
  Optional on any type: "covers": [glob, ...] extra repo-relative files this card accounts for,
  "site": NAME for web-login cards (looked up by web scripts via scripts/cred.js).

PYTHON API
  import cred; cred.card(id); cred.resolve(id, key=None, pair=1); cred.resolver_file(id)
  cred.login_card(site) -> (card_id, Path)
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import fnmatch
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = Path(os.environ.get("NATE_CRED_REGISTRY") or REPO / "Nate's-kb" / "credential-registry.json")
LOCK = REGISTRY.with_suffix(".json.lock")
STORE_NAME = ".secrets"
WALK_DEPTH = 3                      # stores live at asset homes, 1-3 levels deep
SKIP_DIRS = {"node_modules", ".git", ".trash", ".venv", "venv", "__pycache__", "Archive", "archive"}
STALE_DAYS = 180


class CredError(Exception):
    pass


# ---------------------------------------------------------------- registry
def load() -> dict:
    with open(REGISTRY, encoding="utf-8") as f:
        return json.load(f)


def _cards(reg: dict) -> list[dict]:
    return reg.get("cards", [])


def card(card_id: str, reg: dict | None = None) -> dict:
    for c in _cards(reg or load()):
        if c.get("id") == card_id:
            return c
    raise CredError(f"no card {card_id} in {REGISTRY.name}")


def _rel(p: str) -> Path:
    p = os.path.expanduser(p)
    return Path(p) if os.path.isabs(p) else REPO / p


def resolver_file(card_id: str) -> Path:
    r = card(card_id).get("resolver") or {}
    if not r.get("file"):
        raise CredError(f"{card_id} has no resolver.file")
    return _rel(r["file"])


def login_card(site: str) -> tuple[str, Path]:
    """Web-login card lookup by site name (content360, facebook, ...)."""
    for c in _cards(load()):
        r = c.get("resolver") or {}
        if r.get("site") == site and r.get("file"):
            return c["id"], _rel(r["file"])
    raise CredError(f"no web-login card with resolver.site={site!r}; add one to the registry")


def _write(reg: dict) -> None:
    reg.setdefault("_meta", {})["last_updated"] = datetime.date.today().isoformat()
    fd, tmp = tempfile.mkstemp(dir=REGISTRY.parent, prefix=".cred-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, REGISTRY)


class Locked:
    def __enter__(self):
        self.fh = open(LOCK, "w")
        fcntl.flock(self.fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.fh, fcntl.LOCK_UN)
        self.fh.close()


# ---------------------------------------------------------------- resolution
def _env_values(path: Path, key: str) -> list[str]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("export "):
            s = s[7:].lstrip()
        if s.startswith(key + "="):
            v = s.split("=", 1)[1].strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            out.append(v)
    return out


def resolve(card_id: str, key: str | None = None, pair: int = 1) -> str:
    """Return the credential value to the CALLING PROCESS. Never print what this returns."""
    c = card(card_id)
    r = c.get("resolver") or {}
    t = r.get("type")
    if t == "env":
        k = key or r.get("key")
        if not k:
            raise CredError(f"{card_id}: env resolver needs a key")
        path = _rel(r["file"])
        if not path.exists():
            raise CredError(f"{card_id}: resolver file missing")
        vals = [v for v in _env_values(path, k)]
        if len(vals) < pair or not vals[pair - 1]:
            raise CredError(f"{card_id}: {k} (pair {pair}) is empty or absent")
        return vals[pair - 1]
    if t == "fernet-json":
        from cryptography.fernet import Fernet  # lazy: only these cards need it
        data = json.loads(Fernet(_rel(r["key_file"]).read_bytes()).decrypt(_rel(r["file"]).read_bytes()))
        for part in (key or r.get("field", "")).split("."):
            if part:
                data = data[part]
        if not isinstance(data, str) or not data:
            raise CredError(f"{card_id}: field is empty or not a string")
        return data
    if t == "file":
        v = _rel(r["file"]).read_text(encoding="utf-8").strip()
        if not v:
            raise CredError(f"{card_id}: file is empty")
        return v
    if t == "aws-profile":
        return r["profile"]          # a profile name is not a secret; the SDK resolves keys
    raise CredError(f"{card_id}: resolver type {t!r} is not resolvable by cred.py"
                    + (f" ({r.get('how')})" if r.get("how") else ""))


# ---------------------------------------------------------------- audit
def _stores_on_disk() -> list[str]:
    found = []
    for root, dirs, _files in os.walk(REPO):
        depth = Path(root).relative_to(REPO).parts
        if STORE_NAME in dirs:
            found.append(str(Path(root, STORE_NAME).relative_to(REPO)))
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d != STORE_NAME and not d.startswith(".")
                   and len(depth) < WALK_DEPTH - 1]
    return sorted(found)


def _match(rel: str, globs) -> bool:
    return any(fnmatch.fnmatch(rel, g) for g in globs)


def audit(reg: dict | None = None) -> dict:
    reg = reg or load()
    cfg = reg.get("_audit", {})
    stores_cfg = set(cfg.get("stores", []))
    not_cred = set(reg.get("_not_credential_stores", {}))
    ignore = cfg.get("ignore", [])
    pending = [p["path"] if isinstance(p, dict) else p for p in reg.get("_pending_cards", {}).get("items", [])]

    covered = []                                # globs
    missing, unverified, stale, no_resolver = [], [], [], []
    today = datetime.date.today()
    for c in _cards(reg):
        r = c.get("resolver")
        if not r:
            no_resolver.append(c["id"])
            continue
        if r.get("file"):
            covered.append(r["file"])
            if not _rel(r["file"]).exists():
                missing.append(f"{c['id']}: {r['file']}")
        if r.get("key_file") and not _rel(r["key_file"]).exists():
            missing.append(f"{c['id']}: key_file {r['key_file']}")
        covered.extend(r.get("covers", []))
        lv = str(c.get("last_verified_live") or "")[:10]
        if not lv:
            unverified.append(c["id"])
        else:
            try:
                if (today - datetime.date.fromisoformat(lv)).days > STALE_DAYS:
                    stale.append(f"{c['id']}: {lv}")
            except ValueError:
                stale.append(f"{c['id']}: unparseable date {lv!r}")

    on_disk = _stores_on_disk()
    unknown_stores = [s for s in on_disk if s not in stores_cfg and s not in not_cred]
    uncarded, pend = [], []
    for store in sorted(stores_cfg):
        base = REPO / store
        if not base.is_dir():
            missing.append(f"store {store} configured but absent")
            continue
        for root, _d, files in os.walk(base):
            for fn in files:
                rel = str(Path(root, fn).relative_to(REPO))
                if _match(rel, ignore) or _match(rel, covered):
                    continue
                (pend if _match(rel, pending) else uncarded).append(rel)
    return {"cards": len(_cards(reg)), "stores": sorted(stores_cfg), "unknown_stores": unknown_stores,
            "uncarded": sorted(uncarded), "pending": sorted(pend), "missing": missing,
            "no_resolver": no_resolver, "hardcoded_consumers": hardcoded_consumers(cfg, reg),
            "never_verified": unverified, "stale_verification": stale}


def hardcoded_consumers(cfg: dict, reg: dict | None = None) -> list[str]:
    """Scripts that reach a CARDED credential file by path instead of by card id.
    A hit needs both a store reference and the filename stem of a carded file, so scripts that
    only read documents kept in a store (the finance readers) are not flagged. Infrastructure
    that must name the store (guards, backup tier) is allowlisted in _audit.consumer_allow."""
    allow = set(cfg.get("consumer_allow", []))
    stems = set()
    for c in _cards(reg or load()):
        r = c.get("resolver") or {}
        for f in ([r["file"]] if r.get("file") else []) + list(r.get("covers", [])):
            stem = re.split(r"[*?\[]", os.path.basename(f))[0].rstrip("-_.")
            if len(stem) < 6:                      # bare ".env": the folder name identifies it
                stem = os.path.basename(os.path.dirname(f))
            if len(stem) >= 6 and stem != STORE_NAME:
                stems.add(stem)
    hits = []
    for d in cfg.get("consumer_dirs", ["scripts"]):
        base = REPO / d
        if not base.is_dir():
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for fn in files:
                if not fn.endswith((".py", ".js", ".sh", ".mjs", ".ts")):
                    continue
                p = Path(root, fn)
                rel = str(p.relative_to(REPO))
                if rel in allow:
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                names_store = f"/{STORE_NAME}/" in text or f'"{STORE_NAME}"' in text or f"'{STORE_NAME}'" in text
                if names_store and any(re.search(r"(?:^|[/\"'\s])" + re.escape(s) + r"(?:[/\"'.\-]|$)", text, re.M)
                                       for s in stems):
                    hits.append(rel)
    return sorted(hits)


ENV_KEY_RE = re.compile(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)=")


def key_names(card_id: str) -> list[str]:
    """Key NAMES in an env-type card file. Only positively matched [A-Z][A-Z0-9_]* tokens left
    of '=' are emitted; every other line (bare values, comments, prose) is skipped unread."""
    r = card(card_id).get("resolver") or {}
    if r.get("type") != "env":
        raise CredError(f"{card_id}: keys works on env cards only")
    names = []
    for line in _rel(r["file"]).read_text(encoding="utf-8").splitlines():
        m = ENV_KEY_RE.match(line)
        if m:
            names.append(m.group(1))
    return names


# ---------------------------------------------------------------- cli
def _cmd_list(a):
    for c in _cards(load()):
        print(f"{c['id']} | {c.get('sensitivity')} | live {str(c.get('last_verified_live') or 'never')[:10]} | "
              f"{str(c.get('what'))[:80]}")


def _cmd_show(a):
    print(json.dumps(card(a.id), indent=1, ensure_ascii=False))


def _cmd_check(a):
    v = resolve(a.id, a.key, a.pair)
    print(f"{a.id}: present, {len(v)} chars, sha256:{hashlib.sha256(v.encode()).hexdigest()[:12]}")


def _cmd_exec(a):
    if not a.child:
        raise CredError("exec needs a command after --")
    cmd = a.child
    c = card(a.id)
    env = dict(os.environ)
    if (c.get("resolver") or {}).get("type") == "aws-profile":
        env["AWS_PROFILE"] = resolve(a.id)
    else:
        var = a.as_ or a.key or (c.get("resolver") or {}).get("key")
        if not var:
            raise CredError("exec needs --as VAR for this card")
        env[var] = resolve(a.id, a.key, a.pair)
    os.execvpe(cmd[0], cmd, env)


def _cmd_keys(a):
    from collections import Counter
    for k, n in Counter(key_names(a.id)).items():
        print(f"{k}" + (f" x{n}" if n > 1 else ""))


def _cmd_intake(a):
    """Create or extend the blank intake file for an env card: adds `KEY=` lines for this
    card and every other env card sharing the same file. Never touches an existing line."""
    c = card(a.id)
    r = c.get("resolver") or {}
    if r.get("type") != "env" or not r.get("file"):
        raise CredError(f"{a.id}: intake works on env cards with a resolver.file")
    path = _rel(r["file"])
    want = [x["resolver"]["key"] for x in _cards(load())
            if (x.get("resolver") or {}).get("type") == "env" and x["resolver"].get("file") == r["file"]
            and x["resolver"].get("key")]
    have = set(key_names(a.id)) if path.exists() else set()
    add = [k for k in dict.fromkeys(want) if k not in have]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        if not have:
            f.write(f"# Intake for {', '.join(x['id'] for x in _cards(load()) if (x.get('resolver') or {}).get('file') == r['file'])}."
                    " Paste values after '=' in an editor. Never paste them into chat.\n")
        for k in add:
            f.write(f"{k}=\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    print(f"{a.id}: intake {path.relative_to(REPO) if path.is_relative_to(REPO) else path} "
          f"(+{len(add)} key line(s): {', '.join(add) or 'none'})")


def _cmd_verified(a):
    day = a.date or datetime.date.today().isoformat()
    datetime.date.fromisoformat(day)
    with Locked():
        reg = load()
        card(a.id, reg)["last_verified_live"] = day
        _write(reg)
    print(f"{a.id}: last_verified_live = {day}")


def _cmd_audit(a):
    res = audit()
    if a.json:
        print(json.dumps(res, indent=1))
        return
    print(f"cards {res['cards']} | stores {len(res['stores'])}")
    for k in ("unknown_stores", "uncarded", "missing", "no_resolver", "hardcoded_consumers", "pending",
              "never_verified", "stale_verification"):
        items = res[k]
        print(f"{k}: {len(items)}")
        for i in items[:40]:
            print(f"  {i}")
        if len(items) > 40:
            print(f"  ... {len(items) - 40} more")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    child = []
    if "--" in argv:                       # exec: everything after -- is the child command
        i = argv.index("--")
        argv, child = argv[:i], argv[i + 1:]
    p = argparse.ArgumentParser(prog="cred.py", description="credential card resolver (values never printed)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=_cmd_list)
    s = sub.add_parser("show"); s.add_argument("id"); s.set_defaults(fn=_cmd_show)
    for name, fn in (("check", _cmd_check), ("exec", _cmd_exec)):
        s = sub.add_parser(name)
        s.add_argument("id"); s.add_argument("--key"); s.add_argument("--pair", type=int, default=1)
        if name == "exec":
            s.add_argument("--as", dest="as_")
        s.set_defaults(fn=fn)
    s = sub.add_parser("keys"); s.add_argument("id"); s.set_defaults(fn=_cmd_keys)
    s = sub.add_parser("intake"); s.add_argument("id"); s.set_defaults(fn=_cmd_intake)
    s = sub.add_parser("verified"); s.add_argument("id"); s.add_argument("date", nargs="?"); s.set_defaults(fn=_cmd_verified)
    s = sub.add_parser("audit"); s.add_argument("--json", action="store_true"); s.set_defaults(fn=_cmd_audit)
    a = p.parse_args(argv)
    a.child = child
    try:
        a.fn(a)
    except (CredError, KeyError, FileNotFoundError) as e:
        # Messages name cards, keys and files, never values.
        sys.exit(f"cred.py: {e}")


if __name__ == "__main__":
    main()
