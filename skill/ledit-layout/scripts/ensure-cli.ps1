# Ensure cli-anything-ledit is installed and working
$ErrorActionPreference = "SilentlyContinue"
$check = cli-anything-ledit --json inspect 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing cli-anything-ledit..."
    pip install git+https://github.com/tjusaltedfish/cli-anything-Ledit.git 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install cli-anything-ledit"
        exit 1
    }
    Write-Host "Installed successfully."
} else {
    Write-Host "cli-anything-ledit is already installed."
}
$check = cli-anything-ledit --json inspect 2>&1 | ConvertFrom-Json
if (-not $check.ledit_exe_exists) {
    Write-Host "WARNING: L-Edit executable not found."
    Write-Host "Set LEDIT_EXE environment variable to your ledit64.exe path."
} else {
    Write-Host "L-Edit found at: $($check.ledit_exe)"
}
