#Requires -Version 5.1
<#
.SYNOPSIS
    One-click install for cli-anything-ledit.
.DESCRIPTION
    Installs cli-anything-ledit and verifies the installation.
    Run from the repo root: .\install.ps1
#>
$ErrorActionPreference = "Stop"

Write-Host "=== cli-anything-ledit Installer ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python is not installed or not on PATH." -ForegroundColor Red
    Write-Host "Install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

$pyVersion = python --version 2>&1
Write-Host "Found: $pyVersion" -ForegroundColor Green

# Install package
Write-Host ""
Write-Host "Installing cli-anything-ledit..." -ForegroundColor Yellow
pip install -e "." 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pip install failed." -ForegroundColor Red
    exit 1
}
Write-Host "Package installed." -ForegroundColor Green

# Verify
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
$result = cli-anything-ledit --json inspect 2>&1 | ConvertFrom-Json
if ($result.ok) {
    Write-Host "  L-Edit found: $($result.ledit_exe)" -ForegroundColor Green
    Write-Host "  Processes:    $($result.process_count)" -ForegroundColor Green
} else {
    Write-Host "  WARNING: L-Edit not detected. Set LEDIT_EXE env var." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Installation complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick start:" -ForegroundColor White
Write-Host '  cli-anything-ledit --json draw-square-array --rows 4 --cols 6 --size 2 --pitch 5 --layer CURRENT --out outputs\array.tco' -ForegroundColor Gray
Write-Host ""
Write-Host "Run tests:" -ForegroundColor White
Write-Host "  pip install -e `".[dev]`"" -ForegroundColor Gray
Write-Host "  pytest" -ForegroundColor Gray
