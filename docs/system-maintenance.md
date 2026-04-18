# System Maintenance Guide

Last Updated: 2026-04-16

---

## Platform Compatibility

| Script | Linux | WSL | macOS | Notes |
|--------|-------|-----|-------|-------|
| `full-maintenance.sh` | ✓ | ✓ | ✓* | Unified wrapper. Chains Phases 1-3 with smart flag passthrough. Use this for monthly runs. |
| `python-maintenance.sh` | ✓ | ✓ | ✓ | Portable. Cleans pip/uv caches and `__pycache__` anywhere. |
| `kiro-maintenance.sh` | ✓ | ✓ | ✓ | Auto-detects OS. CLI cleanup works everywhere. IDE cleanup adapts paths per platform. |
| `wsl-maintenance.sh` | ✓ | ✓ | ✗ | Standard Linux maintenance (apt, journalctl, fstrim). Not macOS. |
| `wsl-compact.ps1` | ✗ | ✓* | ✗ | WSL2-only. Run from Windows PowerShell to shrink the VHDX virtual disk. |

*Phase 4 (VHDX compact) only applies when running Linux inside WSL2 on Windows. Native Linux and macOS users skip it.

**Quick environment check:**

```bash
echo "=== Environment Check ==="
uname -s | grep -qi linux && echo "✓ Linux/WSL" || echo "✓ $(uname -s)"
command -v python3 &>/dev/null && echo "✓ Python3" || echo "✗ Python3 not found"
command -v git &>/dev/null && echo "✓ Git" || echo "✗ Git not found"
grep -qi microsoft /proc/version 2>/dev/null && echo "✓ WSL detected (Phase 4 available)" || echo "– Not WSL (Phase 4 skipped)"
```

---

## Overview

Four maintenance scripts handle different layers of the development environment. They must run in a specific order because each phase frees disk space that the next phase can reclaim more effectively.

**Frequency**: Monthly, or when disk usage feels high. The Nathaniel Protocol's maintenance-protocol.md handles KB-internal maintenance (memory pruning, intelligence health). This doc covers everything else.

---

## Execution Order

```
Phase 1: Python cleanup        (any terminal, no prereqs)
Phase 2: Kiro cleanup          (close Kiro IDE + CLI first)
Phase 3: WSL cleanup + fstrim  (WSL bash, uses sudo)
Phase 4: WSL VHDX compact      (Admin PowerShell on Windows, shuts down WSL)
```

**Why this order matters:**
- Python cleanup frees `__pycache__`, pip/uv caches inside the WSL filesystem
- Kiro cleanup frees IDE caches on Windows and CLI caches in WSL
- WSL fstrim (Phase 3) marks ALL freed blocks from Phases 1-3 as reclaimable
- VHDX compact (Phase 4) can only reclaim blocks that fstrim has marked

Running Phase 4 without Phase 3 reclaims nothing. Running Phase 3 before Phases 1-2 misses the space they freed.

---

## Phase 1: Python Cleanup

**Script**: `scripts/python-maintenance.sh`
**Run from**: WSL bash
**Prereqs**: None (safe to run anytime)
**Estimated savings**: 500 MB - 1.5 GB

### What it does

1. Scans for `.venv/` and `venv/` directories, reports sizes and age
2. Deletes `__pycache__` directories outside virtual environments
3. Purges pip cache (`~/.cache/pip/`)
4. Cleans uv cache (`~/.cache/uv/`)
5. Audits stale venvs (30+ days untouched, report only unless `--delete-stale-venvs`)

### Commands

```bash
# Preview
./scripts/python-maintenance.sh --dry-run

# Run (cleans caches, leaves venvs alone)
./scripts/python-maintenance.sh

# Also delete stale venvs (interactive confirmation per venv)
./scripts/python-maintenance.sh --delete-stale-venvs

# Skip uv cache (if running Kiro maintenance next, it also cleans uv)
./scripts/python-maintenance.sh --skip-uv
```

### Flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Show what would be deleted, change nothing |
| `--skip-uv` | Skip uv cache cleanup (avoid double-clean with Kiro phase) |
| `--skip-pip` | Skip pip cache cleanup |
| `--delete-stale-venvs` | Prompt to delete venvs untouched 30+ days |

### Expected output

```
[PY-MAINT] === Python Maintenance Script ===
[PY-MAINT] === Phase 1: Current State ===
[PY-MAINT]   __pycache__ (outside venvs): 47 dirs, 150 MB
[PY-MAINT]   pip cache: 141M
[PY-MAINT]   uv cache: 750M
[PY-MAINT] === Phase 2: Clean __pycache__ ===
[PY-MAINT]   Deleted 47 __pycache__ dirs (150 MB)
[PY-MAINT] === Phase 3: Package Manager Caches ===
[PY-MAINT]   pip cache purged (141M)
[PY-MAINT]   uv cache cleaned (750M)
[PY-MAINT] === Done ===
```

### Error handling

| Error | Cause | Action |
|-------|-------|--------|
| `pip: not installed or no cache` | pip not on PATH | Safe to ignore, skip pip cleanup |
| `uv: not installed or no cache` | uv not installed | Safe to ignore, install with `pip install uv` |
| Permission denied on `__pycache__` | Root-owned files | Run with `sudo` or skip those dirs |

### After this phase

Proceed to Phase 2 (Kiro cleanup). If skipping Kiro cleanup, proceed to Phase 3 (WSL).

---

## Phase 2: Kiro Cleanup

**Script**: `scripts/kiro-maintenance.sh`
**Run from**: WSL bash (NOT from inside Kiro CLI)
**Prereqs**: Close Kiro IDE and exit Kiro CLI first
**Estimated savings**: 300 MB - 1.5 GB

### What it does

1. Verifies Kiro IDE and CLI are not running (refuses to proceed if they are)
2. Deletes stale CLI checkouts (`~/.local/share/kiro-cli/cli-checkouts/`)
3. VACUUMs the CLI SQLite database (compacts conversation history)
4. Trims CLI bash history if over 500 lines
5. Cleans IDE caches on Windows (Crashpad, logs, browser caches, GPU caches)
6. Cleans uv cache (if not already done in Phase 1)
7. Audits IDE extensions for duplicate versions (report only)

### Commands

```bash
# Preview
./scripts/kiro-maintenance.sh --dry-run

# Run
./scripts/kiro-maintenance.sh

# Skip slow SQLite VACUUM
./scripts/kiro-maintenance.sh --skip-vacuum

# Skip uv (already cleaned in Phase 1)
./scripts/kiro-maintenance.sh --skip-uv

# Also clear edit history and local storage
./scripts/kiro-maintenance.sh --aggressive
```

### Flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Show what would be deleted, change nothing |
| `--skip-vacuum` | Skip SQLite VACUUM (can be slow on large DBs) |
| `--skip-uv` | Skip uv cache cleanup (if already done in Phase 1) |
| `--aggressive` | Also clear User/History, Local Storage, CachedConfigurations |

### Expected output

```
[KIRO-MAINT] === Kiro Maintenance Script ===
[KIRO-MAINT] Pre-flight passed. Kiro IDE and CLI not running.
[KIRO-MAINT] === Current Sizes ===
[KIRO-MAINT]   CLI data:        540M
[KIRO-MAINT]   IDE AppData:     600M
[KIRO-MAINT] === Phase 1: CLI Cleanup ===
[KIRO-MAINT]   Cleaned CLI checkouts (311M)
[KIRO-MAINT]   VACUUM complete. Reclaimed ~50 MB
[KIRO-MAINT] === Phase 2: IDE Cleanup ===
[KIRO-MAINT]   Cleaned Crashpad reports (113M)
[KIRO-MAINT]   Deleted 6 old log dirs (74M)
...
[KIRO-MAINT] === Phase 4: Extension Audit ===
[KIRO-MAINT]   38 extensions installed (1.7G total)
[KIRO-MAINT]   No duplicate extension versions found
[KIRO-MAINT] === Done ===
```

### Error handling

| Error | Cause | Action |
|-------|-------|--------|
| `Kiro IDE is running. Close it first.` | IDE process detected | Close Kiro IDE, re-run |
| `Kiro CLI is running. Exit it first.` | CLI process detected | Exit CLI session, re-run from plain terminal |
| `sqlite3 not installed, skipping VACUUM` | sqlite3 not on PATH | Install: `sudo apt install sqlite3` |
| `IDE AppData not found` | Windows paths differ | Update `WIN_USER` in script config section |

### Configuration

The script has a config section at the top. Update these for your system:

```bash
WIN_USER="your-windows-username"    # Used to find Windows paths via /mnt/c/
```

### After this phase

Proceed to Phase 3 (WSL cleanup). All the space freed in Phases 1-2 is still "used" from WSL's perspective until fstrim runs.

---

## Phase 3: Linux Cleanup + fstrim

**Script**: `scripts/wsl-maintenance.sh`
**Run from**: Any Linux bash terminal (native or WSL)
**Prereqs**: sudo access. Best run after Phases 1-2 so fstrim captures all freed space.
**Estimated savings**: 100-500 MB (plus marks all Phase 1-2 savings for reclaim)
**macOS**: Not applicable (no apt, different disk model)

### What it does

1. Reports current disk usage
2. Cleans apt package cache (`apt clean` + `autoremove`)
3. Vacuums systemd journal logs (keeps 7 days)
4. Removes `/tmp` entries older than 7 days
5. Runs `fstrim /` to mark all free blocks as reclaimable

### Commands

```bash
# Preview
./scripts/wsl-maintenance.sh --dry-run

# Run
./scripts/wsl-maintenance.sh
```

### Expected output

```
[WSL-MAINT] === WSL Maintenance Script ===
[WSL-MAINT] === Current State ===
[WSL-MAINT]   Disk usage:
    Total: 251G  Used: 12G  Avail: 226G  Use%: 6%
[WSL-MAINT]   apt cache: 245M
[WSL-MAINT]   systemd journal: 48M
[WSL-MAINT] === Phase 2: apt Cleanup ===
[WSL-MAINT]   apt cache cleaned
[WSL-MAINT] === Phase 5: fstrim ===
[WSL-MAINT]   /: 238.5 GiB (xxx bytes) trimmed
[WSL-MAINT] === Done ===
[WSL-MAINT] Phase 1 complete. Free blocks marked via fstrim.
[WSL-MAINT] To reclaim disk space on Windows, run Phase 2:
[WSL-MAINT]   1. Open PowerShell as Administrator
[WSL-MAINT]   2. Run: powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\wsl-compact.ps1
```

### Error handling

| Error | Cause | Action |
|-------|-------|--------|
| `Permission denied` | Missing sudo | Run with sudo or enter password when prompted |
| `fstrim: / not mounted` | WSL1 (not WSL2) | fstrim only works on WSL2. Skip this phase. |

### After this phase

The script tells you exactly what to do next: run Phase 4 from an admin PowerShell.

---

## Phase 4: WSL VHDX Compact (WSL2 only)

**Script**: `scripts/wsl-compact.ps1`
**Run from**: Admin PowerShell on Windows (NOT from WSL)
**Prereqs**: Phase 3 must complete first (fstrim marks the blocks). This script shuts down WSL.
**Estimated savings**: Depends on how much was freed in Phases 1-3
**Native Linux / macOS**: Skip this phase entirely. fstrim in Phase 3 reclaims space directly.

### What it does

1. Verifies running as Administrator
2. Detects all WSL distros and their VHDX files
3. Shuts down WSL (`wsl --shutdown`)
4. Compacts each VHDX using diskpart (reclaims space on Windows disk)
5. Reports before/after sizes

### Commands

```powershell
# From Admin PowerShell:

# Preview
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\wsl-compact.ps1 -DryRun

# Run
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\wsl-compact.ps1
```

### Expected output

```
[WSL-COMPACT] === WSL VHDX Compact Script ===
[WSL-COMPACT] === Detecting WSL Distros ===
[WSL-COMPACT]   Ubuntu: 12.5 GB (C:\...\ext4.vhdx)
[WSL-COMPACT] === Shutting Down WSL ===
[WSL-COMPACT]   WSL shut down
[WSL-COMPACT] === Compacting: Ubuntu (12.5 GB) ===
  10% completed
  20% completed
  ...
  100% completed
[WSL-COMPACT]   Before: 12800 MB  After: 10200 MB  Reclaimed: 2600 MB
[WSL-COMPACT] === Done ===
```

### Error handling

| Error | Cause | Action |
|-------|-------|--------|
| `Must be run as Administrator` | Not elevated | Right-click PowerShell > Run as Administrator |
| `No WSL distros with VHDX files found` | WSL1 or no distros | Only works with WSL2 distros |
| diskpart hangs | Large VHDX, slow disk | Be patient. Can take 5-10 minutes for large disks. |

### After this phase

WSL restarts automatically on next use. Run `wsl` to verify everything works.

---

## Quick Reference

### Full maintenance run (recommended)

```bash
# Phases 1-3 in one command (from WSL, close Kiro first)
./scripts/full-maintenance.sh

# Phase 4: VHDX compact (from Admin PowerShell on Windows)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\wsl-compact.ps1
```

### Dry run everything first

```bash
./scripts/full-maintenance.sh --dry-run
# Then from Admin PowerShell:
# powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\wsl-compact.ps1 -DryRun
```

### Skip individual phases

```bash
./scripts/full-maintenance.sh --skip-phase 2          # Skip Kiro cleanup
./scripts/full-maintenance.sh --aggressive             # Deep Kiro clean (history, local storage)
./scripts/full-maintenance.sh --delete-stale-venvs     # Also prune old venvs
```

Not every phase is needed every time:

| Situation | Run |
|-----------|-----|
| Just need to clean Python caches | `./scripts/python-maintenance.sh` (standalone) |
| Kiro IDE feels slow | `./scripts/kiro-maintenance.sh` (standalone) |
| Windows disk full, WSL VHDX bloated | `./scripts/full-maintenance.sh --skip-phase 1 --skip-phase 2` + Phase 4 |
| Monthly full cleanup | `./scripts/full-maintenance.sh` + Phase 4 |

---

## Relationship to KB Maintenance

This doc covers **system-level** maintenance (caches, disk, IDE). For **Nathaniel KB maintenance** (memory pruning, intelligence health checks, pattern cleanup), use the `maintenance` command in chat, which triggers `maintenance-protocol.md`.

| Scope | Trigger | What it does |
|-------|---------|--------------|
| KB maintenance | Say "maintenance" or "health check" in chat | Prunes memory, validates intelligence stores, checks integrity |
| System maintenance | Run scripts per this doc | Cleans caches, reclaims disk, audits extensions |
