# cli-anything-ledit

`cli-anything-ledit` generates Tanner L-Edit command scripts for layout tasks.
It is designed for Codex/CLI-Anything use: every command can emit JSON receipts
and the generated files are deterministic.

## Commands

```powershell
cli-anything-ledit --help
cli-anything-ledit --json square-array --rows 4 --cols 6 --size 2 --pitch 5 --layer CURRENT
cli-anything-ledit --json draw-square-array --rows 4 --cols 6 --size 2 --pitch 5 --layer CURRENT
cli-anything-ledit --json box --x1 0 --y1 0 --x2 4 --y2 2 --layer CURRENT --out outputs/box.tco
cli-anything-ledit --json path --point 0 0 --point 4 0 --point 4 4 --width 0.4 --out outputs/path.tco
cli-anything-ledit --json rotate --angle 90 --x 0 --y 0 --out outputs/rotate.tco
cli-anything-ledit --json layout-script outputs/layout.json --out outputs/layout.tco
cli-anything-ledit --json verify-layout-script outputs/layout.tco
cli-anything-ledit --json layer-probe --layer Metal1 --out outputs/probe_metal1.tco
cli-anything-ledit --json macro-selection-action --action move --dx 1 --dy 0 --compile
cli-anything-ledit --json macro-object-action --kind circle --x 0 --y 0 --radius 2 --compile
cli-anything-ledit --json macro-file-action --action home-view --compile
cli-anything-ledit --json upi-preflight --macro outputs/cell_ensure_nofocus.upi
cli-anything-ledit --json capabilities
cli-anything-ledit inspect
```

Use `draw-square-array` for the normal one-command path: it writes `.tco`,
writes `.svg`, verifies the generated boxes, and returns the L-Edit `run`
command. The generator also writes a `.run.txt` sidecar with the exact `run`
command so it can be copied without reopening the JSON receipt.

By default, commands only generate and verify files; they do not touch the
foreground L-Edit window. `run-script` and `--send-run-command` are the
interactive SendKeys route: they focus L-Edit and type the generated
`run "C:/.../script.tco"` command. Use that route only when foreground control
is acceptable. A successful JSON receipt includes both `"verified": true` and
`"sent_run_command": true`. If the send step fails, inspect `send.error`; the
fallback is to paste the `.run.txt` line into the L-Edit Command Window
manually.

For normal Windows use, the repository also includes a PowerShell helper that
generates the script and prints the L-Edit command to run:

```powershell
.\scripts\New-LEditSquareArray.ps1 -Rows 4 -Cols 6 -Size 2 -Pitch 5 -Layer CURRENT -Name square_array_4x6
```

Add `-Launch` to start L-Edit with the detected executable.

## Square Array

The `square-array` command writes one `.tco` file containing:

```text
cell TOP
// Using current active L-Edit layer; no layer command emitted.
box -! 0 0 2 2
...
```

To execute it in L-Edit:

```text
run "C:/absolute/path/to/square_array.tco"
```

The command also writes an SVG preview with the same stem.
It also writes a `.run.txt` sidecar containing the exact L-Edit `run` command.
Use `--layer CURRENT` when the target design does not already contain the named
layer. If you pass a real existing layer name, the generated script emits
`layer <name>` before drawing.

Use `layer-probe` to create a tiny script that tests whether the current L-Edit
design accepts a named layer before generating a large array on that layer.

## Direct Layout Commands

For common one-step work, call direct commands instead of writing a JSON spec:

```powershell
cli-anything-ledit --json box --x1 0 --y1 0 --x2 4 --y2 2 --out outputs/box.tco
cli-anything-ledit --json path --point 0 0 --point 4 0 --point 4 4 --width 0.4 --out outputs/path.tco
cli-anything-ledit --json polygon --point 0 0 --point 4 0 --point 2 3 --out outputs/poly.tco
cli-anything-ledit --json text --label NET_A --x 0 --y 6 --out outputs/text.tco
cli-anything-ledit --json instance --cell-name SUBCELL --x 20 --y 0 --out outputs/inst.tco
cli-anything-ledit --json array --cols 3 --rows 2 --pitch-x 5 --pitch-y 5 --out outputs/array.tco
cli-anything-ledit --json move --x 2 --y 0 --mode relative --out outputs/move.tco
cli-anything-ledit --json paste --x 24 --y 0 --out outputs/paste.tco
cli-anything-ledit --json rotate --angle 90 --x 0 --y 0 --out outputs/rotate.tco
cli-anything-ledit --json saveas --path C:\tmp\layout_copy.tdb --out outputs/saveas.tco
```

These commands still only generate and verify `.tco` files. They return a
`run_command` and write a `.run.txt` sidecar for L-Edit's Command Window.

## Composable Layout Scripts

Use `layout-script` when the task is more than a square array. It reads a JSON
file and writes one `.tco` script containing multiple L-Edit Command Window
operations. Supported operations in this first composable layer are:

```text
comment
cell
layer
box
square-array
path / wire
polygon
text
raw
width
goto
instance
array
copy
move
paste
rotate
saveas
```

Example `outputs/layout.json`:

```json
{
  "title": "mixed layout",
  "cell": "TOP",
  "layer": "CURRENT",
  "operations": [
    {"op": "box", "x1": 0, "y1": 0, "x2": 4, "y2": 2},
    {"op": "path", "points": [[0, 4], [4, 4], [4, 8]], "width": 0.4},
    {"op": "polygon", "points": [[6, 0], [10, 0], [8, 4]]},
    {"op": "text", "label": "NET_A", "x": 0, "y": 6},
    {"op": "square-array", "rows": 2, "cols": 3, "size": 0.8, "pitch": 1.4, "origin_x": 12, "origin_y": 0},
    {"op": "instance", "cell": "SUBCELL", "x": 20, "y": 0},
    {"op": "copy"},
    {"op": "paste", "x": 24, "y": 0},
    {"op": "rotate", "angle": 90, "x": 0, "y": 0}
  ]
}
```

Generate and verify it without touching the L-Edit foreground window:

```powershell
cli-anything-ledit --json layout-script outputs/layout.json --out outputs/layout.tco
cli-anything-ledit --json verify-layout-script outputs/layout.tco
```

This does not claim to cover every visible L-Edit UI control. It covers the
stable Command Window scripting layer for common layout creation and editing.
Dialog-heavy operations such as technology setup, DRC setup, extraction, and
batch macro execution should be added through UPI or dedicated backend commands
as separate harness layers.

Use `capabilities` to print the current layer-by-layer coverage from the CLI:

```powershell
cli-anything-ledit --json capabilities
```

## UPI Macros

`macro-smoke`, `macro-square-array`, `macro-selection-action`,
`macro-object-action`, `macro-file-action`, `macro-layer-action`,
`macro-cell-action`, `macro-window-action`, `macro-io-action`,
`macro-grid-action`, `macro-drc-action`, `macro-extract-action`, `macro-via-action`, `macro-basepoint-action`, and `macro-layer-params-action` can generate and compile UPI macros for L-Edit's
`-U <macro>` startup path. This route does not simulate keyboard input.
`macro-selection-action` covers selection-level editing
operations that are better represented by UPI than by Command Window text
commands:

```powershell
cli-anything-ledit --json macro-selection-action --action select-all --compile
cli-anything-ledit --json macro-selection-action --action move --dx 1 --dy 0 --compile
cli-anything-ledit --json macro-selection-action --action group --group-name CodexGroup --compile
cli-anything-ledit --json macro-selection-action --action merge --compile
cli-anything-ledit --json macro-selection-action --action flatten --compile
```

Supported selection actions are `select-all`, `deselect-all`, `cut`, `copy`,
`clear`, `paste`, `duplicate`, `group`, `ungroup`, `merge`, `flatten`,
`flip-horizontal`, `flip-vertical`, `snap-to-mfg-grid`, `move`, and `rotate`.

`macro-object-action` covers object creation where UPI has clearer documented
APIs than the Command Window syntax:

```powershell
cli-anything-ledit --json macro-object-action --kind circle --x 0 --y 0 --radius 2 --compile
cli-anything-ledit --json macro-object-action --kind port --label IN --x1 0 --y1 0 --x2 2 --y2 1 --layer CURRENT --compile
```

Supported object kinds are `circle` and `port`. These commands can generate and
compile macros without focusing L-Edit. Add `--execute` only when you want to
launch L-Edit with `-U <macro>`.

`macro-object-property-action` covers selected-object properties and conversions:

```powershell
cli-anything-ledit --json macro-object-property-action --action set-net-name --net-name NET_A --compile
cli-anything-ledit --json macro-object-property-action --action clear-net-name --compile
cli-anything-ledit --json macro-object-property-action --action set-gds-datatype --gds-datatype 12 --compile
cli-anything-ledit --json macro-object-property-action --action change-layer --layer Mask2 --compile
cli-anything-ledit --json macro-object-property-action --action copy-to-layer --layer CopyLayer --compile
cli-anything-ledit --json macro-object-property-action --action snap-to-grid --grid 0.25 --compile
cli-anything-ledit --json macro-object-property-action --action convert-to-polygon --compile
```

Supported selected-object property actions are `set-gds-datatype`,
`set-net-name`, `clear-net-name`, `change-layer`, `snap-to-grid`,
`snap-to-mfg-grid`, `copy-to-layer`, `delete`, and `convert-to-polygon`.
These commands operate on the current L-Edit selection when executed.

`macro-file-action` covers basic file, cell, and view operations through UPI:

```powershell
cli-anything-ledit --json macro-file-action --action new --path outputs/new_layout.tdb --cell TOP --compile
cli-anything-ledit --json macro-file-action --action open --path C:\path\layout.tdb --cell TOP --compile
cli-anything-ledit --json macro-file-action --action save --compile
cli-anything-ledit --json macro-file-action --action saveas --path C:\tmp\layout_copy.tdb --compile
cli-anything-ledit --json macro-file-action --action open-cell --cell SUBCELL --compile
cli-anything-ledit --json macro-file-action --action home-view --compile
cli-anything-ledit --json macro-file-action --action move-origin --x 1.5 --y -2 --compile
cli-anything-ledit --json macro-file-action --action clear-cell --compile
```

Supported file actions are `new`, `open`, `save`, `saveas`, `close`,
`open-cell`, `home-view`, `move-origin`, and `clear-cell`.

`macro-layer-action` covers basic layer setup and selection layer changes:

```powershell
cli-anything-ledit --json macro-layer-action --action ensure --layer Mask1 --compile
cli-anything-ledit --json macro-layer-action --action set-current --layer Mask1 --compile
cli-anything-ledit --json macro-layer-action --action rename --layer Mask1 --new-name MaskRenamed --compile
cli-anything-ledit --json macro-layer-action --action change-selection-layer --source-layer Mask1 --target-layer Mask2 --compile
cli-anything-ledit --json macro-layer-action --action delete --layer Mask1 --compile
```

Supported layer actions are `ensure`, `set-current`, `delete`, `rename`, and
`change-selection-layer`. `ensure` creates the layer if it does not exist, then
sets it current. `change-selection-layer` creates the target layer when needed.

`macro-cell-action` covers basic cell setup and cell-level operations:

```powershell
cli-anything-ledit --json macro-cell-action --action ensure --cell TOP --compile
cli-anything-ledit --json macro-cell-action --action open --cell TOP --compile
cli-anything-ledit --json macro-cell-action --action copy --source-cell TOP --target-cell TOP_COPY --compile
cli-anything-ledit --json macro-cell-action --action rename --cell TOP_COPY --new-name MAIN_COPY --compile
cli-anything-ledit --json macro-cell-action --action clear --cell TOP_COPY --compile
cli-anything-ledit --json macro-cell-action --action flatten --cell TOP --compile
cli-anything-ledit --json macro-cell-action --action delete --cell TOP_COPY --compile
```

Supported cell actions are `ensure`, `open`, `copy`, `rename`, `delete`,
`clear`, and `flatten`.

`macro-window-action` covers basic window and view operations through UPI:

```powershell
cli-anything-ledit --json macro-window-action --action home-visible-cell --compile
cli-anything-ledit --json macro-window-action --action make-first-layout-visible --compile
cli-anything-ledit --json macro-window-action --action save-visible-image --path outputs/visible_window.png --compile
cli-anything-ledit --json macro-window-action --action new-text-window --text "hello from Codex" --compile
cli-anything-ledit --json macro-window-action --action load-text-window --path C:\tmp\notes.txt --compile
cli-anything-ledit --json macro-window-action --action close-visible-window --compile
```

Supported window actions are `home-visible-cell`,
`make-first-layout-visible`, `save-visible-image`, `new-text-window`,
`load-text-window`, and `close-visible-window`. `close-visible-window` refuses
to close the last remaining window.

`macro-io-action` covers GDS/CIF import and GDS export through UPI:

```powershell
cli-anything-ledit --json macro-io-action --action import-gds --path C:\tmp\input.gds --log-path outputs/import_gds.log --compile
cli-anything-ledit --json macro-io-action --action import-cif --path C:\tmp\input.cif --polygon-as-rect --compile
cli-anything-ledit --json macro-io-action --action export-gds --path outputs/export.gds --cell TOP --compile
```

Supported IO actions are `import-gds`, `import-cif`, and `export-gds`.
Import actions support `--overwrite none|top|all`; GDS import also supports
`--use-gds-datatype` / `--ignore-gds-datatype`. GDS export supports
`--cell`, `--include-hierarchy` / `--flat`, and
`--hidden-objects` / `--visible-only`.

`macro-grid-action` covers grid and manufacturing-grid setup:

```powershell
cli-anything-ledit --json macro-grid-action --action set-manufacturing-grid --value 0.1 --compile
cli-anything-ledit --json macro-grid-action --action set-display-grid --value 1 --compile
cli-anything-ledit --json macro-grid-action --action set-major-grid --value 10 --compile
cli-anything-ledit --json macro-grid-action --action set-snap-grid --value 1 --x 0.25 --y 0.5 --compile
```

Supported grid actions are `set-manufacturing-grid`, `set-display-grid`,
`set-snap-grid`, and `set-major-grid`. Values are in the current L-Edit display
units and are converted to internal units through `LFile_DispUtoIntU`.

`macro-drc-action` covers DRC, DRC result, and marker-related operations:

```powershell
cli-anything-ledit --json macro-drc-action --action set-rule-set --rule-set "DRC Standard Rule Set" --compile
cli-anything-ledit --json macro-drc-action --action set-flags --flag-acute --flag-all-angle --flag-off-grid --compile
cli-anything-ledit --json macro-drc-action --action run --x1 0 --y1 0 --x2 10 --y2 20 --compile
cli-anything-ledit --json macro-drc-action --action run-command-file --path C:\tmp\rules.cal --compile
cli-anything-ledit --json macro-drc-action --action status --compile
cli-anything-ledit --json macro-drc-action --action open-summary --compile
cli-anything-ledit --json macro-drc-action --action clear-markers --compile
```

Supported DRC actions are `run`, `run-command-file`, `set-rule-set`,
`set-tolerance`, `set-flags`, `open-summary`, `open-statistics`,
`load-results`, `clear-markers`, `show-global-markers`,
`hide-global-markers`, and `status`. DRC area options are `--x1 --y1 --x2 --y2`;
omit them to run on the whole visible cell.

`macro-extract-action` covers extraction, netlist, LVS, and related operations:

```powershell
cli-anything-ledit --json macro-extract-action --action run --def-file C:\path\extract.def --spice-out outputs\out.sp --write-node-names --compile
cli-anything-ledit --json macro-extract-action --action run-command-file --path C:\path\lvs.cal --spice-out outputs\out.sp --compile
cli-anything-ledit --json macro-extract-action --action run-hiper --compile
cli-anything-ledit --json macro-extract-action --action set-options --def-file C:\path\extract.def --spice-out outputs\out.sp --write-node-names --write-parasitic-cap --compile
cli-anything-ledit --json macro-extract-action --action open-summary --compile
cli-anything-ledit --json macro-extract-action --action open-statistics --compile
```

Supported extract actions are `run`, `run-command-file`, `run-hiper`,
`set-options`, `open-summary`, and `open-statistics`. The `run` action
uses the legacy `LExtract_Run` API with explicit def file and SPICE output
paths. `set-options` reads the current options via `LExtract_GetOptionsEx840`,
updates the specified fields, and writes them back with `LExtract_SetOptionsEx840`.
Options include `--write-node-names`, `--write-node-capacitance`, and
`--write-parasitic-cap`.

`macro-via-action` covers via definition and fill operations:

```powershell
cli-anything-ledit --json macro-via-action --action add --lower-layer Metal1 --upper-layer Metal2 --via-cell VIA1 --pitch-x 0.5 --pitch-y 0.5 --compile
cli-anything-ledit --json macro-via-action --action count --compile
cli-anything-ledit --json macro-via-action --action find --via-def-name VIA1 --compile
cli-anything-ledit --json macro-via-action --action find-by-layer --lower-layer Metal1 --upper-layer Metal2 --compile
cli-anything-ledit --json macro-via-action --action fill --via-def-name VIA1 --x1 0 --y1 0 --x2 10 --y2 10 --compile
cli-anything-ledit --json macro-via-action --action delete-all --compile
```

Supported via actions are `add`, `delete-all`, `fill`, `find`, `find-by-layer`, and `count`.

`macro-basepoint-action` covers basepoint mode and cell basepoint coordinates:

```powershell
cli-anything-ledit --json macro-basepoint-action --action get-mode --compile
cli-anything-ledit --json macro-basepoint-action --action set-mode --enabled --compile
cli-anything-ledit --json macro-basepoint-action --action get --compile
cli-anything-ledit --json macro-basepoint-action --action set --x 1.5 --y 2.5 --compile
```

Supported basepoint actions are `get-mode`, `set-mode`, `get`, and `set`.

`macro-layer-params-action` covers layer parameters including GDS number/datatype, CIF name, capacitance, resistivity, and layer visibility:

```powershell
cli-anything-ledit --json macro-layer-params-action --action get --layer Metal1 --compile
cli-anything-ledit --json macro-layer-params-action --action set --layer Metal1 --gds-number 10 --gds-datatype 0 --compile
cli-anything-ledit --json macro-layer-params-action --action set-cap --layer Metal1 --cap 2.0 --compile
cli-anything-ledit --json macro-layer-params-action --action set-rho --layer Metal1 --rho 0.05 --compile
cli-anything-ledit --json macro-layer-params-action --action set-fringe-cap --layer Metal1 --fringe-cap 0.1 --compile
```

Supported layer-params actions are `get`, `set`, `set-cap`, `set-rho`, and `set-fringe-cap`.
The `set` action accepts `--gds-number`, `--gds-datatype`, `--cif-name`, `--cap`, `--rho`,
`--fringe-cap`, `--locked`/`--unlocked`, and `--hidden`/`--visible`.

In the current observed environment, compiled macros export `UPI_Entry_Point`
correctly, but `ledit64.exe -U ...` did not write the smoke receipt while an
existing single-instance L-Edit process was present. Treat execution as
experimental until it is re-tested after closing existing L-Edit instances.

Before any `--execute` run, use `upi-preflight`:

```powershell
cli-anything-ledit --json upi-preflight --macro outputs/cell_ensure_nofocus.upi
```

By default this blocks clean-instance execution when any `ledit64.exe` process
is already running, because an existing single-instance L-Edit session may
receive or suppress `-U` macro startup. Use `--allow-existing-process` only
when you intentionally want to test that risky behavior and are ready for
L-Edit to launch or activate.
