# Vectorstore Setup

## Why a Virtual Environment?

PEP 668 (adopted in Ubuntu 23.04+, Debian 12+, Fedora 38+) marks system Python as "externally managed" and blocks `pip install` to prevent breaking OS packages. This affects any modern Linux including WSL.

The vectorstore requires `fastembed`, `numpy`, and `mcp` which cannot be installed to system Python on these systems.

## Solution

A vectorstore-local virtual environment (`Nate's-kb/vectorstore/.venv`) created by `setup.sh`:
- Works on all systems (PEP 668 enforced or not)
- No portability issues (venv created fresh per machine)
- Scripts run from vectorstore dir with local imports
- MCP server uses a wrapper script (`run-server.sh`) that handles paths with spaces correctly

## Requirements

- `uv` package manager (recommended) OR standard `python3 -m venv`
- ~202MB disk space for dependencies

## Manual Setup (if not using setup.sh)

```bash
cd Nate's-kb/vectorstore

# With uv (preferred)
uv venv .venv --relocatable
source .venv/bin/activate
uv pip install fastembed numpy mcp

# Without uv
python3 -m venv .venv
source .venv/bin/activate
pip install fastembed numpy mcp
```

## How Scripts Use the Venv

Vectorstore scripts run from the vectorstore directory:

```bash
cd Nate's-kb/vectorstore
.venv/bin/python3 kb_query.py "search term"
.venv/bin/python3 kb_sync.py
```

The MCP server uses a wrapper script (`run-server.sh`) that handles paths with spaces correctly.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `.venv` doesn't exist | Run `./scripts/setup.sh` or manual setup above |
| `fastembed` not found | `cd Nate's-kb/vectorstore && source .venv/bin/activate && uv pip install fastembed numpy mcp` |
| MCP server fails to load | Ensure `run-server.sh` is executable (`chmod +x`) |
| Permission denied | Check `.venv/bin/python3` is executable |
| Different Python version | Delete `.venv`, re-run setup |

## Flash Drive / Portable Use

The `.venv` is NOT portable between machines (contains symlinks to local Python). Each machine must run `setup.sh` to create its own venv. The venv is in `.gitignore` and not committed.
