#!/bin/bash
# Portable Python finder - works across Windows (Git Bash), WSL, macOS, Linux
# Usage: scripts/run-python.sh scripts/some-script.py [args...]

# Try standard commands first
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        # Verify it's real Python, not the Windows Store stub
        ver=$("$cmd" --version 2>&1)
        if echo "$ver" | grep -q "Python [0-9]"; then
            exec "$cmd" "$@"
        fi
    fi
done

# Fallback: scan common Windows Python install locations
for pydir in \
    "$LOCALAPPDATA/Programs/Python"/Python3*/python.exe \
    "$HOME/AppData/Local/Programs/Python"/Python3*/python.exe \
    "/c/Users"/*/AppData/Local/Programs/Python/Python3*/python.exe \
    "/c/Python3"*/python.exe; do
    if [ -x "$pydir" ] 2>/dev/null; then
        exec "$pydir" "$@"
    fi
done

echo "ERROR: No python found" >&2
exit 1
