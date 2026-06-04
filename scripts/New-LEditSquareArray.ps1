param(
    [Parameter(Mandatory = $true)]
    [int]$Rows,

    [Parameter(Mandatory = $true)]
    [int]$Cols,

    [Parameter(Mandatory = $true)]
    [double]$Size,

    [double]$Pitch = [double]::NaN,
    [double]$PitchX = [double]::NaN,
    [double]$PitchY = [double]::NaN,
    [double]$OriginX = 0.0,
    [double]$OriginY = 0.0,

    [string]$Layer = "CURRENT",
    [string]$Cell = "TOP",
    [string]$Name = "",
    [string]$OutDir = "",

    [switch]$Launch,
    [switch]$SendRunCommand,
    [switch]$SkipVerify,
    [switch]$NoClipboard
)

$ErrorActionPreference = "Stop"

$HarnessRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $OutDir = Join-Path $HarnessRoot "outputs"
}

if ([string]::IsNullOrWhiteSpace($Name)) {
    $Name = "square_array_${Rows}x${Cols}"
}

$safeName = $Name -replace '[\\/:*?"<>|]', "_"
$outPath = Join-Path $OutDir "$safeName.tco"

$cli = Get-Command "cli-anything-ledit" -ErrorAction SilentlyContinue
$squareArgs = @(
    "--json",
    "square-array",
    "--rows", "$Rows",
    "--cols", "$Cols",
    "--size", "$Size",
    "--origin-x", "$OriginX",
    "--origin-y", "$OriginY",
    "--layer", "$Layer",
    "--cell", "$Cell",
    "--out", "$outPath"
)

if (-not [double]::IsNaN($Pitch)) {
    $squareArgs += @("--pitch", "$Pitch")
} else {
    if (-not [double]::IsNaN($PitchX)) {
        $squareArgs += @("--pitch-x", "$PitchX")
    }
    if (-not [double]::IsNaN($PitchY)) {
        $squareArgs += @("--pitch-y", "$PitchY")
    }
}

if ($cli) {
    $rawReceipt = & $cli.Source @squareArgs
} else {
    Push-Location $HarnessRoot
    try {
        $rawReceipt = & python -m cli_anything.ledit @squareArgs
    } finally {
        Pop-Location
    }
}

if ($LASTEXITCODE -ne 0) {
    throw "cli-anything-ledit failed with exit code $LASTEXITCODE.`n$rawReceipt"
}

$receipt = ($rawReceipt | Out-String) | ConvertFrom-Json
if (-not $receipt.ok) {
    throw "cli-anything-ledit reported an error: $($receipt.error)"
}

$verifyReceipt = $null
if (-not $SkipVerify) {
    $verifyArgs = @(
        "--json",
        "verify-script",
        "$($receipt.script)",
        "--rows", "$Rows",
        "--cols", "$Cols",
        "--size", "$Size",
        "--origin-x", "$OriginX",
        "--origin-y", "$OriginY",
        "--layer", "$Layer",
        "--cell", "$Cell"
    )
    if (-not [double]::IsNaN($Pitch)) {
        $verifyArgs += @("--pitch", "$Pitch")
    } else {
        if (-not [double]::IsNaN($PitchX)) {
            $verifyArgs += @("--pitch-x", "$PitchX")
        }
        if (-not [double]::IsNaN($PitchY)) {
            $verifyArgs += @("--pitch-y", "$PitchY")
        }
    }
    if ($cli) {
        $verifyRaw = & $cli.Source @verifyArgs
    } else {
        Push-Location $HarnessRoot
        try {
            $verifyRaw = & python -m cli_anything.ledit @verifyArgs
        } finally {
            Pop-Location
        }
    }
    if ($LASTEXITCODE -ne 0) {
        throw "cli-anything-ledit verify-script failed with exit code $LASTEXITCODE.`n$verifyRaw"
    }
    $verifyReceipt = ($verifyRaw | Out-String) | ConvertFrom-Json
    if (-not $verifyReceipt.ok) {
        throw "Generated script verification failed: $($verifyReceipt.errors -join '; ')"
    }
}

$runCommand = $receipt.run_command
$clipboardCopied = $false
if (-not $NoClipboard) {
    try {
        Set-Clipboard -Value $runCommand
        $clipboardCopied = $true
    } catch {
        $clipboardCopied = $false
    }
}

$launchReceipt = $null
if ($Launch) {
    $inspectRaw = if ($cli) {
        & $cli.Source --json inspect
    } else {
        Push-Location $HarnessRoot
        try {
            & python -m cli_anything.ledit --json inspect
        } finally {
            Pop-Location
        }
    }
    $inspect = ($inspectRaw | Out-String) | ConvertFrom-Json
    if (-not $inspect.ledit_exe_exists) {
        throw "No L-Edit executable was detected."
    }
    Start-Process -FilePath $inspect.ledit_exe -ArgumentList "-s", "-n"
    $launchReceipt = @{
        ok = $true
        ledit_exe = $inspect.ledit_exe
        args = @("-s", "-n")
    }
}

$sendReceipt = $null
if ($SendRunCommand) {
    $sendScript = Join-Path $PSScriptRoot "Send-LEditRunCommand.ps1"
    $sendRaw = & powershell -ExecutionPolicy Bypass -File $sendScript -RunCommand $runCommand
    $sendReceipt = ($sendRaw | Out-String) | ConvertFrom-Json
}

$summary = [ordered]@{
    ok = $true
    script = $receipt.script
    preview = $receipt.preview
    run_file = $receipt.run_file
    powershell_open_file = $receipt.powershell_open_file
    box_count = $receipt.box_count
    bounds = $receipt.bounds
    verified = [bool]($verifyReceipt -and $verifyReceipt.ok)
    verify = $verifyReceipt
    run_command = $runCommand
    clipboard_copied = $clipboardCopied
    launched_ledit = [bool]$Launch
    launch = $launchReceipt
    sent_run_command = [bool]($sendReceipt -and $sendReceipt.sent)
    send = $sendReceipt
}

$summary | ConvertTo-Json -Depth 8

Write-Host ""
Write-Host "Paste this into the L-Edit Command Window:"
Write-Host $runCommand
if ($clipboardCopied) {
    Write-Host ""
    Write-Host "The run command was copied to the clipboard."
}
