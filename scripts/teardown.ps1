# The Nathaniel Protocol - System Teardown
# Removes system-level software installed by the setup scripts.
# Does NOT touch the protocol repo, knowledge base, or any user data.
#
# Run in PowerShell: powershell -ExecutionPolicy Bypass -File scripts/teardown.ps1

Write-Host ""
Write-Host "=== Nathaniel Protocol - System Teardown ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  This removes system software installed by the setup scripts." -ForegroundColor Yellow
Write-Host "  Your protocol folder, knowledge base, and all data are UNTOUCHED." -ForegroundColor Green
Write-Host ""

$confirm = Read-Host "  Continue? (y/n)"
if ($confirm -ne "y") {
    Write-Host "  Cancelled." -ForegroundColor Gray
    exit 0
}

Write-Host ""

# Remove global pip packages
Write-Host "  Removing global pip packages (mcp, uv)..." -ForegroundColor Yellow
foreach ($cmd in @("python", "python3")) {
    $p = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($p) {
        $ver = & $p.Source --version 2>&1
        if ($ver -match "Python \d+\.\d+") {
            & $p.Source -m pip uninstall -y mcp uv 2>$null
            Write-Host "  [OK] pip packages removed" -ForegroundColor Green
            break
        }
    }
}

# Uninstall Kiro CLI from WSL (if WSL exists)
try {
    $wslCheck = wsl -e echo "ready" 2>&1
    if ($wslCheck -match "ready") {
        Write-Host "  Removing Kiro CLI from WSL..." -ForegroundColor Yellow
        wsl -e bash -c "rm -f ~/.local/bin/kiro-cli 2>/dev/null; echo '  [OK] Kiro CLI removed from WSL'"

        Write-Host "  Removing WSL pip packages..." -ForegroundColor Yellow
        wsl -e bash -c "pip3 uninstall -y mcp uv 2>/dev/null; echo '  [OK] WSL pip packages removed'"
    }
} catch {}

# Offer to uninstall Python
Write-Host ""
$removePython = Read-Host "  Uninstall Python 3.12? (y/n)"
if ($removePython -eq "y") {
    Write-Host "  Removing Python..." -ForegroundColor Yellow
    winget uninstall Python.Python.3.12 --silent 2>$null
    Write-Host "  [OK] Python removed" -ForegroundColor Green
}

# Offer to uninstall Git
$removeGit = Read-Host "  Uninstall Git? (y/n)"
if ($removeGit -eq "y") {
    Write-Host "  Removing Git..." -ForegroundColor Yellow
    winget uninstall Git.Git --silent 2>$null
    Write-Host "  [OK] Git removed" -ForegroundColor Green
}

# Offer to uninstall WSL
$removeWSL = Read-Host "  Uninstall WSL and Ubuntu? (y/n)"
if ($removeWSL -eq "y") {
    Write-Host "  Removing Ubuntu distro..." -ForegroundColor Yellow
    wsl --unregister Ubuntu 2>$null
    Write-Host "  [OK] Ubuntu removed" -ForegroundColor Green
    Write-Host "  Removing WSL runtime..." -ForegroundColor Yellow
    winget uninstall Microsoft.WSL --silent 2>$null
    Write-Host "  [OK] WSL runtime removed" -ForegroundColor Green
}

# Offer to uninstall uv
$removeUv = Read-Host "  Uninstall uv? (y/n)"
if ($removeUv -eq "y") {
    Write-Host "  Removing uv..." -ForegroundColor Yellow
    winget uninstall astral-sh.uv --silent 2>$null
    Write-Host "  [OK] uv removed" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Teardown Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Your protocol folder is untouched." -ForegroundColor Green
Write-Host "  Plug into another machine and run setup again anytime." -ForegroundColor Green
Write-Host ""
