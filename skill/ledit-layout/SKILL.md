---
name: ledit-layout
description: >
  Generate and control L-Edit layout files for IC design, grayscale lithography
  test masks, and layout automation. Use when the user asks to create layouts,
  draw shapes, generate test patterns, control L-Edit via command line, or
  automate layout tasks in Tanner L-Edit. Supports natural language requests
  like "draw a 4x6 square array", "run DRC", "extract netlist", etc.
---

# L-Edit Layout Automation

Automates Tanner L-Edit through a CLI harness. The user talks in natural
language; you translate their intent into CLI commands.

## First-Use Setup (auto-install)

Before using this skill, check whether the CLI is available:

```powershell
cli-anything-ledit --json inspect
```

If the command is **not found**, install it automatically:

```powershell
pip install git+https://github.com/tjusaltedfish/cli-anything-Ledit.git
```

If pip install fails (e.g. no network), fall back to editable install from the
skill's bundled source:

```powershell
$skillRoot = "<path-to-this-skill-directory>"
$repoRoot = Split-Path (Split-Path $skillRoot)
pip install -e $repoRoot
```

After install, verify:

```powershell
cli-anything-ledit --json inspect
```

If `ledit_exe_exists` is `false`, ask the user for their L-Edit path and set:

```powershell
$env:LEDIT_EXE = "C:\path\to\ledit64.exe"
```

## How to Use

**Always pass `--json`** to get machine-readable output you can parse.

The general pattern for every command:

```powershell
cli-anything-ledit --json <command> [options]
```

Parse the JSON receipt. If `"ok": true`, proceed. If `"ok": false`, report the
`"error"` field to the user.

## User Intent → Command Mapping

| User says | You run |
|-----------|---------|
| "draw a square array" / "画方阵" | `draw-square-array` |
| "draw a rectangle" / "画矩形" | `box` |
| "draw a path/wire" / "画路径" | `path` |
| "draw a polygon" / "画多边形" | `polygon` |
| "add text label" / "加文字" | `text` |
| "place an instance" / "放实例" | `instance` |
| "run DRC" / "跑DRC" | `macro-drc-action --action run --compile --execute` |
| "extract netlist" / "提取网表" | `macro-extract-action --action run ...` |
| "check L-Edit" / "检查环境" | `inspect` |
| "what can you do" / "你能做什么" | `capabilities` |
| "draw a complex layout" / "画复杂版图" | `layout-script` with JSON spec |
| "set grid" / "设置网格" | `macro-grid-action` |
| "import GDS" / "导入GDS" | `macro-io-action --action import-gds` |
| "create vias" / "打孔" | `macro-via-action` |
| "check layers" / "查看layer" | `macro-layer-action --action ensure` |

## Command Reference

### Layout (no compiler needed, generates .tco files)

```powershell
# Square array — the most common command
cli-anything-ledit --json draw-square-array `
  --rows 4 --cols 6 --size 2 --pitch 5 `
  --layer CURRENT --out outputs/array.tco

# Single box
cli-anything-ledit --json box `
  --x1 0 --y1 0 --x2 10 --y2 5 `
  --out outputs/box.tco

# Path / wire
cli-anything-ledit --json path `
  --point 0 0 --point 10 0 --point 10 5 `
  --width 0.5 --out outputs/path.tco

# Polygon
cli-anything-ledit --json polygon `
  --point 0 0 --point 10 0 --point 5 8 `
  --out outputs/poly.tco

# Text label
cli-anything-ledit --json text `
  --label "OUT" --x 5 --y 10 `
  --out outputs/text.tco

# Instance placement
cli-anything-ledit --json instance `
  --cell-name SUBCELL --x 20 --y 0 `
  --out outputs/inst.tco

# Complex multi-operation layout from JSON spec
cli-anything-ledit --json layout-script layout.json `
  --out outputs/design.tco
```

### UPI Macros (full L-Edit API access, needs Tanner MinGW)

Add `--compile` to build `.upi`, add `--execute` to launch L-Edit with it.

```powershell
# DRC
cli-anything-ledit --json macro-drc-action --action run --compile --execute
cli-anything-ledit --json macro-drc-action --action status --compile

# Extraction / LVS
cli-anything-ledit --json macro-extract-action --action run `
  --def-file C:\path\extract.def --spice-out outputs\out.sp `
  --write-node-names --compile --execute

# Via operations
cli-anything-ledit --json macro-via-action --action add `
  --lower-layer Metal1 --upper-layer Metal2 --via-cell VIA1 `
  --pitch-x 0.5 --pitch-y 0.5 --compile

# Grid setup
cli-anything-ledit --json macro-grid-action --action set-manufacturing-grid `
  --spacing 0.005 --compile --execute

# Layer management
cli-anything-ledit --json macro-layer-action --action ensure `
  --layer-name Metal1 --compile --execute

# Cell operations
cli-anything-ledit --json macro-cell-action --action ensure `
  --cell-name TOP --compile --execute

# File operations (new, open, save, saveas)
cli-anything-ledit --json macro-file-action --action saveas `
  --path C:\output\layout.tdb --compile --execute

# Selection operations (copy, move, group, flip, rotate...)
cli-anything-ledit --json macro-selection-action --action move `
  --dx 10 --dy 0 --compile --execute

# Import/Export
cli-anything-ledit --json macro-io-action --action import-gds `
  --file-path C:\input\layout.gds --compile --execute

# Technology info
cli-anything-ledit --json macro-technology-action --action get --compile

# Layer parameters (GDS number, CIF name, cap, rho)
cli-anything-ledit --json macro-layer-params-action --action get `
  --layer Metal1 --compile
```

### Environment

```powershell
# Check installation and running processes
cli-anything-ledit --json inspect

# List all capabilities
cli-anything-ledit --json capabilities

# Preflight before --execute
cli-anything-ledit --json upi-preflight --macro outputs/file.upi

# Launch L-Edit
cli-anything-ledit --json launch

# Send run command to focused L-Edit window
cli-anything-ledit --json run-script outputs/array.tco
```

### Composable Layout Scripts

For multi-step layouts, create a JSON file and pass it to `layout-script`:

```json
{
  "title": "my layout",
  "cell": "TOP",
  "operations": [
    {"op": "cell", "name": "TOP"},
    {"op": "layer", "name": "Metal1"},
    {"op": "box", "x1": 0, "y1": 0, "x2": 10, "y2": 5},
    {"op": "square-array", "rows": 3, "cols": 3, "size": 1, "pitch": 2, "x": 15, "y": 0},
    {"op": "path", "points": [[0, 8], [10, 8], [10, 12]], "width": 0.5},
    {"op": "polygon", "points": [[20, 0], [25, 0], [22.5, 4]]},
    {"op": "text", "label": "OUT", "x": 22, "y": 5},
    {"op": "save"}
  ]
}
```

```powershell
cli-anything-ledit --json layout-script layout.json --out outputs/design.tco
```

## Workflow for Drawing Layouts

1. **Understand** the user's request (size, shape, layer, coordinates)
2. **Generate** the script: use `draw-square-array`, `box`, `path`, `polygon`, or `layout-script`
3. **Verify** the receipt: check `"ok": true`, report `run_command` to user
4. **Execute** in L-Edit (only if user asks): use `--compile --execute` for UPI macros, or tell user to paste `run_command` into L-Edit Command Window
5. **Confirm** result: check receipt file or visual confirmation

## Important Rules

- Always use `--json` flag for machine-readable output
- Default to `--layer CURRENT` unless user specifies a layer name
- Commands only **generate files** by default; they do NOT touch L-Edit unless `--execute` is used
- Run `upi-preflight` before `--execute` to check for running L-Edit processes
- The `run_command` must be pasted into **L-Edit's Command Window**, not PowerShell
- Generated `.tco` files use forward slashes in paths (L-Edit requirement)
- For Chinese-speaking users, understand both Chinese and English coordinate/shape terminology

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `cli-anything-ledit` not found | Run `pip install git+https://github.com/tjusaltedfish/cli-anything-Ledit.git` |
| `ledit_exe_exists: false` | Set `$env:LEDIT_EXE` to the correct path |
| `--execute` does nothing | Close existing L-Edit, then retry; or use `--allow-existing-process` |
| Layer not found | Use `--layer CURRENT` or create the layer in L-Edit first |
| Compilation fails | Check that Tanner MinGW g++ is installed; set `LEDIT_GCC` |
| SendKeys fails | Ensure L-Edit window is visible and focused |
