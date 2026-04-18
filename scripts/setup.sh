#!/bin/bash
# ============================================================
# The Nathaniel Protocol - Setup Script
# One-command deployment for Kiro IDE/CLI
# ============================================================
#
# Usage: chmod +x scripts/setup.sh && ./scripts/setup.sh
# Options:
#   --skip-vectorstore   Skip venv creation and vectorstore deps
#   --skip-kiro-config   Don't copy .steering-files to .kiro
#   --dry-run            Show what would happen without doing it
#
# ============================================================

set -euo pipefail

# --- Configuration ---
REQUIRED_PYTHON_VERSION="3.9"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- State tracking ---
ERRORS=0
WARNINGS=0
STEPS_PASSED=0
STEPS_TOTAL=8
DRY_RUN=false
SKIP_VECTORSTORE=false
SKIP_KIRO_CONFIG=false

# --- Parse args ---
for arg in "$@"; do
    case $arg in
        --skip-vectorstore) SKIP_VECTORSTORE=true ;;
        --skip-kiro-config) SKIP_KIRO_CONFIG=true ;;
        --dry-run) DRY_RUN=true ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

# --- Helpers ---
pass() { echo "  ✓ $1"; ((STEPS_PASSED++)) || true; }
fail() { echo "  ✗ $1"; ((ERRORS++)) || true; }
warn() { echo "  ⚠ $1"; ((WARNINGS++)) || true; }
info() { echo "  → $1"; }
step() { echo ""; echo "[$1/$STEPS_TOTAL] $2"; }

# --- Detect Python command ---
detect_python() {
    for cmd in python3 python python.exe; do
        if command -v "$cmd" &> /dev/null; then
            if $cmd -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
                echo "$cmd"
                return
            fi
        fi
    done
}

# --- Detect pip command ---
detect_pip() {
    if command -v pip3 &> /dev/null; then
        echo "pip3"
    elif command -v pip &> /dev/null; then
        echo "pip"
    fi
}

# ============================================================
echo "============================================"
echo "  The Nathaniel Protocol - Setup"
echo "============================================"
if $DRY_RUN; then echo "  (DRY RUN - no changes will be made)"; fi
echo ""
echo "  Repo: $REPO_ROOT"

cd "$REPO_ROOT"

# ============================================================
# Step 1: Git
# ============================================================
step 1 "Git"

if command -v git &> /dev/null; then
    pass "Git installed: $(git --version | head -1)"
else
    fail "Git not found"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        info "Install: sudo apt install -y git"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        info "Install: xcode-select --install"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        info "Install: winget install Git.Git (run in PowerShell, then restart terminal)"
    else
        info "Install: https://git-scm.com/downloads"
    fi
fi

# ============================================================
# Step 2: Python 3.9+
# ============================================================
step 2 "Python 3.9+"

PYTHON_CMD=$(detect_python)
if [ -n "$PYTHON_CMD" ]; then
    PY_VER=$($PYTHON_CMD --version 2>&1)
    if $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
        pass "Python: $PY_VER (command: $PYTHON_CMD)"
    else
        fail "Python too old: $PY_VER (need 3.9+)"
    fi
else
    fail "Python 3 not found"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        info "Install: sudo apt install -y python3 python3-pip python3-venv"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        info "Install: brew install python@3.12"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        info "Install: winget install Python.Python.3.12 (run in PowerShell, then restart terminal)"
    else
        info "Install: https://www.python.org/downloads/"
    fi
fi

# ============================================================
# Step 3: pip packages (mcp, uv)
# ============================================================
step 3 "Python packages"

PIP_CMD=$(detect_pip)
if [ -n "$PIP_CMD" ] && [ -n "$PYTHON_CMD" ]; then
    # mcp package
    if $PYTHON_CMD -c "import mcp" 2>/dev/null; then
        pass "mcp package installed"
    else
        info "Installing mcp package..."
        if ! $DRY_RUN; then
            if $PIP_CMD install mcp 2>/dev/null || $PIP_CMD install --break-system-packages mcp 2>/dev/null; then
                pass "mcp package installed"
            else
                warn "System mcp install failed (PEP 668). Vectorstore venv will provide it."
            fi
        else
            info "(dry run) Would install: $PIP_CMD install mcp"
        fi
    fi

    # uv (Kiro CLI uses it for MCP server environments)
    if command -v uv &> /dev/null; then
        pass "uv installed: $(uv --version 2>&1 | head -1)"
    else
        info "Installing uv..."
        if ! $DRY_RUN; then
            if $PIP_CMD install uv 2>/dev/null || $PIP_CMD install --break-system-packages uv 2>/dev/null; then
                pass "uv installed"
            else
                warn "Failed to install uv via pip. Try: curl -LsSf https://astral.sh/uv/install.sh | sh"
            fi
        else
            info "(dry run) Would install: $PIP_CMD install uv"
        fi
    fi
else
    fail "pip not found - cannot install Python packages"
    info "Install pip: https://pip.pypa.io/en/stable/installation/"
fi

# ============================================================
# Step 4: Kiro CLI
# ============================================================
step 4 "Kiro CLI"

if command -v kiro-cli &> /dev/null; then
    pass "Kiro CLI found: $(kiro-cli --version 2>&1 | head -1)"
else
    warn "Kiro CLI not found"
    info "Install: curl -fsSL https://cli.kiro.dev/install | bash"
    info "Or visit: https://kiro.dev/docs/cli/installation/"
    info "The protocol works without Kiro but is built for it. Also works with Claude Code, Cursor, and other agentic IDEs."
fi

# ============================================================
# Step 4b: sqlite3 CLI (used by kiro-maintenance.sh VACUUM)
# ============================================================
if command -v sqlite3 &> /dev/null; then
    pass "sqlite3 CLI installed: $(sqlite3 --version 2>&1 | head -1)"
else
    warn "sqlite3 CLI not found (kiro-maintenance.sh VACUUM will be skipped)"
    info "Install: sudo apt-get install sqlite3"
fi

# ============================================================
# Step 5: Deploy Kiro configuration
# ============================================================
step 5 "Kiro configuration (.steering-files → .kiro)"

if $SKIP_KIRO_CONFIG; then
    info "Skipped (--skip-kiro-config)"
else
    if [ -d ".steering-files" ]; then
        if ! $DRY_RUN; then
            mkdir -p .kiro
            # Copy each subdirectory, preserving existing content
            for dir in agents settings steering specs; do
                if [ -d ".steering-files/$dir" ]; then
                    mkdir -p ".kiro/$dir"
                    # Copy files, skip existing to preserve user customizations
                    find ".steering-files/$dir" -type f | while read src; do
                        dest=".kiro/${src#.steering-files/}"
                        if [ ! -f "$dest" ] || [ "$(basename "$src")" = "mcp.json" ]; then
                            mkdir -p "$(dirname "$dest")"
                            cp "$src" "$dest"
                        fi
                    done
                fi
            done
            # Copy root-level settings.json (trusted commands, workspace config)
            if [ -f ".steering-files/settings.json" ]; then
                cp ".steering-files/settings.json" ".kiro/settings.json"
            fi
            pass "Kiro config deployed to .kiro/"
        else
            info "(dry run) Would copy .steering-files/* to .kiro/"
        fi
    else
        fail ".steering-files/ directory not found"
    fi
fi

# Claude Code support: copy CLAUDE.md if not present
if [ ! -f "CLAUDE.md" ] && [ -f ".steering-files/steering/Nathaniel.md" ]; then
    if ! $DRY_RUN; then
        cp .steering-files/steering/Nathaniel.md CLAUDE.md
        pass "Claude Code config deployed (CLAUDE.md)"
    else
        info "(dry run) Would copy CLAUDE.md"
    fi
fi

# ============================================================
# Step 6: Vectorstore venv + dependencies
# ============================================================
step 6 "Vectorstore (hybrid search)"

if $SKIP_VECTORSTORE; then
    info "Skipped (--skip-vectorstore)"
else
    VECTORSTORE_DIR="$REPO_ROOT/Nate's-kb/vectorstore"
    VENV_PATH="$VECTORSTORE_DIR/.venv"
    WRAPPER_SCRIPT="$VECTORSTORE_DIR/run-server.sh"

    # Convert to Windows path if running in Git Bash (Windows Python doesn't understand /e/ paths)
    if command -v cygpath &>/dev/null; then
        VENV_PATH_NATIVE="$(cygpath -w "$VENV_PATH")"
        VECTORSTORE_DIR_NATIVE="$(cygpath -w "$VECTORSTORE_DIR")"
    else
        VENV_PATH_NATIVE="$VENV_PATH"
        VECTORSTORE_DIR_NATIVE="$VECTORSTORE_DIR"
    fi

    # Detect platform-specific venv paths
    if [ -d "$VENV_PATH/Scripts" ] 2>/dev/null || [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        VENV_PYTHON="$VENV_PATH/Scripts/python.exe"
        VENV_ACTIVATE="$VENV_PATH/Scripts/activate"
    else
        VENV_PYTHON="$VENV_PATH/bin/python3"
        VENV_ACTIVATE="$VENV_PATH/bin/activate"
    fi

    # Ensure wrapper script is executable (may fail on NTFS — non-blocking)
    if [ -f "$WRAPPER_SCRIPT" ]; then
        chmod +x "$WRAPPER_SCRIPT" 2>/dev/null && pass "run-server.sh executable" || true
    fi

    # Create venv if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        info "Creating virtual environment in vectorstore dir..."
        if ! $DRY_RUN; then
            # Try uv first, fall back to python -m venv --copies (avoids symlinks on NTFS/WSL)
            if command -v uv &> /dev/null && uv venv "$VENV_PATH_NATIVE" --python 3.10+ 2>/dev/null; then
                pass "venv created (uv)"
            elif command -v uv &> /dev/null && uv venv "$VENV_PATH_NATIVE" 2>/dev/null; then
                pass "venv created (uv)"
            elif $PYTHON_CMD -m venv "$VENV_PATH_NATIVE" --copies 2>/dev/null; then
                pass "venv created (python --copies)"
            elif $PYTHON_CMD -m venv "$VENV_PATH_NATIVE" 2>/dev/null; then
                pass "venv created (python)"
            else
                # NTFS symlink fallback: create in /tmp (native Linux fs), copy to NTFS
                if $PYTHON_CMD -m venv /tmp/_nate_venv --copies 2>/dev/null; then
                    rm -rf "$VENV_PATH_NATIVE"
                    cp -rL /tmp/_nate_venv "$VENV_PATH_NATIVE"
                    rm -rf /tmp/_nate_venv
                    pass "venv created (NTFS fallback)"
                else
                    fail "Failed to create venv"
                fi
            fi
        else
            info "(dry run) Would create venv at $VENV_PATH"
        fi
    else
        # Venv directory exists — verify it's usable on this platform
        VENV_USABLE=false
        if [ -f "$VENV_PATH/bin/python" ]; then
            VENV_USABLE=true
        elif [ -f "$VENV_PATH/Scripts/python.exe" ] && [ "$(uname -o 2>/dev/null)" != "GNU/Linux" ]; then
            VENV_USABLE=true
        fi

        if $VENV_USABLE; then
            # Check Python version matches system
            VENV_VER=$( (grep "^version_info" "$VENV_PATH/pyvenv.cfg" 2>/dev/null || true) | cut -d= -f2 | tr -d ' ' | cut -d. -f1-2)
            SYS_VER=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            if [ -n "$VENV_VER" ] && [ -n "$SYS_VER" ] && [ "$VENV_VER" != "$SYS_VER" ]; then
                warn "venv Python $VENV_VER != system Python $SYS_VER — rebuilding"
                rm -rf "$VENV_PATH"
                if command -v uv &> /dev/null && uv venv "$VENV_PATH_NATIVE" --python "$PYTHON_CMD" --relocatable 2>/dev/null; then
                    pass "venv recreated (uv, Python $SYS_VER)"
                elif $PYTHON_CMD -m venv "$VENV_PATH_NATIVE" --copies 2>/dev/null; then
                    pass "venv recreated (python $SYS_VER)"
                elif $PYTHON_CMD -m venv /tmp/_nate_venv --copies 2>/dev/null; then
                    cp -rL /tmp/_nate_venv "$VENV_PATH_NATIVE"
                    rm -rf /tmp/_nate_venv
                    pass "venv recreated (NTFS fallback, Python $SYS_VER)"
                else
                    fail "Failed to recreate venv"
                fi
            else
                pass "venv exists (Python version matches)"
            fi
        elif [ "$(uname -o 2>/dev/null)" = "GNU/Linux" ] && [ -f "$VENV_PATH/Scripts/python.exe" ]; then
            # Windows venv found in WSL — recreate as Linux venv
            info "Recreating venv (found Windows venv in Linux environment)..."
            rm -rf "$VENV_PATH"
            if $PYTHON_CMD -m venv "$VENV_PATH" --copies 2>/dev/null; then
                pass "venv recreated"
            elif $PYTHON_CMD -m venv /tmp/_nate_venv --copies 2>/dev/null; then
                cp -rL /tmp/_nate_venv "$VENV_PATH"
                rm -rf /tmp/_nate_venv
                pass "venv recreated (NTFS fallback)"
            else
                fail "Failed to recreate venv"
            fi
        else
            # Broken venv — recreate
            info "Recreating venv (existing venv unusable)..."
            rm -rf "$VENV_PATH"
            if $PYTHON_CMD -m venv "$VENV_PATH" --copies 2>/dev/null; then
                pass "venv recreated"
            elif $PYTHON_CMD -m venv /tmp/_nate_venv --copies 2>/dev/null; then
                cp -rL /tmp/_nate_venv "$VENV_PATH"
                rm -rf /tmp/_nate_venv
                pass "venv recreated (NTFS fallback)"
            else
                fail "Failed to recreate venv"
            fi
        fi
    fi

    # Install vectorstore dependencies
    if [ -d "$VENV_PATH" ]; then
        if ! $DRY_RUN; then
            info "Installing vectorstore dependencies..."
            # Use venv python directly — uv --python fails on paths with apostrophes (Nate's-kb)
            if [ -f "$VENV_PATH/bin/python3" ]; then
                VPYTHON="$VENV_PATH/bin/python3"
            elif [ -f "$VENV_PATH/bin/python" ]; then
                VPYTHON="$VENV_PATH/bin/python"
            elif [ -f "$VENV_PATH/Scripts/python.exe" ]; then
                VPYTHON="$VENV_PATH/Scripts/python.exe"
            else
                VPYTHON=""
            fi

            if [ -n "$VPYTHON" ]; then
                # pip on NTFS/WSL can return non-zero despite success; verify by import
                "$VPYTHON" -m pip install fastembed numpy mcp 2>&1 | tail -5
                if "$VPYTHON" -c "import numpy; import fastembed" 2>/dev/null; then
                    pass "fastembed + numpy + mcp installed"
                else
                    warn "pip install failed. Run manually: $VPYTHON -m pip install fastembed numpy mcp"
                fi
            else
                warn "venv python not found in $VENV_PATH"
            fi
            
            # Build index if intelligence stores have content
            PATTERNS_FILE="$REPO_ROOT/Nate's-kb/Intelligence/patterns.json"
            if [ -n "$VPYTHON" ] && "$VPYTHON" -c "
import json, sys
d=json.load(open(sys.argv[1], encoding='utf-8'))
sys.exit(0 if d.get('entries') else 1)
" "$PATTERNS_FILE" 2>/dev/null; then
                info "Building vectorstore index..."
                (cd "$VECTORSTORE_DIR" && "$VPYTHON" kb_vectorize.py) && pass "Vectorstore index built" || warn "Vectorstore build failed. Run manually: cd Nate's-kb/vectorstore && .venv/bin/python3 kb_vectorize.py"
            else
                if [ -z "$VPYTHON" ]; then
                    warn "venv python not found (vectorstore won't work until fixed)"
                else
                    info "Intelligence stores empty, skipping vectorstore build"
                fi
            fi
        else
            info "(dry run) Would install: fastembed numpy mcp"
            info "(dry run) Would build vectorstore index if stores have content"
        fi
    fi
fi

# ============================================================
# Step 7: Git repository + sanitization filters
# (Late in sequence so NTFS/WSL chmod failures don't block setup)
# ============================================================
step 7 "Git repository and sanitization filters"

if [ -n "$PYTHON_CMD" ] && command -v git &> /dev/null; then
    if [ ! -d .git ]; then
        if ! $DRY_RUN; then
            git init -q "$REPO_ROOT"
            pass "Git repository initialized"
        else
            info "(dry run) Would run: git init"
        fi
    else
        pass "Git repository exists"
    fi

    if ! $DRY_RUN; then
        GIT_DIR="$REPO_ROOT/.git"

        # chmod separately — always fails on NTFS, must not block git config
        chmod +x scripts/run-python.sh 2>/dev/null || true

        if (
            git config filter.sanitize-memory.clean "scripts/run-python.sh scripts/git-filter-clean.py"
            git config filter.sanitize-memory.smudge "scripts/run-python.sh scripts/git-filter-smudge.py"
            git config filter.sanitize-memory.required true
        ) 2>/dev/null; then
            pass "Git sanitization filters configured"
        else
            warn "Git filter config failed. Re-run setup or configure manually."
        fi

        if (
            git config core.autocrlf input
            git config core.safecrlf false
        ) 2>/dev/null; then
            pass "Line ending normalization configured"
        else
            warn "Line ending config failed. Non-blocking."
        fi

        # Pre-commit hook for KB integrity validation
        if [ -f scripts/pre-commit-kb-validate.sh ]; then
            cp scripts/pre-commit-kb-validate.sh "$GIT_DIR/hooks/pre-commit"
            chmod +x "$GIT_DIR/hooks/pre-commit" 2>/dev/null || true
            pass "Pre-commit hook installed"
        fi

        # Ensure git user identity is configured (WSL doesn't inherit Windows git config)
        if ! git --git-dir="$GIT_DIR" config user.email &>/dev/null; then
            git --git-dir="$GIT_DIR" config user.email "nate@pocket-hq.local" 2>/dev/null || true
            git --git-dir="$GIT_DIR" config user.name "Nathaniel" 2>/dev/null || true
        fi
    else
        info "(dry run) Would configure git clean/smudge filters"
    fi
else
    warn "Skipping git setup (missing git or python)"
fi

# ============================================================
# Step 8: Initial commit
# ============================================================
step 8 "Initial commit"

if command -v git &> /dev/null && [ -d .git ]; then
    GIT_CMD="git --git-dir=$REPO_ROOT/.git --work-tree=$REPO_ROOT"
    if [ -z "$($GIT_CMD log --oneline -1 2>/dev/null)" ]; then
        if ! $DRY_RUN; then
            # Set default identity if not configured (fresh Git install)
            if ! $GIT_CMD config user.email &>/dev/null; then
                $GIT_CMD config user.email "nate@nathaniel-protocol"
                $GIT_CMD config user.name "Nathaniel Protocol"
            fi
            $GIT_CMD add -A
            $GIT_CMD commit -q -m "Initial commit: Nathaniel Protocol setup"
            pass "Initial commit created"
        else
            info "(dry run) Would create initial commit"
        fi
    else
        pass "Commits already exist"
    fi
else
    warn "Skipping commit (no git repo)"
fi

# ============================================================
# Summary
# ============================================================
echo ""
echo "============================================"
echo "  Setup Complete"
echo "============================================"
echo "  Passed:   $STEPS_PASSED"
echo "  Warnings: $WARNINGS"
echo "  Errors:   $ERRORS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "  ⚠ Fix errors above and re-run."
    echo ""
    exit 1
fi

echo "  Next steps:"
echo "    1. Open a chat and say hello"
echo "    2. Say \"save\" before closing each session"
echo "    3. Optional: Say \"customize\" to personalize"
echo ""
