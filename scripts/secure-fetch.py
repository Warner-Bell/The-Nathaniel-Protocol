#!/usr/bin/env python3
"""MCP fetch proxy - sits between Kiro and mcp-server-fetch, filters URLs."""
import sys, json, subprocess, re, os, threading
from datetime import datetime

BLOCKED = [
    r"^https?://localhost($|[:/])", r"^https?://127\.", r"^https?://10\.",
    r"^https?://192\.168\.", r"^https?://172\.(1[6-9]|2[0-9]|3[01])\.",
    r"^https?://0[\d.]", r"^https?://0x", r"^https?://\d{8,10}(/|$)",
    r"^https?://\[::1\]",
    r"169\.254\.169\.254", r"metadata\.google\.internal",
    r"^data:", r":(22|23|25|3389|5900)(/|$)",
    r"^https?://bit\.ly(/|$)", r"^https?://tinyurl\.com(/|$)",
    r"^https?://t\.co/", r"^https?://goo\.gl(/|$)",
    r"@(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|169\.254\.)",
]
LOG = os.path.expanduser("~/.kiro/security.log")

def is_blocked(url):
    for p in BLOCKED:
        if re.search(p, url, re.IGNORECASE):
            return p
    if '?' in url and len(url.split('?', 1)[1]) > 500:
        return "query > 500 chars"
    return None

def log_event(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()} {msg}\n")

def forward_output(proc_stdout):
    for line in proc_stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

try:
    proc = subprocess.Popen(
        ["uvx", "mcp-server-fetch"] + sys.argv[1:],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        text=True, bufsize=1
    )
except FileNotFoundError:
    log_event("ERROR: uvx not found. Install uv: https://docs.astral.sh/uv/")
    sys.exit(1)

t = threading.Thread(target=forward_output, args=(proc.stdout,), daemon=True)
t.start()

try:
    for line in sys.stdin:
        forward = True
        try:
            msg = json.loads(line.strip())
            if msg.get("method") == "tools/call":
                params = msg.get("params")
                if not isinstance(params, dict):
                    forward = False
                elif params.get("name") == "fetch":
                    url = params.get("arguments", {}).get("url", "")
                    reason = is_blocked(url)
                    if reason:
                        log_event(f"BLOCKED: {url} - {reason}")
                        resp = json.dumps({
                            "jsonrpc": "2.0", "id": msg.get("id"),
                            "error": {"code": -32600, "message": f"URL blocked by security policy: {reason}"}
                        })
                        sys.stdout.write(resp + "\n")
                        sys.stdout.flush()
                        forward = False
        except Exception:
            pass
        if forward:
            proc.stdin.write(line)
            proc.stdin.flush()
except (BrokenPipeError, IOError):
    pass
finally:
    try:
        proc.stdin.close()
    except (BrokenPipeError, IOError):
        pass
    proc.wait()
