# WSL VHDX Compact Script (Phase 2 of 2)
# Shuts down WSL and compacts the virtual disk to reclaim space on Windows.
# Must be run from an elevated (Admin) PowerShell prompt.
# Run wsl-maintenance.sh inside WSL first to clean and fstrim.
#
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\wsl-compact.ps1 [-DryRun]

param(
    [switch]$DryRun
)

$prefix = "[WSL-COMPACT]"

function Log($msg) { Write-Host "$prefix $msg" -ForegroundColor Magenta }
function Warn($msg) { Write-Host "[WARNING] $msg" -ForegroundColor Yellow }
function Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# --- Admin check ---
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Err "This script must be run as Administrator. Right-click PowerShell > Run as Administrator."
    exit 1
}

Log "=== WSL VHDX Compact Script ==="
if ($DryRun) { Log "Mode: DRY RUN" } else { Log "Mode: LIVE" }
Write-Host ""

# --- Find distros and VHDX paths ---
Log "=== Detecting WSL Distros ==="
$lxssKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
$distros = Get-ChildItem $lxssKey -ErrorAction SilentlyContinue | ForEach-Object {
    $p = Get-ItemProperty $_.PSPath
    $basePath = $p.BasePath
    # Check both possible VHDX locations
    $vhdx = @(
        (Join-Path $basePath 'ext4.vhdx'),
        (Join-Path $basePath 'LocalState\ext4.vhdx')
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if ($vhdx) {
        $size = (Get-Item $vhdx).Length
        [PSCustomObject]@{
            Name = $p.DistributionName
            VhdxPath = $vhdx
            SizeMB = [math]::Round($size / 1MB)
            SizeGB = [math]::Round($size / 1GB, 2)
        }
    }
}

if (-not $distros -or $distros.Count -eq 0) {
    Err "No WSL distros with VHDX files found."
    exit 1
}

foreach ($d in $distros) {
    Log "  $($d.Name): $($d.SizeGB) GB ($($d.VhdxPath))"
}
Write-Host ""

# --- Shutdown WSL ---
Log "=== Shutting Down WSL ==="
if ($DryRun) {
    Log "  [DRY RUN] Would run: wsl --shutdown"
} else {
    Log "  Running wsl --shutdown..."
    wsl.exe --shutdown
    Start-Sleep -Seconds 3
    Log "  WSL shut down"
}
Write-Host ""

# --- Compact each VHDX ---
foreach ($d in $distros) {
    Log "=== Compacting: $($d.Name) ($($d.SizeGB) GB) ==="

    if ($DryRun) {
        Log "  [DRY RUN] Would compact: $($d.VhdxPath)"
        continue
    }

    $before = $d.SizeMB

    # Build diskpart script
    $dpScript = @"
select vdisk file="$($d.VhdxPath)"
attach vdisk readonly
compact vdisk
detach vdisk
exit
"@
    $tempFile = [IO.Path]::GetTempFileName()
    Set-Content -LiteralPath $tempFile -Value $dpScript -Encoding ASCII

    Log "  Running diskpart (this may take a few minutes)..."
    $lastPct = -1
    diskpart /s $tempFile 2>&1 | ForEach-Object {
        if ($_ -match '(\d+)\s+percent') {
            $pct = [int]$Matches[1]
            if ($pct -ne $lastPct -and ($pct % 10 -eq 0 -or $pct -eq 100)) {
                Write-Host "  $pct% completed" -ForegroundColor Cyan
                $lastPct = $pct
            }
        }
    }

    Remove-Item $tempFile -ErrorAction SilentlyContinue

    # Report savings
    if (Test-Path $d.VhdxPath) {
        $afterMB = [math]::Round((Get-Item $d.VhdxPath).Length / 1MB)
        $saved = $before - $afterMB
        Log "  Before: $before MB  After: $afterMB MB  Reclaimed: $saved MB"
    }
    Write-Host ""
}

# --- Done ---
Log "=== Done ==="
Log "WSL will restart automatically on next use."
Log "Run 'wsl' to verify everything is working."
