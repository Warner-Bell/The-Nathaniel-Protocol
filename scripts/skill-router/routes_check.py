#!/usr/bin/env python3
"""routes_check.py - drift guard between the kernel Protocol Keyword Map
(the single source of truth for WHICH protocols exist) and routes.json (the
router's curated copy).

WHY THIS EXISTS: routes.json's protocol keyword
sets are DELIBERATELY CURATED, not a verbatim kernel copy. Noisy single tokens
(save, git, memory, session, morning, review, offer, diagnose, ...) are dropped
or replaced with phrases so the router's protocol precision holds. So we do NOT
auto-generate routes.json from the kernel -- that would undo the tuning. What
actually bites is COVERAGE drift: the kernel gains or loses a routable protocol
and routes.json silently doesn't track it. This guard turns that silent rot
into a loud failure.

Two checks:
  COVERAGE (enforced): the set of routable protocols in the kernel map ==
    the set of protocol keys in routes.json. Missing/extra -> exit 1.
  KEYWORD DRIFT (advisory): per-protocol, report kernel keywords absent from
    routes.json and vice-versa. Never fails on its own (divergence is
    intentional curation) -- it just surfaces what a human curator may want
    to review. Use --strict to make it fail too (rarely wanted).

Run:
  python3 routes_check.py            # coverage (enforced) + keyword-drift report
  python3 routes_check.py --strict   # also exit 1 on any keyword drift
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]  # scripts/skill-router/ -> repo root
ROUTES = HERE / "routes.json"
# The Protocol Keyword Map lives in ecosystem-operation.md. Deployed copy first (.kiro/), then the
# template source (.steering-files/) so the check also runs before setup.sh.
KERNEL = REPO / ".kiro" / "steering" / "ecosystem-operation.md"
if not KERNEL.exists():
    KERNEL = REPO / ".steering-files" / "steering" / "ecosystem-operation.md"

# markdown table row: | keywords | target | load | confidence |
ROW = re.compile(r"^\|(?P<kw>.+?)\|(?P<target>.+?)\|(?P<load>.+?)\|(?P<conf>.+?)\|\s*$")
BACKTICK = re.compile(r"`([^`]+)`")


def parse_kernel_protocols() -> dict:
    """Return {protocol_key: [kernel keywords]} for every ROUTABLE protocol in
    the Protocol Keyword Map table. Routable == the target cell names a real
    protocol markdown FILE (backtick-wrapped, ends in .md). Kernel-internal
    gates/sections (cognitive-integrity-check, Active Capture Protocol) and the
    'Spawn analyst subagent' row have no file target and are skipped."""
    text = KERNEL.read_text(encoding="utf-8")
    start = text.find("**Protocol Keyword Map")  # tolerate "**...Map**" and "**...Map:**"
    if start == -1:
        raise SystemExit("routes_check: Protocol Keyword Map not found in kernel")
    end = text.find("**Action Triggers**", start)
    section = text[start:end if end != -1 else len(text)]

    out = {}
    for raw in section.splitlines():
        line = raw.strip()
        m = ROW.match(line)
        if not m:
            continue
        kw = m.group("kw").strip()
        target = m.group("target").strip()
        if kw == "Keywords" or set(kw) <= set("-| "):
            continue  # header or separator row
        bt = BACKTICK.search(target)
        if not bt:
            continue  # no file target (e.g. "Spawn analyst subagent with topic")
        tok = bt.group(1)
        if not tok.endswith(".md"):
            continue  # kernel gate / section, not a routable protocol file
        key = Path(tok).stem  # patterns/behavioral-control-pipeline.md -> behavioral-control-pipeline
        out[key] = [k.strip() for k in kw.split(",") if k.strip()]
    return out


def _norm_kw(kws) -> set:
    # align the kernel's "does X support" placeholder with the router's "does it support"
    return {k.lower().replace(" x ", " it ") for k in kws}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="also fail on per-protocol keyword drift (default: advisory)")
    args = ap.parse_args()

    kernel = parse_kernel_protocols()
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))["protocols"]

    kset, rset = set(kernel), set(routes)
    missing = sorted(kset - rset)  # in kernel, not routed -> router can never suggest it
    extra = sorted(rset - kset)    # in routes, no matching kernel protocol -> stale/renamed

    fail = False
    print("=== COVERAGE (enforced) ===")
    if missing:
        fail = True
        print(f"  MISSING from routes.json ({len(missing)}): {', '.join(missing)}")
    if extra:
        fail = True
        print(f"  EXTRA in routes.json, no kernel protocol ({len(extra)}): {', '.join(extra)}")
    if not fail:
        print(f"  OK: {len(kset)} routable kernel protocols, routes.json in sync")

    print("\n=== KEYWORD DRIFT (advisory - curation is intentional) ===")
    drift = False
    for key in sorted(kset & rset):
        only_k = sorted(_norm_kw(kernel[key]) - _norm_kw(routes[key]))
        only_r = sorted(_norm_kw(routes[key]) - _norm_kw(kernel[key]))
        if only_k or only_r:
            drift = True
            print(f"  {key}:")
            if only_k:
                print(f"      kernel-only (curated out): {only_k}")
            if only_r:
                print(f"      routes-only (curated in):  {only_r}")
    if not drift:
        print("  none")

    if args.strict and drift:
        fail = True
    print(f"\n{'DRIFT' if fail else 'CLEAN'}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
