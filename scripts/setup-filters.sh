#!/bin/bash
# Setup git filters for Memory/Intelligence sanitization
# Run this after cloning the repo on a new system

# Detect python command (python3 on Linux/Mac, python on Windows)
if command -v python3 &> /dev/null; then
    PY="python3"
else
    PY="python"
fi

git config filter.sanitize-memory.clean "$PY scripts/git-filter-clean.py"
git config filter.sanitize-memory.smudge "$PY scripts/git-filter-smudge.py"
git config filter.sanitize-memory.required true

echo "Git sanitization filter configured (using $PY)."

# --- Dual-Instance Harmony ---
# Normalize line endings for cross-runtime compatibility (WSL + Windows)
git config core.autocrlf input
git config core.safecrlf false
echo "Line ending normalization configured (autocrlf=input, safecrlf=false)."

# Install pre-commit hook for KB integrity validation
HOOK_PATH=".git/hooks/pre-commit"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -d ".git/hooks" ]; then
    echo "No .git/hooks directory. Skipping pre-commit hook."
elif [ ! -f "$HOOK_PATH" ]; then
    cp "$SCRIPT_DIR/pre-commit-kb-validate.sh" "$HOOK_PATH"
    chmod +x "$HOOK_PATH"
    echo "Pre-commit hook installed."
elif ! grep -q "pre-commit-kb-validate" "$HOOK_PATH"; then
    echo "" >> "$HOOK_PATH"
    echo "# KB validation hook" >> "$HOOK_PATH"
    echo "bash scripts/pre-commit-kb-validate.sh || exit 1" >> "$HOOK_PATH"
    echo "Pre-commit hook appended to existing hook."
else
    echo "Pre-commit hook already installed."
fi
