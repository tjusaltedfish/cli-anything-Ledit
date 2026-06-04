# Acceptance Checklist: Codex/CLI-Anything to L-Edit Square Arrays

## Goal

Use Codex and a CLI-Anything harness to connect to Tanner L-Edit and draw user
requested square arrays.

## Verified by Automation

- CLI package exists as `cli-anything-ledit`.
- Entry point exposes:
  - `inspect`
  - `launch`
  - `square-array`
  - `draw-square-array`
  - `layer-probe`
  - `verify-script`
- `inspect` detects the real L-Edit executable:

```text
C:\Program Files\Tanner EDA\Tanner Tools v16.3\ledit64.exe
```

- `inspect` detects the local L-Edit documentation:

```text
C:\Program Files\Tanner EDA\Tanner Tools v16.3\Docs\ledit.pdf
```

- `draw-square-array` writes:
  - `.tco` Tanner Command File
  - `.svg` preview
  - `.run.txt` file containing the exact L-Edit `run` command
- `draw-square-array` verifies:
  - box count
  - expected box count
  - bounds
  - first box
  - last box
  - empty error list on success
- `layer-probe` writes a tiny `.tco` plus `.run.txt` to test whether the active
  L-Edit design accepts a named layer before drawing a full array on it.
- PowerShell helper `scripts\New-LEditSquareArray.ps1` also generates and
  verifies scripts.
- Safe keystroke sender `scripts\Send-LEditRunCommand.ps1` refuses to send if
  no visible L-Edit window is found.
- Test suite currently covers core writer, verifier, CLI entry points,
  installed command execution, PowerShell helper, and safe send failure.

## Current Machine State

Latest inspected GUI state:

```json
{
  "process_count": 1,
  "visible_window_count": 0,
  "can_send_run_command": false
}
```

The existing `ledit64` process is responding but has `MainWindowHandle=0`, so
Codex cannot safely send `run` into L-Edit automatically on this desktop state.

## Manual L-Edit Confirmation Still Needed

The remaining proof must happen inside the L-Edit GUI:

1. Open or bring L-Edit to a usable visible window.
2. Open L-Edit Command Window.
3. Run the command from a generated `.run.txt` file, for example:

```text
run "C:/Users/ASUS/Documents/L_edit/agent-harness/outputs/acceptance_6x9.tco"
```

4. Confirm the expected square array appears in the target cell/current layer.

When this visual confirmation succeeds, the objective can be treated as fully
closed.

## Recommended Smoke Command

```powershell
cd C:\Users\ASUS\Documents\L_edit\agent-harness

cli-anything-ledit --json draw-square-array `
  --rows 6 `
  --cols 9 `
  --size 1.2 `
  --pitch-x 2.4 `
  --pitch-y 2.8 `
  --origin-x 5 `
  --origin-y 7 `
  --layer CURRENT `
  --cell TOP `
  --out .\outputs\acceptance_6x9.tco `
  --launch
```

Expected automated success indicators:

```json
{
  "ok": true,
  "verified": true,
  "box_count": 54,
  "verify": {
    "ok": true,
    "expected_box_count": 54,
    "errors": []
  }
}
```

Then paste the contents of:

```text
outputs\acceptance_6x9.run.txt
```

into the L-Edit Command Window.
