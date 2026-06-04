# Runbook: Codex/CLI-Anything to L-Edit Square Arrays

This project uses `cli-anything-ledit` to generate Tanner L-Edit command files
for square arrays.

## 1. Check L-Edit Detection

Run from a normal PowerShell terminal:

```powershell
cli-anything-ledit --json inspect
```

Expected on this machine:

```text
C:\Program Files\Tanner EDA\Tanner Tools v16.3\ledit64.exe
```

The Start Menu shortcut points to a stale `Program Files (x86)` target on this
machine, so use the path detected by `cli-anything-ledit inspect`.

## 2. Generate a Square Array

Recommended CLI command:

```powershell
cli-anything-ledit --json draw-square-array `
  --rows 12 `
  --cols 8 `
  --size 1.5 `
  --pitch 3.5 `
  --layer CURRENT `
  --cell TOP `
  --out C:\Users\ASUS\Documents\L_edit\agent-harness\outputs\square_array_12x8.tco
```

`draw-square-array` writes the `.tco`, writes the `.svg`, verifies the generated
geometry, and prints the exact L-Edit `run` command.

Recommended PowerShell helper:

```powershell
cd C:\Users\ASUS\Documents\L_edit\agent-harness

.\scripts\New-LEditSquareArray.ps1 `
  -Rows 12 `
  -Cols 8 `
  -Size 1.5 `
  -Pitch 3.5 `
  -Layer CURRENT `
  -Cell TOP `
  -Name square_array_12x8
```

The helper writes the `.tco` and `.svg`, prints the exact L-Edit `run` command,
and copies that command to the clipboard when Windows clipboard access is
available. It also runs `cli-anything-ledit verify-script` by default and
includes the verification receipt in its JSON output. Add `-SkipVerify` only
when debugging the generator itself. Add `-Launch` to also start L-Edit through
normal PowerShell.
Add `-SendRunCommand` only after L-Edit is visible and its Command Window is
focused; this is a best-effort keystroke sender and will safely report failure
if no visible L-Edit window is found.

Use `-PitchX`, `-PitchY`, `-OriginX`, and `-OriginY` when the array needs
different x/y spacing or a nonzero lower-left origin:

```powershell
.\scripts\New-LEditSquareArray.ps1 `
  -Rows 3 `
  -Cols 5 `
  -Size 1.25 `
  -PitchX 2.5 `
  -PitchY 3 `
  -OriginX 10 `
  -OriginY 20 `
  -Layer CURRENT `
  -Cell TOP `
  -Name offset_array_3x5
```

## 2a. Probe a Named Layer

If you want a named layer such as `Metal1`, probe it before generating a large
array:

```powershell
cli-anything-ledit --json layer-probe `
  --layer Metal1 `
  --cell TOP `
  --out C:\Users\ASUS\Documents\L_edit\agent-harness\outputs\probe_metal1.tco
```

Paste the generated `.run.txt` command into L-Edit's Command Window. If L-Edit
reports that the layer cannot be found, the current design/technology does not
accept that layer through ordinary command-window scripting. Use
`--layer CURRENT`, create/import the layer in L-Edit first, or build a UPI macro
bridge for `LLayer_New(...)`.

Example: 12 rows, 8 columns, square side length 1.5, pitch 3.5:

```powershell
cli-anything-ledit --json square-array `
  --rows 12 `
  --cols 8 `
  --size 1.5 `
  --pitch 3.5 `
  --layer CURRENT `
  --cell TOP `
  --out C:\Users\ASUS\Documents\L_edit\agent-harness\outputs\square_array_12x8.tco
```

The command writes both:

```text
C:\Users\ASUS\Documents\L_edit\agent-harness\outputs\square_array_12x8.tco
C:\Users\ASUS\Documents\L_edit\agent-harness\outputs\square_array_12x8.svg
```

The `.svg` is a quick preview. The `.tco` is the file L-Edit executes.

## 2b. Verify a Generated Script

Before running the script in L-Edit, validate the generated `.tco`:

```powershell
cli-anything-ledit --json verify-script `
  C:\Users\ASUS\Documents\L_edit\agent-harness\outputs\square_array_12x8.tco `
  --rows 12 `
  --cols 8 `
  --size 1.5 `
  --pitch 3.5 `
  --layer CURRENT `
  --cell TOP
```

The verifier checks the number of `box -!` commands, bounding box, first box,
and last box against the expected array parameters.

## 3. Launch L-Edit Without Codex Action Links

Use normal PowerShell:

```powershell
& 'C:\Program Files\Tanner EDA\Tanner Tools v16.3\ledit64.exe' -s -n
```

The `-s` option prevents file association changes; `-n` hides the splash screen.

Or use the helper with `-Launch`:

```powershell
.\scripts\New-LEditSquareArray.ps1 -Rows 12 -Cols 8 -Size 1.5 -Pitch 3.5 -Launch
```

If L-Edit is already visible and the Command Window has focus, you can ask the
helper to send the `run` command:

```powershell
.\scripts\New-LEditSquareArray.ps1 `
  -Rows 12 `
  -Cols 8 `
  -Size 1.5 `
  -Pitch 3.5 `
  -Name square_array_12x8 `
  -SendRunCommand
```

## 4. Draw the Array in L-Edit

After L-Edit is visible, open the L-Edit command window and run:

```text
run "C:/Users/ASUS/Documents/L_edit/agent-harness/outputs/square_array_12x8.tco"
```

For the post-fix 4x4 smoke-test file:

```text
run "C:/Users/ASUS/Documents/L_edit/agent-harness/outputs/square_array_4x4_after_fix.tco"
```

## 5. Notes About the OpenAI/Electron Error

If a dialog appears saying `Error launching app` and references
`C:\Program Files\WindowsApps\OpenAI...?...type=action`, that is Codex/OpenAI
desktop action-link handling, not L-Edit and not the generated `.tco` script.
Use the normal PowerShell commands above to bypass the action link.
