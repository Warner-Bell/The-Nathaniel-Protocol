#!/bin/bash
# Unified System Maintenance Script
# Chains Phases 1-3 in the correct order with smart flag passthrough.
# Phase 4 (VHDX compact) must still be run manually from Admin PowerShell.
#
# Usage:
#   ./scripts/full-maintenance.sh                  # Run all 3 phases
#   ./scripts/full-maintenance.sh --dry-run        # Preview all 3 phases
#   ./scripts/full-maintenance.sh --skip-phase 2   # Skip Kiro cleanup
#   ./scripts/full-maintenance.sh --aggressive     # Pass --aggressive to Kiro phase
#   ./scripts/full-maintenance.sh --delete-stale-venvs  # Pass to Python phase

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Defaults ---
DRY_RUN=false
AGGRESSIVE=false
DELETE_STALE=false
SKIP_PHASE_1=false
SKIP_PHASE_2=false
SKIP_PHASE_3=false

# --- Parse flags ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        --aggressive) AGGRESSIVE=true; shift ;;
        --delete-stale-venvs) DELETE_STALE=true; shift ;;
        --skip-phase)
            case "${2:-}" in
                1) SKIP_PHASE_1=true ;;
                2) SKIP_PHASE_2=true ;;
                3) SKIP_PHASE_3=true ;;
                *) echo "[ERROR] --skip-phase requires 1, 2, or 3"; exit 1 ;;
            esac
            shift 2 ;;
        --help)
            echo "Usage: $0 [--dry-run] [--skip-phase N] [--aggressive] [--delete-stale-venvs]"
            echo ""
            echo "Runs Phases 1-3 of system maintenance in order:"
            echo "  Phase 1: Python cleanup (caches, __pycache__, venv audit)"
            echo "  Phase 2: Kiro cleanup (IDE + CLI caches, requires Kiro closed)"
            echo "  Phase 3: Linux/WSL cleanup + fstrim"
            echo ""
            echo "Flags:"
            echo "  --dry-run              Preview all phases without changing anything"
            echo "  --skip-phase N         Skip phase N (1, 2, or 3)"
            echo "  --aggressive           Pass --aggressive to Kiro phase (clears history/local storage)"
            echo "  --delete-stale-venvs   Pass --delete-stale-venvs to Python phase"
            echo ""
            echo "Phase 4 (VHDX compact) must be run separately from Admin PowerShell:"
            echo "  powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\\wsl-compact.ps1"
            exit 0 ;;
        *) echo "[ERROR] Unknown flag: $1. Use --help for usage."; exit 1 ;;
    esac
done

# --- Helpers ---
BOLD="\033[1m"
GREEN="\033[1;32m"
BLUE="\033[1;34m"
MAGENTA="\033[1;35m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

banner() { echo -e "\n${BOLD}════════════════════════════════════════════════════════════${RESET}"; echo -e "${BOLD}  $1${RESET}"; echo -e "${BOLD}════════════════════════════════════════════════════════════${RESET}\n"; }
log() { echo -e "${GREEN}[MAINT]${RESET} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${RESET} $1"; }
err() { echo -e "${RED}[ERROR]${RESET} $1"; }

# --- Header ---
banner "UNIFIED SYSTEM MAINTENANCE"
log "Mode: $( $DRY_RUN && echo 'DRY RUN' || echo 'LIVE' )"
log "Phases: $( $SKIP_PHASE_1 && echo '⊘1' || echo '✓1' ) $( $SKIP_PHASE_2 && echo '⊘2' || echo '✓2' ) $( $SKIP_PHASE_3 && echo '⊘3' || echo '✓3' )"
echo ""

# Track timing
TOTAL_START=$(date +%s)
PHASE_RESULTS=()

run_phase() {
    local phase_num="$1"
    local phase_name="$2"
    local script="$3"
    shift 3
    local args=("$@")

    banner "PHASE $phase_num: $phase_name"

    if [ ! -f "$script" ]; then
        err "Script not found: $script"
        PHASE_RESULTS+=("Phase $phase_num: SKIPPED (script missing)")
        return 1
    fi

    local phase_start
    phase_start=$(date +%s)

    if bash "$script" "${args[@]}"; then
        local elapsed=$(( $(date +%s) - phase_start ))
        PHASE_RESULTS+=("Phase $phase_num: DONE (${elapsed}s)")
        log "Phase $phase_num complete (${elapsed}s)"
    else
        local elapsed=$(( $(date +%s) - phase_start ))
        PHASE_RESULTS+=("Phase $phase_num: FAILED (${elapsed}s)")
        warn "Phase $phase_num had errors (${elapsed}s). Continuing."
    fi
}

# ═══════════════════════════════════════════
# PHASE 1: Python Cleanup
# ═══════════════════════════════════════════
if $SKIP_PHASE_1; then
    log "Phase 1 (Python): skipped"
    PHASE_RESULTS+=("Phase 1: SKIPPED")
else
    PY_ARGS=()
    $DRY_RUN && PY_ARGS+=(--dry-run)
    # Always skip-uv in Phase 1 since Kiro phase handles it (unless Phase 2 is skipped)
    $SKIP_PHASE_2 || PY_ARGS+=(--skip-uv)
    $DELETE_STALE && PY_ARGS+=(--delete-stale-venvs)

    run_phase 1 "PYTHON CLEANUP" "$SCRIPT_DIR/python-maintenance.sh" "${PY_ARGS[@]}"
fi

# ═══════════════════════════════════════════
# PHASE 2: Kiro Cleanup
# ═══════════════════════════════════════════
if $SKIP_PHASE_2; then
    log "Phase 2 (Kiro): skipped"
    PHASE_RESULTS+=("Phase 2: SKIPPED")
else
    KIRO_ARGS=()
    $DRY_RUN && KIRO_ARGS+=(--dry-run)
    $AGGRESSIVE && KIRO_ARGS+=(--aggressive)

    run_phase 2 "KIRO CLEANUP" "$SCRIPT_DIR/kiro-maintenance.sh" "${KIRO_ARGS[@]}"
fi

# ═══════════════════════════════════════════
# PHASE 3: Linux/WSL Cleanup + fstrim
# ═══════════════════════════════════════════
if $SKIP_PHASE_3; then
    log "Phase 3 (Linux/WSL): skipped"
    PHASE_RESULTS+=("Phase 3: SKIPPED")
else
    WSL_ARGS=()
    $DRY_RUN && WSL_ARGS+=(--dry-run)

    run_phase 3 "LINUX/WSL CLEANUP" "$SCRIPT_DIR/wsl-maintenance.sh" "${WSL_ARGS[@]}"
fi

# ═══════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════
TOTAL_ELAPSED=$(( $(date +%s) - TOTAL_START ))

banner "MAINTENANCE COMPLETE"
for result in "${PHASE_RESULTS[@]}"; do
    log "  $result"
done
log ""
log "Total time: ${TOTAL_ELAPSED}s"

# Phase 4 reminder (WSL only)
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo ""
    log "━━━ Phase 4: VHDX Compact (manual) ━━━"
    log "To reclaim disk space on Windows:"
    log "  1. Open PowerShell as Administrator"
    log "  2. Run:"
    log "     powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\\wsl-compact.ps1"
    echo ""
fi
