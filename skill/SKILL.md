# cli-anything-Ledit Skill

Drives Tanner L-Edit layout automation from the CLI. Use when the user asks to
draw layouts, generate square arrays, run DRC, extract netlists, manage
cells/layers, or any other L-Edit task that would normally require the GUI.

## Prerequisites

- Windows with Tanner L-Edit v16.3+ installed
- Python >= 3.10
- `pip install cli-anything-ledit` (or `pip install -e .` from this repo)

## Quick Check

```bash
cli-anything-ledit --json inspect
```

If `ledit_exe_exists` is `true`, the tool is ready.

## Common Workflows

### Draw a Square Array

```bash
cli-anything-ledit --json draw-square-array \
  --rows ROWS --cols COLS --size SIZE --pitch PITCH \
  --layer CURRENT --out outputs/array.tco
```

The JSON receipt includes `run_command` — paste it into L-Edit's Command Window.

### Multi-Step Layout

```bash
cli-anything-ledit --json layout-script layout.json --out outputs/design.tco
```

### Run DRC

```bash
cli-anything-ledit --json macro-drc-action --action run --compile --execute
```

### Extract Netlist

```bash
cli-anything-ledit --json macro-extract-action --action run \
  --def-file PATH --spice-out outputs/out.sp --write-node-names --compile --execute
```

### Inspect Environment

```bash
cli-anything-ledit --json inspect
cli-anything-ledit --json capabilities
cli-anything-ledit --json upi-preflight --macro outputs/file.upi
```

## Key Rules

- Always use `--json` flag for machine-readable output
- Commands only generate files by default; add `--compile --execute` to run in L-Edit
- Use `--layer CURRENT` to avoid layer-not-found errors
- Run `upi-preflight` before any `--execute` to check for running L-Edit processes
- The `run_command` in the receipt must be pasted into L-Edit's Command Window, not PowerShell
