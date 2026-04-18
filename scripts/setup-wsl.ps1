# The Nathaniel Protocol - WSL Environment Setup
# Run this AFTER bootstrap-windows.ps1 has completed.
# Installs Python3, uv, Kiro CLI inside WSL and runs setup.sh.
# No admin privileges required.

Write-Host ""
Write-Host "=== Nathaniel Protocol - WSL Environment Setup ===" -ForegroundColor Cyan
Write-Host ""

# Verify WSL is ready
$wslReady = $false
try {
    $distroCheck = wsl -e echo "ready" 2>&1
    if ($distroCheck -match "ready") { $wslReady = $true }
} catch {}

if (-not $wslReady) {
    Write-Host "  [!] WSL is not ready. Run bootstrap-windows.ps1 first." -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host "  [OK] WSL + distro ready" -ForegroundColor Green
Write-Host ""
Write-Host "  Installing dependencies inside WSL..." -ForegroundColor Yellow

# Install Python3, pip, venv, unzip inside WSL
wsl -e bash -c "sudo apt update -qq && sudo apt install -y -qq python3 python3-pip python3-venv curl unzip sqlite3 > /dev/null 2>&1 && echo '  [OK] Python3 + pip + venv + sqlite3 installed' || echo '  [FAIL] Package install failed'"

# Install uv inside WSL (Kiro CLI uses it for MCP server environments)
wsl -e bash -lc "command -v uv" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] uv already installed" -ForegroundColor Green
} else {
    Write-Host "  Installing uv..." -ForegroundColor Yellow
    wsl -e bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
    wsl -e bash -lc "command -v uv" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] uv installed" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] uv install failed" -ForegroundColor Red
    }
}

# Ensure ~/.local/bin is on PATH (uv and kiro-cli install there)
wsl -e bash -c "grep -q 'local/bin' ~/.bashrc 2>/dev/null || echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"

# Ensure 'python' command exists (some MCP servers use 'python' not 'python3')
wsl -e bash -c "command -v python &>/dev/null || sudo ln -sf /usr/bin/python3 /usr/bin/python"

# Install Kiro CLI inside WSL
wsl -e bash -lc "command -v kiro-cli" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Kiro CLI already installed" -ForegroundColor Green
} else {
    Write-Host "  Installing Kiro CLI..." -ForegroundColor Yellow
    wsl -e bash -c "curl -fsSL https://cli.kiro.dev/install | bash"
    wsl -e bash -lc "command -v kiro-cli" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Kiro CLI installed" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Kiro CLI install failed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "  Running setup.sh (git filters, vectorstore, benchmarks)..." -ForegroundColor Yellow

# Get repo path in WSL format
$winPath = (Get-Location).Path
$wslPath = wsl -e bash -c "wslpath '$winPath'" 2>$null
if (-not $wslPath) { $wslPath = "/mnt/" + $winPath.Substring(0,1).ToLower() + $winPath.Substring(2).Replace("\","/") }

wsl -e bash -lc "cd '$wslPath' && bash scripts/setup.sh"

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "  Congratulations! The Nathaniel Protocol is fully installed." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Kiro IDE:  Start a chat and say hello" -ForegroundColor White
Write-Host "  Kiro CLI:  Type 'wsl' then 'kiro-cli chat' to start" -ForegroundColor White
Write-Host ""
Write-Host "  Run 'save' before closing each session." -ForegroundColor Yellow
Write-Host ""
