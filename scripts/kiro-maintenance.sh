#!/bin/bash
# Kiro Maintenance Script
# Cleans Kiro IDE and Kiro CLI caches, logs, and temp files.
# Cross-platform: Linux, macOS, WSL. Auto-detects OS and adjusts paths.
# Kiro IDE and CLI must be closed before running.

set -euo pipefail

# --- Detect platform ---
PLATFORM="unknown"
IDE_APPDATA=""
IDE_HOME=""

if grep -qi microsoft /proc/version 2>/dev/null; then
    PLATFORM="wsl"
    WIN_USER="${WIN_USER:-$(cmd.exe /C "echo %USERNAME%" 2>/dev/null | tr -d '\r' || echo "UNKNOWN")}"
    IDE_APPDATA="/mnt/c/Users/${WIN_USER}/AppData/Roaming/Kiro"
    IDE_HOME="/mnt/c/Users/${WIN_USER}/.kiro"
elif [[ "$(uname -s)" == "Darwin" ]]; then
    PLATFORM="macos"
    IDE_APPDATA="$HOME/Library/Application Support/Kiro"
    IDE_HOME="$HOME/.kiro"
else
    PLATFORM="linux"
    IDE_APPDATA="${XDG_CONFIG_HOME:-$HOME/.config}/Kiro"
    IDE_HOME="$HOME/.kiro"
fi

CLI_DATA="$HOME/.local/share/kiro-cli"
CLI_HOME="$HOME/.kiro"

DRY_RUN=false
SKIP_VACUUM=false
SKIP_UV=false
AGGRESSIVE=false

# --- Parse flags ---
for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --skip-vacuum) SKIP_VACUUM=true ;;
        --skip-uv) SKIP_UV=true ;;
        --aggressive) AGGRESSIVE=true ;;
        --help) echo "Usage: $0 [--dry-run] [--skip-vacuum] [--skip-uv] [--aggressive]"; exit 0 ;;
    esac
done

# --- Helpers ---
log() { echo -e "\033[1;34m[KIRO-MAINT]\033[0m $1"; }
warn() { echo -e "\033[1;33m[WARNING]\033[0m $1"; }
err() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }
size_of() { du -sh "$1" 2>/dev/null | cut -f1 || echo "0"; }

clean_dir() {
    local dir="$1"
    local label="$2"
    if [ -d "$dir" ]; then
        local sz
        sz=$(size_of "$dir")
        if $DRY_RUN; then
            log "  [DRY RUN] Would clean $label ($sz): $dir"
        else
            rm -rf "${dir:?}"/*
            log "  Cleaned $label ($sz): $dir"
        fi
    fi
}

# --- Pre-flight ---
log "=== Kiro Maintenance Script ==="
log "Platform: $PLATFORM"
log "Mode: $( $DRY_RUN && echo 'DRY RUN' || echo 'LIVE' )"
echo ""

# Check Kiro IDE not running
case $PLATFORM in
    wsl)
        if powershell.exe -Command "Get-Process Kiro -ErrorAction SilentlyContinue" 2>/dev/null | grep -qi kiro; then
            err "Kiro IDE is running. Close it first."
            exit 1
        fi
        ;;
    macos)
        if pgrep -x "Kiro" > /dev/null 2>&1; then
            err "Kiro IDE is running. Close it first."
            exit 1
        fi
        ;;
    linux)
        if pgrep -f "[Kk]iro" > /dev/null 2>&1 && ! pgrep -f "kiro-cli" > /dev/null 2>&1; then
            err "Kiro IDE may be running. Close it first."
            exit 1
        fi
        ;;
esac

# Check Kiro CLI
if pgrep -f kiro-cli > /dev/null 2>&1; then
    err "Kiro CLI is running. Exit it first."
    exit 1
fi

log "Pre-flight passed. Kiro IDE and CLI not running."
echo ""

# --- Snapshot before ---
log "=== Current Sizes ==="
[ -d "$CLI_DATA" ] && log "  CLI data:        $(size_of "$CLI_DATA")"
[ -f "$CLI_DATA/data.sqlite3" ] && log "  CLI SQLite DB:   $(size_of "$CLI_DATA/data.sqlite3")"
[ -d "$CLI_DATA/cli-checkouts" ] && log "  CLI checkouts:   $(size_of "$CLI_DATA/cli-checkouts")"
[ -d "$IDE_APPDATA" ] && log "  IDE AppData:     $(size_of "$IDE_APPDATA")"
[ -d "$IDE_HOME/extensions" ] && log "  IDE extensions:  $(size_of "$IDE_HOME/extensions")"
command -v uv &>/dev/null && [ -d "$HOME/.cache/uv" ] && log "  UV cache:        $(size_of "$HOME/.cache/uv")"
echo ""

# --- Phase 1: CLI Cleanup (WSL) ---
log "=== Phase 1: CLI Cleanup ==="

# Stale checkouts
if [ -d "$CLI_DATA/cli-checkouts" ]; then
    count=$(find "$CLI_DATA/cli-checkouts" -mindepth 1 -maxdepth 1 -type d | wc -l)
    log "  Found $count checkout(s)"
    clean_dir "$CLI_DATA/cli-checkouts" "CLI checkouts"
fi

# SQLite VACUUM
if [ -f "$CLI_DATA/data.sqlite3" ] && ! $SKIP_VACUUM; then
    sz_before=$(stat -c%s "$CLI_DATA/data.sqlite3" 2>/dev/null || echo 0)
    if $DRY_RUN; then
        log "  [DRY RUN] Would VACUUM data.sqlite3 ($(size_of "$CLI_DATA/data.sqlite3"))"
    else
        log "  VACUUMing data.sqlite3 ($(size_of "$CLI_DATA/data.sqlite3"))..."
        sqlite3 "$CLI_DATA/data.sqlite3" "VACUUM;" 2>/dev/null || warn "  sqlite3 not installed, skipping VACUUM"
        sz_after=$(stat -c%s "$CLI_DATA/data.sqlite3" 2>/dev/null || echo 0)
        saved=$(( (sz_before - sz_after) / 1024 / 1024 ))
        log "  VACUUM complete. Reclaimed ~${saved} MB"
    fi
fi

# Bash history trim
if [ -f "$CLI_HOME/.cli_bash_history" ]; then
    lines=$(wc -l < "$CLI_HOME/.cli_bash_history")
    if [ "$lines" -gt 500 ]; then
        if $DRY_RUN; then
            log "  [DRY RUN] Would trim .cli_bash_history ($lines lines -> 500)"
        else
            tail -500 "$CLI_HOME/.cli_bash_history" > "$CLI_HOME/.cli_bash_history.tmp"
            mv "$CLI_HOME/.cli_bash_history.tmp" "$CLI_HOME/.cli_bash_history"
            log "  Trimmed .cli_bash_history ($lines -> 500 lines)"
        fi
    else
        log "  .cli_bash_history OK ($lines lines)"
    fi
fi
echo ""

# --- Phase 2: IDE Cleanup (Windows via /mnt/c/) ---
log "=== Phase 2: IDE Cleanup ==="

if [ ! -d "$IDE_APPDATA" ]; then
    warn "  IDE AppData not found at $IDE_APPDATA, skipping"
else
    # Crashpad
    clean_dir "$IDE_APPDATA/Crashpad/reports" "Crashpad reports"

    # Logs - keep only the most recent
    if [ -d "$IDE_APPDATA/logs" ]; then
        log_dirs=$(find "$IDE_APPDATA/logs" -mindepth 1 -maxdepth 1 -type d | sort)
        log_count=$(echo "$log_dirs" | wc -l)
        if [ "$log_count" -gt 1 ]; then
            newest=$(echo "$log_dirs" | tail -1)
            old_dirs=$(echo "$log_dirs" | head -n -1)
            old_sz=$(echo "$old_dirs" | xargs du -shc 2>/dev/null | tail -1 | cut -f1)
            if $DRY_RUN; then
                log "  [DRY RUN] Would delete $((log_count - 1)) old log dirs ($old_sz), keeping $(basename "$newest")"
            else
                echo "$old_dirs" | xargs rm -rf
                log "  Deleted $((log_count - 1)) old log dirs ($old_sz), kept $(basename "$newest")"
            fi
        else
            log "  Logs: only 1 dir, nothing to clean"
        fi
    fi

    # Safe-to-delete caches
    clean_dir "$IDE_APPDATA/Cache/Cache_Data" "Cache_Data"
    clean_dir "$IDE_APPDATA/Cache/No_Vary_Search" "No_Vary_Search"
    clean_dir "$IDE_APPDATA/CachedData" "CachedData"
    clean_dir "$IDE_APPDATA/CachedExtensionVSIXs" "CachedExtensionVSIXs"
    clean_dir "$IDE_APPDATA/Code Cache" "Code Cache"
    clean_dir "$IDE_APPDATA/GPUCache" "GPUCache"
    clean_dir "$IDE_APPDATA/DawnGraphiteCache" "DawnGraphiteCache"
    clean_dir "$IDE_APPDATA/DawnWebGPUCache" "DawnWebGPUCache"
    clean_dir "$IDE_APPDATA/blob_storage" "blob_storage"
    clean_dir "$IDE_APPDATA/WebStorage" "WebStorage"
    clean_dir "$IDE_APPDATA/Network" "Network"
    clean_dir "$IDE_APPDATA/Service Worker" "Service Worker"
    clean_dir "$IDE_APPDATA/Session Storage" "Session Storage"
    clean_dir "$IDE_APPDATA/Shared Dictionary" "Shared Dictionary"
    clean_dir "$IDE_APPDATA/Backups" "Backups"

    # Aggressive mode
    if $AGGRESSIVE; then
        warn "  Aggressive mode: clearing History and Local Storage"
        clean_dir "$IDE_APPDATA/User/History" "User/History (undo history)"
        clean_dir "$IDE_APPDATA/Local Storage" "Local Storage (preferences)"
        clean_dir "$IDE_APPDATA/CachedConfigurations" "CachedConfigurations"
        clean_dir "$IDE_APPDATA/CachedProfilesData" "CachedProfilesData"
    fi
fi
echo ""

# --- Phase 3: UV Cache ---
log "=== Phase 3: UV Cache ==="
if $SKIP_UV; then
    log "  Skipped (--skip-uv)"
elif command -v uv &>/dev/null; then
    if [ -d "$HOME/.cache/uv" ]; then
        sz=$(size_of "$HOME/.cache/uv")
        if $DRY_RUN; then
            log "  [DRY RUN] Would run uv cache clean ($sz)"
        else
            uv cache clean
            log "  UV cache cleaned ($sz freed)"
        fi
    else
        log "  No UV cache found"
    fi
else
    log "  uv not installed, skipping"
fi
echo ""

# --- Phase 4: Extension Audit (report only) ---
log "=== Phase 4: Extension Audit ==="
if [ -d "$IDE_HOME/extensions" ]; then
    ext_count=$(ls -1 "$IDE_HOME/extensions" 2>/dev/null | wc -l)
    ext_size=$(size_of "$IDE_HOME/extensions")
    log "  $ext_count extensions installed ($ext_size total)"

    # Find duplicate extension IDs (different versions)
    dupes=$(ls -1 "$IDE_HOME/extensions" 2>/dev/null \
        | sed 's/-[0-9][0-9]*\.[0-9].*$//' \
        | sort | uniq -d)
    if [ -n "$dupes" ]; then
        warn "  Duplicate extensions found (old versions may be removable):"
        while IFS= read -r ext_id; do
            echo "    $ext_id:"
            ls -1 "$IDE_HOME/extensions" | grep "^${ext_id}-[0-9]" | sed 's/^/      /'
        done <<< "$dupes"
    else
        log "  No duplicate extension versions found"
    fi
else
    log "  Extensions directory not found"
fi
echo ""

# --- Post-cleanup report ---
log "=== Post-Cleanup Sizes ==="
[ -d "$CLI_DATA" ] && log "  CLI data:        $(size_of "$CLI_DATA")"
[ -f "$CLI_DATA/data.sqlite3" ] && log "  CLI SQLite DB:   $(size_of "$CLI_DATA/data.sqlite3")"
[ -d "$IDE_APPDATA" ] && log "  IDE AppData:     $(size_of "$IDE_APPDATA")"
[ -d "$IDE_HOME/extensions" ] && log "  IDE extensions:  $(size_of "$IDE_HOME/extensions")"
command -v uv &>/dev/null && [ -d "$HOME/.cache/uv" ] && log "  UV cache:        $(size_of "$HOME/.cache/uv")"
echo ""
log "=== Done ==="
