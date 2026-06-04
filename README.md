> **English** | [中文](README.zh-CN.md)

# cli-anything-Ledit

A **CLI-Anything** harness that automates [Tanner L-Edit](https://www.sw.siemens.com/ic-design/tanner-eda/) layout tasks from the command line. Generate Tanner Command Files (`.tco`), compile and execute UPI macros, control L-Edit windows via SendKeys, and verify layout geometry — all without touching the GUI.

> **CLI-Anything** is a methodology for wrapping any GUI-only EDA tool behind a scriptable CLI so that AI agents (Codex, Claude, GPT, etc.) and CI pipelines can drive it deterministically.

## Highlights

- **30+ CLI commands** covering layout drawing, cell/layer/file management, DRC, extraction, via fill, grid setup, technology queries, and more
- **Two automation layers**
  - *Command-window scripts* (`.tco`) — lightweight, no compiler needed
  - *UPI C++ macros* (`.cpp` → `.upi`) — full API access to L-Edit internals
- **JSON receipts** on every command for machine-readable integration
- **Built-in verification** of generated square-array geometry (box count, bounds, first/last box)
- **SVG preview** sidecar files for visual sanity checks before opening L-Edit
- **Configurable paths** — all Tanner toolchain paths can be overridden via environment variables

## Quick Start

### Prerequisites

- **Windows** with Tanner L-Edit v16.3 (or compatible) installed
- **Python ≥ 3.10**
- **PowerShell** (for SendKeys integration, optional)
- **MinGW g++** bundled with Tanner (for UPI macro compilation, optional)

### Install as Codex Skill (Recommended)

One command — installs the skill into Codex so you can use natural language:

```bash
codex skill install tjusaltedfish/cli-anything-Ledit/skill/ledit-layout
```

Or using the skill installer script:

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo tjusaltedfish/cli-anything-Ledit \
  --path skill/ledit-layout
```

After installation, just talk to Codex naturally:

> "Draw a 4x6 square array with 2um squares at 5um pitch"

> "Run DRC on the current cell"

> "Extract the netlist and save as SPICE"

The agent handles everything automatically — installing dependencies, generating scripts, compiling macros, and executing in L-Edit.

### Install via pip

```bash
pip install git+https://github.com/tjusaltedfish/cli-anything-Ledit.git
```

From source:

```bash
git clone https://github.com/tjusaltedfish/cli-anything-Ledit.git
cd cli-anything-Ledit
pip install -e .
```

One-click scripts:

```powershell
# Windows
.\install.ps1

# Linux/macOS
bash install.sh
```

### Verify Installation

```bash
cli-anything-ledit --json inspect
```

Expected output:

```json
{
  "ok": true,
  "ledit_exe": "C:\\Program Files\\Tanner EDA\\Tanner Tools v16.3\\ledit64.exe",
  "ledit_exe_exists": true,
  "process_count": 0
}
```

### Generate Your First Square Array

```bash
cli-anything-ledit --json draw-square-array \
  --rows 4 --cols 6 --size 2 --pitch 5 \
  --layer CURRENT --out outputs/my_array.tco
```

This writes three files:

| File | Purpose |
|------|---------|
| `outputs/my_array.tco` | Tanner Command File to paste into L-Edit |
| `outputs/my_array.svg` | SVG preview of the geometry |
| `outputs/my_array.run.txt` | Ready-to-paste `run` command |

Open L-Edit's Command Window and run:

```
run "C:/path/to/outputs/my_array.tco"
```

## Command Reference

### Layout Commands

| Command | Description |
|---------|-------------|
| `draw-square-array` | Generate, verify, and preview a square array in one step |
| `square-array` | Generate a square array `.tco` (no verify) |
| `box` | Draw a single rectangle |
| `path` | Draw a polyline path |
| `polygon` | Draw a polygon |
| `text` | Place a text label |
| `instance` | Place a cell instance |
| `array` | Create an instance array |
| `layout-script` | Execute a multi-operation JSON layout spec |
| `layer-probe` | Test whether the active design accepts a named layer |

### UPI Macro Commands

Every `macro-*` command generates C++ source. Add `--compile` to build a `.upi` DLL, and `--execute` to launch L-Edit with it.

| Command | Domain |
|---------|--------|
| `macro-square-array` | Draw square arrays via UPI |
| `macro-selection-action` | Copy, move, group, merge, flatten, flip, rotate |
| `macro-object-action` | Create circles, arcs, tori, pies |
| `macro-file-action` | New, open, save, saveas, close, home-view |
| `macro-layer-action` | Ensure, set-current, delete, rename layers |
| `macro-cell-action` | Ensure, open, copy, rename, delete, flatten cells |
| `macro-window-action` | Home view, save image, text windows |
| `macro-io-action` | Import/export GDS and CIF |
| `macro-grid-action` | Manufacturing, display, snap, major grid |
| `macro-drc-action` | Run DRC, manage markers, load results |
| `macro-extract-action` | Extraction, netlist, LVS |
| `macro-via-action` | Via definition, fill, find, count |
| `macro-object-property-action` | GDS datatype, net name, layer change |
| `macro-basepoint-action` | Basepoint mode and coordinates |
| `macro-layer-params-action` | GDS/CIF params, cap, rho, visibility |
| `macro-technology-action` | Technology name, units, lambda |
| `macro-cell-info-action` | List cells, get name, get visible |
| `macro-net-info-action` | List nets, count nets |
| `macro-smoke` | Minimal UPI smoke-test macro |

### Utility Commands

| Command | Description |
|---------|-------------|
| `inspect` | Detect L-Edit paths, running processes, and capabilities |
| `capabilities` | List all automation layers and their commands |
| `verify-script` | Validate a `.tco` file's command structure |
| `upi-preflight` | Check whether UPI execution is safe |
| `launch` | Start a new L-Edit instance |
| `run-script` | Send a `run` command to the focused L-Edit window |

### PowerShell Helpers

```powershell
# Generate, verify, and preview a square array
.\scripts\New-LEditSquareArray.ps1 -Rows 4 -Cols 6 -Size 2 -Pitch 5

# Add -Launch to start L-Edit automatically
.\scripts\New-LEditSquareArray.ps1 -Rows 4 -Cols 6 -Size 2 -Pitch 5 -Launch

# Send the run command to a visible L-Edit window
.\scripts\New-LEditSquareArray.ps1 -Rows 4 -Cols 6 -Size 2 -Pitch 5 -SendRunCommand
```

## Configuration

All Tanner toolchain paths can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LEDIT_EXE` | Auto-detected | Path to `ledit64.exe` |
| `LEDIT_DOC` | `C:\Program Files\Tanner EDA\Tanner Tools v16.3\Docs\ledit.pdf` | Path to L-Edit documentation |
| `LEDIT_GCC` | `C:\Program Files\Tanner EDA\Tanner Tools v16.3\mingw64\bin\g++.exe` | MinGW g++ for UPI compilation |
| `LEDIT_UPI_INCLUDE` | `C:\Program Files\Tanner EDA\Tanner Tools v16.3\upi\Include` | UPI header directory |
| `LEDIT_UPI_LINK_LIB` | `<UPI_INCLUDE>/libupilink-gcc4.6.3-x64.a` | UPI link library |
| `LEDIT_DEFAULT_OUTPUT_DIR` | `outputs` | Default output directory |

Example:

```bash
set LEDIT_EXE=D:\Tanner\v16.3\ledit64.exe
set LEDIT_GCC=D:\Tanner\v16.3\mingw64\bin\g++.exe
cli-anything-ledit --json inspect
```

## Architecture

```
cli_anything/ledit/
├── __init__.py           # Package metadata
├── __main__.py           # python -m entry point
├── config.py             # Centralized path configuration (env vars + defaults)
├── ledit_cli.py          # Click CLI with 30+ commands and REPL
├── core/
│   ├── macro_writer.py   # C++ UPI macro code generation
│   ├── script_writer.py  # .tco Tanner Command File generation
│   ├── session.py        # In-process command history
│   └── verify.py         # Geometry verification (box count, bounds)
├── utils/
│   └── ledit_backend.py  # L-Edit process management, compilation, SendKeys
└── tests/
    ├── test_core.py      # Unit tests for writers, verifiers, macros
    └── test_full_e2e.py  # End-to-end CLI tests
```

**Design principles:**

- Every command returns a JSON receipt with `"ok": true/false`
- Generated files are deterministic (no timestamps, no randomness)
- No GUI interaction unless explicitly requested (`--execute`, `run-script`)
- Safe by default: verify before run, preflight before execute

## Composable Layout Scripts

For multi-step layouts, pass a JSON spec to `layout-script`:

```bash
cli-anything-ledit --json layout-script layout.json --out outputs/design.tco
```

Example `layout.json`:

```json
{
  "title": "mixed layout",
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

## Testing

```bash
pip install -e ".[dev]"
pytest
```

The test suite covers:

- Square-array geometry generation and verification
- All UPI macro builders (cell, layer, file, DRC, extraction, via, etc.)
- CLI entry points and JSON receipt validation
- Script verification (command structure, box counts, bounds)
- Process inspection and preflight checks

## Examples

### Grayscale Lithography Test Mask

See [`examples/grayscale_test/`](examples/grayscale_test/) for a real-world use case: generating grayscale lithography test mask layouts with programmable pixel arrays.

### DRC + Extraction Workflow

```bash
# Run DRC on current cell
cli-anything-ledit --json macro-drc-action --action run --compile --execute

# Extract netlist
cli-anything-ledit --json macro-extract-action --action run \
  --def-file C:\path\extract.def --spice-out outputs\out.sp \
  --write-node-names --compile --execute
```

## License

[MIT](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Run tests (`pytest`)
4. Submit a pull request

## Acknowledgments

Built with [Click](https://click.palletsprojects.com/) for the CLI framework.



