param(
    [Parameter(Mandatory = $true)]
    [string]$RunCommand
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type -AssemblyName System.Windows.Forms

Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public static class LEditWindowApi {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@

function Find-LEditWindow {
    $processes = @(Get-Process -Name "ledit64" -ErrorAction SilentlyContinue)
    foreach ($candidate in $processes | Where-Object { $_.MainWindowHandle -ne 0 }) {
        return [ordered]@{
            process = $candidate
            handle = [IntPtr]$candidate.MainWindowHandle
            title = $candidate.MainWindowTitle
            source = "MainWindowHandle"
        }
    }

    $windows = New-Object System.Collections.Generic.List[object]
    [LEditWindowApi]::EnumWindows({
        param([IntPtr]$hWnd, [IntPtr]$lParam)
        if (-not [LEditWindowApi]::IsWindowVisible($hWnd)) {
            return $true
        }
        $processId = 0
        [void][LEditWindowApi]::GetWindowThreadProcessId($hWnd, [ref]$processId)
        if (-not ($processes | Where-Object { $_.Id -eq $processId })) {
            return $true
        }
        $builder = New-Object System.Text.StringBuilder 1024
        [void][LEditWindowApi]::GetWindowText($hWnd, $builder, $builder.Capacity)
        $title = $builder.ToString()
        if ($title -like "*L-Edit*") {
            $process = $processes | Where-Object { $_.Id -eq $processId } | Select-Object -First 1
            $windows.Add([ordered]@{
                process = $process
                handle = $hWnd
                title = $title
                source = "EnumWindows"
            })
        }
        return $true
    }, [IntPtr]::Zero) | Out-Null

    if ($windows.Count -gt 0) {
        return $windows[0]
    }

    return $null
}

$process = Get-Process -Name "ledit64" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } |
    Select-Object -First 1

$window = Find-LEditWindow

if (-not $window) {
    [ordered]@{
        ok = $false
        sent = $false
        error = "No visible L-Edit window with a nonzero MainWindowHandle was found."
        run_command = $RunCommand
    } | ConvertTo-Json -Depth 4
    exit 2
}

$process = $window.process
$handle = [IntPtr]$window.handle

[void][LEditWindowApi]::ShowWindow($handle, 9)
[void][LEditWindowApi]::SetForegroundWindow($handle)
Start-Sleep -Milliseconds 250

$activated = $false
try {
    $activated = [Microsoft.VisualBasic.Interaction]::AppActivate($process.Id)
} catch {
    $activated = $false
}
if (-not $activated) {
    [void][LEditWindowApi]::SetForegroundWindow($handle)
    Start-Sleep -Milliseconds 250
}

[System.Windows.Forms.SendKeys]::SendWait("``")
Start-Sleep -Milliseconds 150
[System.Windows.Forms.SendKeys]::SendWait($RunCommand)
[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")

[ordered]@{
    ok = $true
    sent = $true
    process_id = $process.Id
    window_handle = [int64]$handle
    window_title = $window.title
    window_source = $window.source
    app_activate = $activated
    run_command = $RunCommand
} | ConvertTo-Json -Depth 4
