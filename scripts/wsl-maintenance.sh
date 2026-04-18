#!/bin/bash
# Linux Maintenance Script
# Cleans apt cache, journal logs, tmp, and runs fstrim to mark free blocks.
# Works on native Linux and WSL2. On WSL2, follow up with wsl-compact.ps1 to reclaim disk.
# On native Linux, fstrim reclaims space directly (no Phase 4 needed).

set -euo pipefail

DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --help) echo "Usage: $0 [--dry-run]"; exit 0 ;;
    esac
done

# --- Helpers ---
log() { echo -e "\033[1;35m[WSL-MAINT]\033[0m $1"; }
warn() { echo -e "\033[1;33m[WARNING]\033[0m $1"; }
size_of() { du -sh "$1" 2>/dev/null | cut -f1 || echo "0"; }

log "=== WSL Maintenance Script ==="
log "Mode: $( $DRY_RUN && echo 'DRY RUN' || echo 'LIVE' )"
echo ""

# Platform note
if grep -qi microsoft /proc/version 2>/dev/null; then
    log "Platform: WSL2 (Phase 4 VHDX compact available after this)"
else
    log "Platform: Native Linux (no VHDX compact needed)"
fi

# --- Phase 1: Current State ---
log "=== Current State ==="
log "  Disk usage:"
df -h / | tail -1 | awk '{printf "    Total: %s  Used: %s  Avail: %s  Use%%: %s\n", $2, $3, $4, $5}'

apt_cache_sz=$(size_of /var/cache/apt/archives)
log "  apt cache: $apt_cache_sz"

journal_sz=$(sudo journalctl --disk-usage 2>/dev/null | grep -oP '[\d.]+[KMGT]' || echo "unknown")
log "  systemd journal: $journal_sz"

tmp_count=$(find /tmp -mindepth 1 -maxdepth 1 -mtime +7 2>/dev/null | wc -l)
log "  /tmp entries older than 7d: $tmp_count"
echo ""

# --- Phase 2: apt cleanup ---
log "=== Phase 2: apt Cleanup ==="
if $DRY_RUN; then
    log "  [DRY RUN] Would run: apt clean + autoremove"
else
    sudo apt-get clean -y 2>/dev/null
    log "  apt cache cleaned"
    sudo apt-get autoremove -y 2>/dev/null | tail -1
    log "  Orphaned packages removed"
fi
echo ""

# --- Phase 3: Journal cleanup ---
log "=== Phase 3: Journal Logs ==="
if $DRY_RUN; then
    log "  [DRY RUN] Would vacuum journals older than 7 days"
else
    sudo journalctl --vacuum-time=7d 2>/dev/null | tail -1
    log "  Journals vacuumed (kept 7 days)"
fi
echo ""

# --- Phase 4: /tmp cleanup ---
log "=== Phase 4: /tmp Cleanup ==="
if [ "$tmp_count" -gt 0 ]; then
    if $DRY_RUN; then
        log "  [DRY RUN] Would remove $tmp_count entries older than 7 days"
    else
        sudo find /tmp -mindepth 1 -maxdepth 1 -mtime +7 -exec rm -rf {} + 2>/dev/null
        log "  Removed $tmp_count old /tmp entries"
    fi
else
    log "  /tmp clean, nothing to do"
fi
echo ""

# --- Phase 5: fstrim ---
log "=== Phase 5: fstrim (mark free blocks) ==="
if $DRY_RUN; then
    log "  [DRY RUN] Would run: fstrim -v /"
else
    trim_result=$(sudo fstrim -v / 2>&1) || true
    log "  $trim_result"
fi
echo ""

# --- Post-cleanup state ---
log "=== Post-Cleanup State ==="
df -h / | tail -1 | awk '{printf "    Total: %s  Used: %s  Avail: %s  Use%%: %s\n", $2, $3, $4, $5}'
echo ""

# --- Next step ---
log "=== Done ==="
log "Cleanup complete. Free blocks marked via fstrim."

if grep -qi microsoft /proc/version 2>/dev/null; then
    log ""
    log "WSL2 detected. To reclaim disk space on Windows, run Phase 4:"
    log "  1. Open PowerShell as Administrator"
    log "  2. Run: powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\\wsl-compact.ps1"
    log ""
    log "This will shut down WSL and compact the VHDX file."
else
    log "Native Linux: fstrim reclaimed space directly. No further steps needed."
fi
