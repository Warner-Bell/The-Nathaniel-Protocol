# The Nathaniel Protocol - Windows Bootstrap
# Installs Git, Python, uv, WSL, and Ubuntu on Windows.
# Run this first, then run setup-wsl.ps1 to complete the environment.

# Self-elevate if not admin (needed for WSL install)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "  Requesting administrator access for WSL installation..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host ""
Write-Host "=== Nathaniel Protocol - Windows Bootstrap ===" -ForegroundColor Cyan
Write-Host ""

# Check and install Git
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "  [OK] Git installed: $(git --version)" -ForegroundColor Green
} else {
    Write-Host "  Installing Git..." -ForegroundColor Yellow
    winget install Git.Git --accept-package-agreements --accept-source-agreements
    Write-Host "  [OK] Git installed" -ForegroundColor Green
}

# Check and install Python
$pythonFound = $false
foreach ($cmd in @("python3", "python")) {
    $p = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($p) {
        $ver = & $p.Source --version 2>&1
        if ($ver -match "Python \d+\.\d+") {
            Write-Host "  [OK] Python installed: $ver" -ForegroundColor Green
            $pythonFound = $true
            break
        }
    }
}

if (-not $pythonFound) {
    Write-Host "  Installing Python 3.12..." -ForegroundColor Yellow
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    Write-Host "  [OK] Python installed" -ForegroundColor Green
}

# Check and install uv (needed for MCP servers in Kiro)
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "  [OK] uv installed: $(uv --version)" -ForegroundColor Green
} else {
    Write-Host "  Installing uv..." -ForegroundColor Yellow
    winget install astral-sh.uv --accept-package-agreements --accept-source-agreements
    Write-Host "  [OK] uv installed" -ForegroundColor Green
}

# Deploy Kiro config: copy .steering-files to .kiro
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$steering = Join-Path $repoRoot ".steering-files"
$kiro = Join-Path $repoRoot ".kiro"
if ((Test-Path $steering) -and -not (Test-Path $kiro)) {
    Copy-Item -Path $steering -Destination $kiro -Recurse
    Write-Host "  [OK] Kiro config deployed (.steering-files -> .kiro)" -ForegroundColor Green
} elseif (Test-Path $kiro) {
    Write-Host "  [OK] Kiro config already deployed" -ForegroundColor Green
} else {
    Write-Host "  [WARN] .steering-files not found - Kiro config not deployed" -ForegroundColor Yellow
}

Write-Host ""

# --- WSL + Ubuntu Installation ---

$wslReady = $false
try {
    $distroCheck = wsl -e echo "ready" 2>&1
    if ($distroCheck -match "ready") { $wslReady = $true }
} catch {}

if ($wslReady) {
    Write-Host "  [OK] WSL + distro ready" -ForegroundColor Green
} else {
    # Install WSL runtime via winget (--force handles broken/partial installs)
    $wslVersion = wsl --version 2>&1
    if ($LASTEXITCODE -ne 0 -or $wslVersion -match "cannot find") {
        Write-Host "  Installing WSL..." -ForegroundColor Yellow
        winget install Microsoft.WSL --force --accept-package-agreements --accept-source-agreements 2>$null
    } else {
        Write-Host "  [OK] WSL runtime present" -ForegroundColor Green
    }

    # Unregister broken Ubuntu if it exists but can't run
    # wsl --list outputs UTF-16LE; use chcp + string replace to strip null bytes
    $ubuntuCheck = (wsl --list --quiet 2>&1 | Out-String) -replace "`0", ""
    if ($ubuntuCheck -match "Ubuntu") {
        Write-Host "  Found existing Ubuntu registration. Cleaning up..." -ForegroundColor Yellow
        wsl --unregister Ubuntu 2>$null
    }

    # Install Ubuntu distro
    Write-Host "  Installing Ubuntu (this downloads ~500MB, may take a few minutes)..." -ForegroundColor Yellow
    Write-Host "  >> When Ubuntu finishes, create a username and password, then type 'exit'." -ForegroundColor Yellow
    Write-Host ""
    wsl --install -d Ubuntu
    $installExit = $LASTEXITCODE
    Write-Host ""

    # Check result
    if ($installExit -ne 0) {
        # Could be ERROR_ALREADY_EXISTS or other failure — verify directly
        Write-Host "  Install returned code $installExit. Verifying..." -ForegroundColor Yellow
    }

    # Verify it worked
    try {
        $retryCheck = wsl -e echo "ready" 2>&1
        if ($retryCheck -match "ready") {
            Write-Host "  [OK] WSL + Ubuntu ready" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "  WSL needs a restart to finish. Reboot, then run this script again." -ForegroundColor Yellow
            Write-Host ""
            exit 1
        }
    } catch {
        Write-Host ""
        Write-Host "  WSL needs a restart to finish. Reboot, then run this script again." -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}

Write-Host ""
Write-Host "=== Bootstrap Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Windows prerequisites and WSL installed." -ForegroundColor Green

if (-not $env:CALLED_FROM_SETUP_BAT) {
    Write-Host ""
    Write-Host "  Next steps:" -ForegroundColor Green
    Write-Host "    1. Open Kiro, start a chat, and say hello" -ForegroundColor White
    Write-Host "    2. From the Kiro terminal, run:" -ForegroundColor White
    Write-Host "       powershell -ExecutionPolicy Bypass -File scripts/setup-wsl.ps1" -ForegroundColor Yellow
}
Write-Host ""
