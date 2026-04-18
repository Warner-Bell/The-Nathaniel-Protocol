#!/bin/bash
# Python / .venv Maintenance Script
# Cleans __pycache__, pip/uv caches, and audits stale venvs
# Run from WSL bash.

set -euo pipefail

# --- Config ---
# Scans from current working directory by default. Override with PROJECT_ROOT env var.
PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"

DRY_RUN=false
SKIP_UV=false
SKIP_PIP=false
DELETE_STALE=false

for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --skip-uv) SKIP_UV=true ;;
        --skip-pip) SKIP_PIP=true ;;
        --delete-stale-venvs) DELETE_STALE=true ;;
        --help) echo "Usage: $0 [--dry-run] [--skip-uv] [--skip-pip] [--delete-stale-venvs]"; exit 0 ;;
    esac
done

# --- Helpers ---
log() { echo -e "\033[1;32m[PY-MAINT]\033[0m $1"; }
warn() { echo -e "\033[1;33m[WARNING]\033[0m $1"; }
size_of() { du -sh "$1" 2>/dev/null | cut -f1 || echo "0"; }

log "=== Python Maintenance Script ==="
log "Mode: $( $DRY_RUN && echo 'DRY RUN' || echo 'LIVE' )"
log "Project root: $PROJECT_ROOT"
echo ""

# --- Phase 1: Scan and Report ---
log "=== Phase 1: Current State ==="

# Venvs
log "  Virtual environments:"
find "$PROJECT_ROOT" -maxdepth 8 -type d \( -name ".venv" -o -name "venv" \) 2>/dev/null | while read -r d; do
    age_days=$(( ($(date +%s) - $(stat -c %Y "$d" 2>/dev/null || echo 0)) / 86400 ))
    log "    $(size_of "$d")  ${d#$PROJECT_ROOT/}  (${age_days}d old)"
done

# Pycache
total_pycache=$(find "$PROJECT_ROOT" -name "__pycache__" -not -path "*/.venv/*" -not -path "*/venv/*" -type d 2>/dev/null | wc -l)
pycache_size=$(find "$PROJECT_ROOT" -name "__pycache__" -not -path "*/.venv/*" -not -path "*/venv/*" -type d -exec du -s {} + 2>/dev/null | awk '{sum+=$1} END {printf "%.0f", sum/1024}')
log "  __pycache__ (outside venvs): $total_pycache dirs, ${pycache_size:-0} MB"

# Caches
[ -d "$HOME/.cache/pip" ] && log "  pip cache: $(size_of "$HOME/.cache/pip")"
[ -d "$HOME/.cache/uv" ] && log "  uv cache: $(size_of "$HOME/.cache/uv")"
echo ""

# --- Phase 2: Clean __pycache__ ---
log "=== Phase 2: Clean __pycache__ (outside venvs) ==="
if [ "$total_pycache" -gt 0 ]; then
    if $DRY_RUN; then
        log "  [DRY RUN] Would delete $total_pycache __pycache__ dirs (${pycache_size:-0} MB)"
    else
        find "$PROJECT_ROOT" -name "__pycache__" -not -path "*/.venv/*" -not -path "*/venv/*" -type d -exec rm -rf {} + 2>/dev/null || true
        log "  Deleted $total_pycache __pycache__ dirs (${pycache_size:-0} MB)"
    fi
else
    log "  No __pycache__ dirs to clean"
fi
echo ""

# --- Phase 3: Package Manager Caches ---
log "=== Phase 3: Package Manager Caches ==="

# pip
if $SKIP_PIP; then
    log "  pip: skipped (--skip-pip)"
elif command -v pip &>/dev/null && [ -d "$HOME/.cache/pip" ]; then
    sz=$(size_of "$HOME/.cache/pip")
    if $DRY_RUN; then
        log "  [DRY RUN] Would purge pip cache ($sz)"
    else
        pip cache purge 2>/dev/null
        log "  pip cache purged ($sz)"
    fi
else
    log "  pip: not installed or no cache"
fi

# uv
if $SKIP_UV; then
    log "  uv: skipped (--skip-uv)"
elif command -v uv &>/dev/null && [ -d "$HOME/.cache/uv" ]; then
    sz=$(size_of "$HOME/.cache/uv")
    if $DRY_RUN; then
        log "  [DRY RUN] Would clean uv cache ($sz)"
    else
        uv cache clean
        log "  uv cache cleaned ($sz)"
    fi
else
    log "  uv: not installed or no cache"
fi
echo ""

# --- Phase 4: Stale Venv Audit ---
log "=== Phase 4: Venv Audit ==="
find "$PROJECT_ROOT" -maxdepth 8 -type d \( -name ".venv" -o -name "venv" \) 2>/dev/null | while read -r d; do
    age_days=$(( ($(date +%s) - $(stat -c %Y "$d" 2>/dev/null || echo 0)) / 86400 ))
    rel="${d#$PROJECT_ROOT/}"
    sz=$(size_of "$d")

    # Flag naming convention
    if [[ "$(basename "$d")" == "venv" ]]; then
        warn "  $rel ($sz, ${age_days}d) - uses 'venv/' not '.venv/' convention"
    fi

    # Flag stale
    if [ "$age_days" -gt 30 ]; then
        warn "  $rel ($sz, ${age_days}d) - not modified in 30+ days"
        if $DELETE_STALE; then
            if $DRY_RUN; then
                log "    [DRY RUN] Would delete $rel ($sz)"
            else
                read -rp "    Delete $rel ($sz)? [y/N] " confirm
                if [[ "$confirm" =~ ^[Yy]$ ]]; then
                    rm -rf "$d"
                    log "    Deleted $rel"
                else
                    log "    Skipped"
                fi
            fi
        fi
    else
        log "  $rel ($sz, ${age_days}d) - active"
    fi
done
echo ""

# --- Post-cleanup Report ---
log "=== Post-Cleanup State ==="
new_pycache=$(find "$PROJECT_ROOT" -name "__pycache__" -not -path "*/.venv/*" -not -path "*/venv/*" -type d 2>/dev/null | wc -l)
log "  __pycache__ (outside venvs): $new_pycache dirs"
[ -d "$HOME/.cache/pip" ] && log "  pip cache: $(size_of "$HOME/.cache/pip")"
[ -d "$HOME/.cache/uv" ] && log "  uv cache: $(size_of "$HOME/.cache/uv")"
echo ""
log "=== Done ==="
