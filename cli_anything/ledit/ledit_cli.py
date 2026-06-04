from __future__ import annotations

import json
from pathlib import Path

import click

from .core.script_writer import (
    CURRENT_LAYER,
    LayoutScriptSpec,
    LayerProbeSpec,
    SquareArraySpec,
    build_run_command,
    write_layout_script,
    write_layer_probe,
    write_square_array,
)
from .core.macro_writer import (
    BASEPOINT_ACTIONS,
    CELL_ACTIONS,
    CELL_INFO_ACTIONS,
    DRC_ACTIONS,
    EXTRACT_ACTIONS,
    FILE_ACTIONS,
    GRID_ACTIONS,
    IO_ACTIONS,
    LAYER_ACTIONS,
    LAYER_PARAMS_ACTIONS,
    OBJECT_PROPERTY_ACTIONS,
    SELECTION_ACTIONS,
    NET_INFO_ACTIONS,
    TECHNOLOGY_ACTIONS,
    VIA_ACTIONS,
    WINDOW_ACTIONS,
    write_basepoint_upi_macro,
    write_cell_info_upi_macro,
    write_cell_upi_macro,
    write_drc_upi_macro,
    write_extract_upi_macro,
    write_file_upi_macro,
    write_grid_upi_macro,
    write_io_upi_macro,
    write_layer_params_upi_macro,
    write_layer_upi_macro,
    write_object_upi_macro,
    write_object_property_upi_macro,
    write_selection_upi_macro,
    write_square_array_upi_macro,
    write_technology_upi_macro,
    write_upi_smoke_macro,
    write_net_info_upi_macro,
    write_via_upi_macro,
    write_window_upi_macro,
)
from .core.verify import verify_layout_script, verify_square_array_script
from .core.session import LEditSession
from .utils.ledit_backend import compile_upi_macro, execute_upi_macro, inspect_install, launch_ledit, preflight_upi_execution, send_run_script


def emit(data: dict[str, object], as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if data.get("ok") is False:
        click.echo(f"ERROR: {data.get('error')}", err=True)
        return
    for key, value in data.items():
        click.echo(f"{key}: {value}")


def format_launch_command(launch_receipt: dict[str, object], executable_macro: Path) -> str | None:
    launch = launch_receipt.get("launch")
    if not launch_receipt.get("ok") or not isinstance(launch, dict):
        return None
    ledit_exe = launch.get("ledit_exe")
    args = launch.get("args")
    if not ledit_exe or not isinstance(args, list):
        return None
    quoted_args = " ".join(f'"{arg}"' if " " in str(arg) else str(arg) for arg in args)
    return f'"{ledit_exe}" {quoted_args}'.strip() or f'"{ledit_exe}" -U "{executable_macro}"'


@click.group(invoke_without_command=True)
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
@click.pass_context


def main(ctx: click.Context, as_json: bool) -> None:
    """CLI-Anything harness for Tanner L-Edit."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = as_json
    ctx.obj["session"] = LEditSession()
    if ctx.invoked_subcommand is None:
        repl(ctx)


def _run_macro_pipeline(
    ctx: click.Context,
    receipt: dict[str, object],
    write_fn,
    write_kwargs: dict[str, object],
    exported_functions: list[str],
    macro_label: str,
    *,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float = 4.0,
    check_receipt_file: bool = True,
) -> None:
    """Shared pipeline: write -> compile -> execute -> emit for all UPI macro commands."""
    try:
        write_receipt = write_fn(**write_kwargs)
        receipt.update(write_receipt)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=exported_functions)
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = (
                    compile_receipt.get("error")
                    or compile_receipt.get("stderr")
                    or f"Failed to compile {macro_label} UPI macro."
                )
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            if not launch_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = launch_receipt.get("error", "Failed to launch L-Edit with macro.")
            if check_receipt_file:
                receipt_file = Path(str(receipt.get("receipt_file", "")))
                receipt["receipt_exists"] = receipt_file.exists()
                receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
                if not receipt["receipt_exists"]:
                    receipt["ok"] = False
                    receipt["error"] = f"L-Edit launched, but the {macro_label} macro did not write its receipt file."
    except Exception as exc:
        receipt["ok"] = False
        receipt["error"] = str(exc)
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])

@main.command("inspect")
@click.pass_context
def inspect_cmd(ctx: click.Context) -> None:
    """Inspect local L-Edit paths and script execution hint."""
    emit({"ok": True, **inspect_install()}, ctx.obj["json"])


@main.command("capabilities")
@click.pass_context
def capabilities_cmd(ctx: click.Context) -> None:
    """Report the layered L-Edit automation capabilities exposed by this harness."""
    emit(
        {
            "ok": True,
            "layers": [
                {
                    "name": "command-window-script",
                    "status": "usable",
                    "commands": [
                        "cell",
                        "layer",
                        "box",
                        "square-array",
                        "path/wire",
                        "polygon",
                        "text",
                        "width",
                        "goto",
                        "instance",
                        "array",
                        "copy",
                        "move",
                        "paste",
                        "rotate",
                        "save",
                        "saveas",
                        "raw-safe-command",
                    ],
                    "entrypoints": [
                        "layout-script",
                        "draw-square-array",
                        "box",
                        "path",
                        "polygon",
                        "text",
                        "instance",
                        "width",
                        "goto",
                        "array",
                        "copy",
                        "move",
                        "paste",
                        "rotate",
                        "saveas",
                        "run-script",
                    ],
                    "notes": "layout-script and draw-square-array only write files unless --send-run-command is used.",
                },
                {
                    "name": "upi-macro",
                    "status": "experimental",
                    "commands": [
                        "macro-smoke",
                        "macro-square-array",
                        "macro-selection-action",
                        "macro-object-action",
                        "macro-object-property-action",
                        "macro-file-action",
                        "macro-layer-action",
                        "macro-cell-action",
                        "macro-window-action",
                        "macro-io-action",
                        "macro-grid-action",
                        "macro-drc-action",
                        "macro-extract-action",
                        "macro-via-action",
                        "macro-basepoint-action",
                        "macro-layer-params-action",
                        "macro-technology-action",
                        "macro-cell-info-action",
                        "macro-net-info-action",
                        "upi-preflight",
                    ],
                    "notes": "Uses ledit64.exe -U and does not simulate keyboard input; object, file/cell/view, layer, cell, window, import/export, grid, DRC, and preflight actions cover more basic layout operations; clean-instance execution still needs validation.",
                },
                {
                    "name": "interactive-window-sendkeys",
                    "status": "usable-with-consent",
                    "commands": ["run-script", "--send-run-command"],
                    "notes": "This route focuses L-Edit and sends keystrokes. Use only when the user is ready for foreground control.",
                },
                {
                    "name": "window-ui",
                    "status": "planned",
                    "commands": ["dialog workflows", "technology setup", "DRC/extraction setup", "macro manager"],
                    "notes": "Use only for UI surfaces that are not available through command scripts or UPI.",
                },
            ],
        },
        ctx.obj["json"],
    )


@main.command("upi-preflight")
@click.option("--macro", "macro_path", type=click.Path(path_type=Path), default=None, help="Optional .cpp or .upi macro path to check.")
@click.option("--allow-existing-process", is_flag=True, help="Warn instead of blocking when L-Edit is already running.")
@click.option("--no-default-args", is_flag=True, help="Do not include the default -s -n startup flags in the launch plan.")
@click.option("--macro-first", is_flag=True, help="Plan -U before extra startup arguments.")
@click.pass_context
def upi_preflight_cmd(
    ctx: click.Context,
    macro_path: Path | None,
    allow_existing_process: bool,
    no_default_args: bool,
    macro_first: bool,
) -> None:
    """Check whether UPI -U execution is safe before launching L-Edit."""
    receipt = preflight_upi_execution(
        macro_path,
        default_args=not no_default_args,
        macro_first=macro_first,
        require_clean_instance=not allow_existing_process,
    )
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("launch")
@click.option(
    "--open-script",
    "script_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional path to a generated .tco file. This only reports the run command; L-Edit executes .tco files from its command window.",
)
@click.pass_context
def launch_cmd(ctx: click.Context, script_path: Path | None) -> None:
    """Launch L-Edit using the first existing executable path."""
    receipt = launch_ledit()
    if receipt.get("ok") and script_path is not None:
        receipt["script"] = str(script_path.resolve())
        receipt["run_command"] = build_run_command(script_path.resolve())
    emit(receipt, ctx.obj["json"])


@main.command("run-script")
@click.argument("script_path", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--launch", is_flag=True, help="Launch L-Edit first, then attempt to send the run command.")
@click.option("--wait-ms", type=int, default=1200, show_default=True, help="Wait after launch before sending.")
@click.pass_context
def run_script_cmd(ctx: click.Context, script_path: Path, launch: bool, wait_ms: int) -> None:
    """Interactively send a generated .tco run command to a visible L-Edit window."""
    receipt: dict[str, object] = {
        "ok": False,
        "sent": False,
        "script": str(script_path.resolve()),
        "run_command": build_run_command(script_path.resolve()),
        "launch": None,
    }
    if launch:
        import time

        launch_receipt = launch_ledit()
        receipt["launch"] = launch_receipt
        if not launch_receipt.get("ok"):
            receipt["error"] = launch_receipt.get("error", "Failed to launch L-Edit.")
            ctx.obj["session"].record(receipt)
            emit(receipt, ctx.obj["json"])
            return
        time.sleep(max(wait_ms, 0) / 1000.0)
    send_receipt = send_run_script(script_path)
    receipt.update(send_receipt)
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


def build_square_array_spec(
    rows: int,
    cols: int,
    size: float,
    pitch: float | None,
    pitch_x: float | None,
    pitch_y: float | None,
    origin_x: float,
    origin_y: float,
    layer: str,
    cell: str,
) -> SquareArraySpec:
    resolved_pitch_x = pitch_x if pitch_x is not None else pitch
    resolved_pitch_y = pitch_y if pitch_y is not None else pitch
    if resolved_pitch_x is None:
        resolved_pitch_x = size
    if resolved_pitch_y is None:
        resolved_pitch_y = size
    return SquareArraySpec(
        rows=rows,
        cols=cols,
        size=size,
        pitch_x=resolved_pitch_x,
        pitch_y=resolved_pitch_y,
        layer=layer,
        cell=cell,
        origin_x=origin_x,
        origin_y=origin_y,
    )


def write_single_operation_script(
    ctx: click.Context,
    operation: dict[str, object],
    out_path: Path,
    *,
    cell: str,
    layer: str,
    title: str,
    save: bool = True,
) -> None:
    try:
        spec = LayoutScriptSpec(operations=[operation], cell=cell, layer=layer, title=title, save=save)
        receipt = write_layout_script(spec, out_path)
        verify_receipt = verify_layout_script(Path(receipt["script"]))
        receipt["verified"] = verify_receipt.ok
        receipt["verify"] = verify_receipt.__dict__
        if not verify_receipt.ok:
            receipt["ok"] = False
            receipt["error"] = "; ".join(verify_receipt.errors)
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("square-array")
@click.option("--rows", type=int, required=True, help="Number of array rows.")
@click.option("--cols", type=int, required=True, help="Number of array columns.")
@click.option("--size", type=float, required=True, help="Square side length in L-Edit display units.")
@click.option("--pitch", type=float, default=None, help="Pitch in both x and y directions.")
@click.option("--pitch-x", type=float, default=None, help="Pitch in x direction.")
@click.option("--pitch-y", type=float, default=None, help="Pitch in y direction.")
@click.option("--origin-x", type=float, default=0.0, show_default=True)
@click.option("--origin-y", type=float, default=0.0, show_default=True)
@click.option("--layer", default=CURRENT_LAYER, show_default=True, help="L-Edit layer name, or CURRENT to use the active layer.")
@click.option("--cell", default="TOP", show_default=True, help="L-Edit cell name.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/square_array.tco"),
    show_default=True,
    help="Output Tanner Command File path.",
)
@click.pass_context
def square_array_cmd(
    ctx: click.Context,
    rows: int,
    cols: int,
    size: float,
    pitch: float | None,
    pitch_x: float | None,
    pitch_y: float | None,
    origin_x: float,
    origin_y: float,
    layer: str,
    cell: str,
    out_path: Path,
) -> None:
    """Generate a L-Edit .tco script that draws a square array."""
    try:
        spec = build_square_array_spec(rows, cols, size, pitch, pitch_x, pitch_y, origin_x, origin_y, layer, cell)
        receipt = write_square_array(spec, out_path)
    except Exception as exc:  # Click should present validation failures as JSON too.
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("draw-square-array")
@click.option("--rows", type=int, required=True, help="Number of array rows.")
@click.option("--cols", type=int, required=True, help="Number of array columns.")
@click.option("--size", type=float, required=True, help="Square side length in L-Edit display units.")
@click.option("--pitch", type=float, default=None, help="Pitch in both x and y directions.")
@click.option("--pitch-x", type=float, default=None, help="Pitch in x direction.")
@click.option("--pitch-y", type=float, default=None, help="Pitch in y direction.")
@click.option("--origin-x", type=float, default=0.0, show_default=True)
@click.option("--origin-y", type=float, default=0.0, show_default=True)
@click.option("--layer", default=CURRENT_LAYER, show_default=True, help="L-Edit layer name, or CURRENT to use the active layer.")
@click.option("--cell", default="TOP", show_default=True, help="L-Edit cell name.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/square_array.tco"),
    show_default=True,
    help="Output Tanner Command File path.",
)
@click.option("--launch", is_flag=True, help="Also launch L-Edit after writing and verifying the script.")
@click.option(
    "--send-run-command",
    is_flag=True,
    help="After writing, focus L-Edit and send the run command with keystrokes.",
)
@click.pass_context
def draw_square_array_cmd(
    ctx: click.Context,
    rows: int,
    cols: int,
    size: float,
    pitch: float | None,
    pitch_x: float | None,
    pitch_y: float | None,
    origin_x: float,
    origin_y: float,
    layer: str,
    cell: str,
    out_path: Path,
    launch: bool,
    send_run_command: bool,
) -> None:
    """Generate, verify, and optionally launch L-Edit for a square-array script."""
    try:
        spec = build_square_array_spec(rows, cols, size, pitch, pitch_x, pitch_y, origin_x, origin_y, layer, cell)
        write_receipt = write_square_array(spec, out_path)
        verify_receipt = verify_square_array_script(Path(write_receipt["script"]), spec)
        receipt: dict[str, object] = {
            **write_receipt,
            "verified": verify_receipt.ok,
            "verify": verify_receipt.__dict__,
            "launched_ledit": False,
            "launch": None,
        }
        if not verify_receipt.ok:
            receipt["ok"] = False
            receipt["error"] = "; ".join(verify_receipt.errors)
        elif launch:
            launch_receipt = launch_ledit()
            receipt["launched_ledit"] = bool(launch_receipt.get("ok"))
            receipt["launch"] = launch_receipt
        if verify_receipt.ok and send_run_command:
            send_receipt = send_run_script(Path(write_receipt["script"]))
            receipt["sent_run_command"] = bool(send_receipt.get("sent"))
            receipt["send"] = send_receipt
            if not send_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = str(send_receipt.get("error", "Failed to send run command to L-Edit."))
        else:
            receipt.setdefault("sent_run_command", False)
            receipt.setdefault("send", None)
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("layer-probe")
@click.option("--layer", required=True, help="Real L-Edit layer name to probe. CURRENT is not allowed.")
@click.option("--cell", default="TOP", show_default=True, help="L-Edit cell name.")
@click.option("--origin-x", type=float, default=0.0, show_default=True)
@click.option("--origin-y", type=float, default=0.0, show_default=True)
@click.option("--marker-size", type=float, default=0.2, show_default=True, help="Small marker box side length.")
@click.option("--no-marker", is_flag=True, help="Only test layer selection, without drawing a marker box.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/layer_probe.tco"),
    show_default=True,
    help="Output Tanner Command File path.",
)
@click.pass_context
def layer_probe_cmd(
    ctx: click.Context,
    layer: str,
    cell: str,
    origin_x: float,
    origin_y: float,
    marker_size: float,
    no_marker: bool,
    out_path: Path,
) -> None:
    """Generate a tiny .tco that probes whether L-Edit accepts a named layer."""
    try:
        spec = LayerProbeSpec(
            layer=layer,
            cell=cell,
            origin_x=origin_x,
            origin_y=origin_y,
            marker_size=marker_size,
            draw_marker=not no_marker,
        )
        receipt = write_layer_probe(spec, out_path)
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("box")
@click.option("--x1", type=float, required=True)
@click.option("--y1", type=float, required=True)
@click.option("--x2", type=float, required=True)
@click.option("--y2", type=float, required=True)
@click.option("--layer", default=CURRENT_LAYER, show_default=True)
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/box.tco"), show_default=True)
@click.pass_context
def box_cmd(ctx: click.Context, x1: float, y1: float, x2: float, y2: float, layer: str, cell: str, out_path: Path) -> None:
    """Generate and verify a one-box L-Edit script."""
    write_single_operation_script(
        ctx,
        {"op": "box", "x1": x1, "y1": y1, "x2": x2, "y2": y2},
        out_path,
        cell=cell,
        layer=layer,
        title="box",
    )


@main.command("path")
@click.option("--point", "points", type=(float, float), multiple=True, required=True, help="Path point; repeat at least twice.")
@click.option("--width", "path_width", type=float, default=None, help="Optional path width.")
@click.option("--layer", default=CURRENT_LAYER, show_default=True)
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/path.tco"), show_default=True)
@click.pass_context
def path_cmd(
    ctx: click.Context,
    points: tuple[tuple[float, float], ...],
    path_width: float | None,
    layer: str,
    cell: str,
    out_path: Path,
) -> None:
    """Generate and verify a path/wire L-Edit script."""
    operation: dict[str, object] = {"op": "path", "points": [list(point) for point in points]}
    if path_width is not None:
        operation["width"] = path_width
    write_single_operation_script(ctx, operation, out_path, cell=cell, layer=layer, title="path")


@main.command("polygon")
@click.option("--point", "points", type=(float, float), multiple=True, required=True, help="Polygon point; repeat at least three times.")
@click.option("--layer", default=CURRENT_LAYER, show_default=True)
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/polygon.tco"), show_default=True)
@click.pass_context
def polygon_cmd(ctx: click.Context, points: tuple[tuple[float, float], ...], layer: str, cell: str, out_path: Path) -> None:
    """Generate and verify a polygon L-Edit script."""
    write_single_operation_script(
        ctx,
        {"op": "polygon", "points": [list(point) for point in points]},
        out_path,
        cell=cell,
        layer=layer,
        title="polygon",
    )


@main.command("text")
@click.option("--label", required=True)
@click.option("--x", type=float, required=True)
@click.option("--y", type=float, required=True)
@click.option("--layer", default=CURRENT_LAYER, show_default=True)
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/text.tco"), show_default=True)
@click.pass_context
def text_cmd(ctx: click.Context, label: str, x: float, y: float, layer: str, cell: str, out_path: Path) -> None:
    """Generate and verify a text label L-Edit script."""
    write_single_operation_script(
        ctx,
        {"op": "text", "label": label, "x": x, "y": y},
        out_path,
        cell=cell,
        layer=layer,
        title="text",
    )


@main.command("instance")
@click.option("--cell-name", required=True, help="Referenced cell name to instantiate.")
@click.option("--x", type=float, required=True)
@click.option("--y", type=float, required=True)
@click.option("--file", "source_file", default=None, help="Optional source file for the instance cell.")
@click.option("--cell", default="TOP", show_default=True, help="Target L-Edit cell name.")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/instance.tco"), show_default=True)
@click.pass_context
def instance_cmd(ctx: click.Context, cell_name: str, x: float, y: float, source_file: str | None, cell: str, out_path: Path) -> None:
    """Generate and verify an instance-placement L-Edit script."""
    operation: dict[str, object] = {"op": "instance", "cell": cell_name, "x": x, "y": y}
    if source_file:
        operation["file"] = source_file
    write_single_operation_script(ctx, operation, out_path, cell=cell, layer=CURRENT_LAYER, title="instance")


@main.command("width")
@click.option("--value", type=float, default=None, help="Optional path width. Omit to query/reset through L-Edit command semantics.")
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/width.tco"), show_default=True)
@click.pass_context
def width_cmd(ctx: click.Context, value: float | None, cell: str, out_path: Path) -> None:
    """Generate and verify a path-width L-Edit script."""
    operation: dict[str, object] = {"op": "width"}
    if value is not None:
        operation["value"] = value
    write_single_operation_script(ctx, operation, out_path, cell=cell, layer=CURRENT_LAYER, title="width", save=False)


@main.command("goto")
@click.option("--x", type=float, required=True)
@click.option("--y", type=float, required=True)
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/goto.tco"), show_default=True)
@click.pass_context
def goto_cmd(ctx: click.Context, x: float, y: float, cell: str, out_path: Path) -> None:
    """Generate and verify a goto-view L-Edit script."""
    write_single_operation_script(ctx, {"op": "goto", "x": x, "y": y}, out_path, cell=cell, layer=CURRENT_LAYER, title="goto", save=False)


@main.command("array")
@click.option("--cols", type=int, required=True)
@click.option("--rows", type=int, required=True)
@click.option("--pitch", type=float, default=None, help="Pitch in both x and y directions.")
@click.option("--pitch-x", type=float, default=None, help="Pitch in x direction.")
@click.option("--pitch-y", type=float, default=None, help="Pitch in y direction.")
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/array.tco"), show_default=True)
@click.pass_context
def array_cmd(
    ctx: click.Context,
    cols: int,
    rows: int,
    pitch: float | None,
    pitch_x: float | None,
    pitch_y: float | None,
    cell: str,
    out_path: Path,
) -> None:
    """Generate and verify an array-current-selection L-Edit script."""
    operation: dict[str, object] = {"op": "array", "cols": cols, "rows": rows}
    if pitch is not None:
        operation["pitch"] = pitch
    if pitch_x is not None:
        operation["pitch_x"] = pitch_x
    if pitch_y is not None:
        operation["pitch_y"] = pitch_y
    write_single_operation_script(ctx, operation, out_path, cell=cell, layer=CURRENT_LAYER, title="array")


@main.command("copy")
@click.option("--x", type=float, default=None)
@click.option("--y", type=float, default=None)
@click.option("--layer", default=CURRENT_LAYER, show_default=True)
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/copy.tco"), show_default=True)
@click.pass_context
def copy_cmd(ctx: click.Context, x: float | None, y: float | None, layer: str, cell: str, out_path: Path) -> None:
    """Generate and verify a copy-current-selection L-Edit script."""
    operation: dict[str, object] = {"op": "copy"}
    if (x is None) != (y is None):
        receipt = {"ok": False, "error": "--x and --y must be provided together for positioned copy."}
        ctx.obj["session"].record(receipt)
        emit(receipt, ctx.obj["json"])
        return
    if x is not None and y is not None:
        operation.update({"x": x, "y": y})
    write_single_operation_script(ctx, operation, out_path, cell=cell, layer=layer, title="copy")


@main.command("move")
@click.option("--x", type=float, required=True)
@click.option("--y", type=float, required=True)
@click.option("--mode", type=click.Choice(["absolute", "relative"]), default="absolute", show_default=True)
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/move.tco"), show_default=True)
@click.pass_context
def move_cmd(ctx: click.Context, x: float, y: float, mode: str, cell: str, out_path: Path) -> None:
    """Generate and verify a move-current-selection L-Edit script."""
    write_single_operation_script(ctx, {"op": "move", "x": x, "y": y, "mode": mode}, out_path, cell=cell, layer=CURRENT_LAYER, title="move")


@main.command("paste")
@click.option("--x", type=float, required=True)
@click.option("--y", type=float, required=True)
@click.option("--mode", type=click.Choice(["absolute", "relative"]), default="absolute", show_default=True)
@click.option("--layer", default=CURRENT_LAYER, show_default=True)
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/paste.tco"), show_default=True)
@click.pass_context
def paste_cmd(ctx: click.Context, x: float, y: float, mode: str, layer: str, cell: str, out_path: Path) -> None:
    """Generate and verify a paste-buffer L-Edit script."""
    write_single_operation_script(ctx, {"op": "paste", "x": x, "y": y, "mode": mode}, out_path, cell=cell, layer=layer, title="paste")


@main.command("rotate")
@click.option("--angle", type=float, required=True)
@click.option("--x", type=float, required=True)
@click.option("--y", type=float, required=True)
@click.option("--mode", type=click.Choice(["absolute", "relative"]), default="absolute", show_default=True)
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/rotate.tco"), show_default=True)
@click.pass_context
def rotate_cmd(ctx: click.Context, angle: float, x: float, y: float, mode: str, cell: str, out_path: Path) -> None:
    """Generate and verify a rotate-current-selection L-Edit script."""
    write_single_operation_script(
        ctx,
        {"op": "rotate", "angle": angle, "x": x, "y": y, "mode": mode},
        out_path,
        cell=cell,
        layer=CURRENT_LAYER,
        title="rotate",
    )


@main.command("saveas")
@click.option("--path", "target_path", required=True, help="Target TDB path for L-Edit saveas.")
@click.option("--cell", default="TOP", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/saveas.tco"), show_default=True)
@click.pass_context
def saveas_cmd(ctx: click.Context, target_path: str, cell: str, out_path: Path) -> None:
    """Generate and verify a saveas L-Edit script."""
    write_single_operation_script(
        ctx,
        {"op": "saveas", "path": target_path},
        out_path,
        cell=cell,
        layer=CURRENT_LAYER,
        title="saveas",
        save=False,
    )


@main.command("layout-script")
@click.argument("spec_path", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/layout_script.tco"),
    show_default=True,
    help="Output Tanner Command File path.",
)
@click.option("--launch", is_flag=True, help="Also launch L-Edit after writing the script.")
@click.option(
    "--send-run-command",
    is_flag=True,
    help="After writing, focus L-Edit and send the run command with keystrokes.",
)
@click.pass_context
def layout_script_cmd(ctx: click.Context, spec_path: Path, out_path: Path, launch: bool, send_run_command: bool) -> None:
    """Generate a composable L-Edit .tco script from a JSON layout spec."""
    try:
        data = json.loads(spec_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("layout spec must be a JSON object")
        spec = LayoutScriptSpec(
            operations=data.get("operations", []),
            cell=str(data.get("cell", "TOP")),
            layer=str(data.get("layer", CURRENT_LAYER)),
            save=bool(data.get("save", True)),
            title=str(data.get("title", spec_path.stem)),
        )
        receipt = write_layout_script(spec, out_path)
        verify_receipt = verify_layout_script(Path(receipt["script"]))
        receipt["verified"] = verify_receipt.ok
        receipt["verify"] = verify_receipt.__dict__
        if not verify_receipt.ok:
            receipt["ok"] = False
            receipt["error"] = "; ".join(verify_receipt.errors)
        receipt["launched_ledit"] = False
        receipt["launch"] = None
        if launch:
            launch_receipt = launch_ledit()
            receipt["launched_ledit"] = bool(launch_receipt.get("ok"))
            receipt["launch"] = launch_receipt
            if not launch_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = launch_receipt.get("error", "Failed to launch L-Edit.")
        if send_run_command and receipt.get("ok"):
            send_receipt = send_run_script(Path(receipt["script"]))
            receipt["sent_run_command"] = bool(send_receipt.get("sent"))
            receipt["send"] = send_receipt
            if not send_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = str(send_receipt.get("error", "Failed to send run command to L-Edit."))
        else:
            receipt.setdefault("sent_run_command", False)
            receipt.setdefault("send", None)
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("verify-layout-script")
@click.argument("script_path", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.pass_context
def verify_layout_script_cmd(ctx: click.Context, script_path: Path) -> None:
    """Verify and summarize a generated layout-script .tco without touching L-Edit."""
    receipt = verify_layout_script(script_path)
    ctx.obj["session"].record(receipt.__dict__)
    emit(receipt.__dict__, ctx.obj["json"])


@main.command("macro-square-array")
@click.option("--rows", type=int, required=True, help="Number of array rows.")
@click.option("--cols", type=int, required=True, help="Number of array columns.")
@click.option("--size", type=float, required=True, help="Square side length in L-Edit display units.")
@click.option("--pitch", type=float, default=None, help="Pitch in both x and y directions.")
@click.option("--pitch-x", type=float, default=None, help="Pitch in x direction.")
@click.option("--pitch-y", type=float, default=None, help="Pitch in y direction.")
@click.option("--origin-x", type=float, default=0.0, show_default=True)
@click.option("--origin-y", type=float, default=0.0, show_default=True)
@click.option("--layer", default=CURRENT_LAYER, show_default=True, help="L-Edit layer name, or CURRENT to use the active layer.")
@click.option("--cell", default="TOP", show_default=True, help="L-Edit cell name kept in the receipt; macro uses the visible cell.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/square_array_macro.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--tdb-out", "tdb_path", type=click.Path(path_type=Path), default=None, help="Have the macro create and save this .tdb file.")
@click.pass_context
def macro_square_array_cmd(
    ctx: click.Context,
    rows: int,
    cols: int,
    size: float,
    pitch: float | None,
    pitch_x: float | None,
    pitch_y: float | None,
    origin_x: float,
    origin_y: float,
    layer: str,
    cell: str,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    tdb_path: Path | None,
) -> None:
    """Generate a UPI macro that can be executed by L-Edit with -U."""
    try:
        spec = build_square_array_spec(rows, cols, size, pitch, pitch_x, pitch_y, origin_x, origin_y, layer, cell)
        receipt = write_square_array_upi_macro(spec, out_path, tdb_path=tdb_path)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro)
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(executable_macro, default_args=not no_default_args, macro_first=macro_first)
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            if not launch_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = launch_receipt.get("error", "Failed to launch L-Edit with macro.")
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-selection-action")
@click.option("--action", type=click.Choice(sorted(SELECTION_ACTIONS)), required=True)
@click.option("--dx", type=float, default=0.0, show_default=True, help="Move dx, or rotate center x, in display units.")
@click.option("--dy", type=float, default=0.0, show_default=True, help="Move dy, or rotate center y, in display units.")
@click.option("--angle", type=float, default=0.0, show_default=True, help="Rotate angle in degrees for --action rotate.")
@click.option("--group-name", default="CodexGroup", show_default=True, help="Group cell name for --action group.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/selection_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_selection_action_cmd(
    ctx: click.Context,
    action: str,
    dx: float,
    dy: float,
    angle: float,
    group_name: str,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for selection/edit actions such as copy, move, group, merge, and flatten."""
    try:
        receipt = write_selection_upi_macro(action, out_path, dx=dx, dy=dy, angle=angle, group_name=group_name)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexSelectionAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile selection UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the selection macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-object-action")
@click.option("--kind", type=click.Choice(["circle", "port", "torus", "pie"]), required=True, help="UPI object kind to create.")
@click.option("--x", type=float, default=0.0, show_default=True, help="Circle center x in display units.")
@click.option("--y", type=float, default=0.0, show_default=True, help="Circle center y in display units.")
@click.option("--radius", type=float, default=1.0, show_default=True, help="Circle/pie radius in display units.")
@click.option("--inner-radius", type=float, default=0.5, show_default=True, help="Torus inner radius in display units.")
@click.option("--outer-radius", type=float, default=1.0, show_default=True, help="Torus outer radius in display units.")
@click.option("--start-angle", type=float, default=0.0, show_default=True, help="Start angle for torus/pie in degrees.")
@click.option("--stop-angle", type=float, default=360.0, show_default=True, help="Stop angle for torus/pie in degrees.")
@click.option("--label", default="PORT", show_default=True, help="Port label for --kind port.")
@click.option("--x1", type=float, default=0.0, show_default=True, help="Port lower-left x in display units.")
@click.option("--y1", type=float, default=0.0, show_default=True, help="Port lower-left y in display units.")
@click.option("--x2", type=float, default=1.0, show_default=True, help="Port upper-right x in display units.")
@click.option("--y2", type=float, default=1.0, show_default=True, help="Port upper-right y in display units.")
@click.option("--layer", default=CURRENT_LAYER, show_default=True, help="L-Edit layer name, or CURRENT to use the active layer.")
@click.option("--cell", default="TOP", show_default=True, help="Cell name hint kept in the receipt; macro uses the visible cell.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/object_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_object_action_cmd(
    ctx: click.Context,
    kind: str,
    x: float,
    y: float,
    radius: float,
    inner_radius: float,
    outer_radius: float,
    start_angle: float,
    stop_angle: float,
    label: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    layer: str,
    cell: str,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for object creation not covered reliably by .tco scripts."""
    try:
        receipt = write_object_upi_macro(
            kind,
            out_path,
            layer=layer,
            cell=cell,
            x=x,
            y=y,
            radius=radius,
            inner_radius=inner_radius,
            outer_radius=outer_radius,
            start_angle=start_angle,
            stop_angle=stop_angle,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            label=label,
        )
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexObjectAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile object UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the object macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-file-action")
@click.option("--action", type=click.Choice(sorted(FILE_ACTIONS)), required=True)
@click.option("--path", "target_path", default=None, help="TDB path for new/open/saveas actions.")
@click.option("--cell", default="TOP", show_default=True, help="Cell name for new/open/open-cell actions.")
@click.option("--x", type=float, default=0.0, show_default=True, help="X coordinate for --action move-origin.")
@click.option("--y", type=float, default=0.0, show_default=True, help="Y coordinate for --action move-origin.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/file_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_file_action_cmd(
    ctx: click.Context,
    action: str,
    target_path: str | None,
    cell: str,
    x: float,
    y: float,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for file, cell, and view operations."""
    try:
        receipt = write_file_upi_macro(action, out_path, path=target_path, cell=cell, x=x, y=y)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexFileAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile file UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the file macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-layer-action")
@click.option("--action", type=click.Choice(sorted(LAYER_ACTIONS)), required=True)
@click.option("--layer", default=None, help="Layer name for ensure/set-current/delete/rename.")
@click.option("--new-name", default=None, help="New layer name for --action rename.")
@click.option("--source-layer", default=None, help="Source layer for --action change-selection-layer.")
@click.option("--target-layer", default=None, help="Target layer for --action change-selection-layer.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/layer_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_layer_action_cmd(
    ctx: click.Context,
    action: str,
    layer: str | None,
    new_name: str | None,
    source_layer: str | None,
    target_layer: str | None,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for layer setup and selection layer changes."""
    try:
        receipt = write_layer_upi_macro(
            action,
            out_path,
            layer=layer,
            new_name=new_name,
            source_layer=source_layer,
            target_layer=target_layer,
        )
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexLayerAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile layer UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the layer macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-cell-action")
@click.option("--action", type=click.Choice(sorted(CELL_ACTIONS)), required=True)
@click.option("--cell", default=None, help="Cell name for ensure/open/rename/delete/clear/flatten.")
@click.option("--new-name", default=None, help="New cell name for --action rename.")
@click.option("--source-cell", default=None, help="Source cell for --action copy.")
@click.option("--target-cell", default=None, help="Target cell for --action copy.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/cell_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_cell_action_cmd(
    ctx: click.Context,
    action: str,
    cell: str | None,
    new_name: str | None,
    source_cell: str | None,
    target_cell: str | None,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for cell setup and cell-level editing."""
    try:
        receipt = write_cell_upi_macro(
            action,
            out_path,
            cell=cell,
            new_name=new_name,
            source_cell=source_cell,
            target_cell=target_cell,
        )
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexCellAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile cell UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the cell macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-window-action")
@click.option("--action", type=click.Choice(sorted(WINDOW_ACTIONS)), required=True)
@click.option("--path", "target_path", default=None, help="File path for save-visible-image or load-text-window.")
@click.option("--text", default=None, help="Text content for --action new-text-window.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/window_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_window_action_cmd(
    ctx: click.Context,
    action: str,
    target_path: str | None,
    text: str | None,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for basic window and view operations."""
    try:
        receipt = write_window_upi_macro(action, out_path, path=target_path, text=text)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexWindowAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile window UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the window macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-io-action")
@click.option("--action", type=click.Choice(sorted(IO_ACTIONS)), required=True)
@click.option("--path", "target_path", default=None, help="Source path for imports or destination path for export-gds.")
@click.option("--log-path", default=None, help="Optional import/export log path.")
@click.option("--cell", default=None, help="Specified cell name for export-gds. Defaults to active cell.")
@click.option("--include-hierarchy/--flat", default=True, show_default=True, help="Include hierarchy for export-gds.")
@click.option("--hidden-objects/--visible-only", default=False, show_default=True, help="Include hidden objects and layers for export-gds.")
@click.option("--use-gds-datatype/--ignore-gds-datatype", default=True, show_default=True, help="Use GDS datatype during import-gds.")
@click.option("--polygon-as-rect", is_flag=True, help="Convert rectangular CIF polygons to boxes during import-cif.")
@click.option("--overwrite", type=click.Choice(["all", "top", "none"]), default="none", show_default=True, help="Cell overwrite policy for imports.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/io_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_io_action_cmd(
    ctx: click.Context,
    action: str,
    target_path: str | None,
    log_path: str | None,
    cell: str | None,
    include_hierarchy: bool,
    hidden_objects: bool,
    use_gds_datatype: bool,
    polygon_as_rect: bool,
    overwrite: str,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for GDS/CIF import and GDS export."""
    try:
        receipt = write_io_upi_macro(
            action,
            out_path,
            path=target_path,
            log_path=log_path,
            cell=cell,
            include_hierarchy=include_hierarchy,
            hidden_objects=hidden_objects,
            use_gds_datatype=use_gds_datatype,
            polygon_as_rect=polygon_as_rect,
            overwrite=overwrite,
        )
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexIOAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile IO UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the IO macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-grid-action")
@click.option("--action", type=click.Choice(sorted(GRID_ACTIONS)), required=True)
@click.option("--value", type=float, required=True, help="Grid value in current L-Edit display units.")
@click.option("--x", type=float, default=None, help="X snap grid value for set-snap-grid.")
@click.option("--y", type=float, default=None, help="Y snap grid value for set-snap-grid.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/grid_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_grid_action_cmd(
    ctx: click.Context,
    action: str,
    value: float,
    x: float | None,
    y: float | None,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for grid and manufacturing-grid setup."""
    try:
        receipt = write_grid_upi_macro(action, out_path, value=value, x=x, y=y)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexGridAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile grid UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the grid macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-drc-action")
@click.option("--action", type=click.Choice(sorted(DRC_ACTIONS)), required=True)
@click.option("--path", "target_path", default=None, help="Command-file or results path for DRC actions.")
@click.option("--rule-set", default=None, help="Rule-set name for set-rule-set.")
@click.option("--tolerance", type=int, default=0, show_default=True, help="DRC tolerance for set-tolerance.")
@click.option("--flag-acute/--no-flag-acute", default=False, show_default=True, help="Flag acute angles for set-flags.")
@click.option("--flag-all-angle/--no-flag-all-angle", default=False, show_default=True, help="Flag all-angle edges for set-flags.")
@click.option("--flag-off-grid/--no-flag-off-grid", default=False, show_default=True, help="Flag off-grid objects for set-flags.")
@click.option("--show-browser/--hide-browser", default=False, show_default=True, help="Show navigator when loading DRC results.")
@click.option("--x1", type=float, default=None, help="DRC area lower-left X.")
@click.option("--y1", type=float, default=None, help="DRC area lower-left Y.")
@click.option("--x2", type=float, default=None, help="DRC area upper-right X.")
@click.option("--y2", type=float, default=None, help="DRC area upper-right Y.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/drc_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_drc_action_cmd(
    ctx: click.Context,
    action: str,
    target_path: str | None,
    rule_set: str | None,
    tolerance: int,
    flag_acute: bool,
    flag_all_angle: bool,
    flag_off_grid: bool,
    show_browser: bool,
    x1: float | None,
    y1: float | None,
    x2: float | None,
    y2: float | None,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for DRC, marker, and DRC-result operations."""
    try:
        receipt = write_drc_upi_macro(
            action,
            out_path,
            path=target_path,
            rule_set=rule_set,
            tolerance=tolerance,
            flag_acute=flag_acute,
            flag_all_angle=flag_all_angle,
            flag_off_grid=flag_off_grid,
            show_browser=show_browser,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexDRCAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile DRC UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the DRC macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-object-property-action")
@click.option("--action", type=click.Choice(sorted(OBJECT_PROPERTY_ACTIONS)), required=True)
@click.option("--gds-datatype", type=int, default=0, show_default=True, help="GDS datatype for set-gds-datatype.")
@click.option("--net-name", default=None, help="Net name for set-net-name.")
@click.option("--layer", default=None, help="Target layer for change-layer or copy-to-layer.")
@click.option("--grid", type=float, default=1.0, show_default=True, help="Display-unit grid size for snap-to-grid.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/object_property_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_object_property_action_cmd(
    ctx: click.Context,
    action: str,
    gds_datatype: int,
    net_name: str | None,
    layer: str | None,
    grid: float,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for selected-object properties and conversions."""
    try:
        receipt = write_object_property_upi_macro(
            action,
            out_path,
            gds_datatype=gds_datatype,
            net_name=net_name,
            layer=layer,
            grid=grid,
        )
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexObjectPropertyAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile object-property UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the object-property macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-smoke")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/codex_macro_smoke.cpp"),
    show_default=True,
    help="Output smoke-test UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated smoke macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_smoke_cmd(
    ctx: click.Context,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a minimal UPI macro that only writes a receipt file."""
    try:
        receipt = write_upi_smoke_macro(out_path)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexSmokeMacro"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile smoke UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the smoke macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("verify-script")
@click.argument("script_path", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--rows", type=int, required=True, help="Expected number of array rows.")
@click.option("--cols", type=int, required=True, help="Expected number of array columns.")
@click.option("--size", type=float, required=True, help="Expected square side length.")
@click.option("--pitch", type=float, default=None, help="Expected uniform pitch in x and y.")
@click.option("--pitch-x", type=float, default=None, help="Expected pitch in x direction.")
@click.option("--pitch-y", type=float, default=None, help="Expected pitch in y direction.")
@click.option("--origin-x", type=float, default=0.0, show_default=True)
@click.option("--origin-y", type=float, default=0.0, show_default=True)
@click.option("--layer", default=CURRENT_LAYER, show_default=True, help="Expected L-Edit layer name, or CURRENT when no layer command is expected.")
@click.option("--cell", default="TOP", show_default=True, help="Expected L-Edit cell name.")
@click.pass_context
def verify_script_cmd(
    ctx: click.Context,
    script_path: Path,
    rows: int,
    cols: int,
    size: float,
    pitch: float | None,
    pitch_x: float | None,
    pitch_y: float | None,
    origin_x: float,
    origin_y: float,
    layer: str,
    cell: str,
) -> None:
    spec = build_square_array_spec(rows, cols, size, pitch, pitch_x, pitch_y, origin_x, origin_y, layer, cell)
    receipt = verify_square_array_script(script_path, spec)
    ctx.obj["session"].record(receipt.__dict__)
    emit(receipt.__dict__, ctx.obj["json"])



@main.command("macro-extract-action")
@click.option("--action", type=click.Choice(sorted(EXTRACT_ACTIONS)), required=True)
@click.option("--def-file", default=None, help="Extraction definition file for run or set-options.")
@click.option("--spice-out", default=None, help="SPICE output file path for run, run-command-file, or set-options.")
@click.option("--path", "target_path", default=None, help="Command file path for run-command-file.")
@click.option("--write-node-names/--no-write-node-names", default=False, show_default=True, help="Write node names for run or set-options.")
@click.option("--write-node-capacitance/--no-write-node-capacitance", default=False, show_default=True, help="Write node capacitance for run.")
@click.option("--write-parasitic-cap/--no-write-parasitic-cap", default=False, show_default=True, help="Write parasitic capacitance for set-options.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("outputs/extract_action.cpp"),
    show_default=True,
    help="Output L-Edit UPI macro source path.",
)
@click.option("--execute", is_flag=True, help="Launch L-Edit with -U <macro> after writing it.")
@click.option("--compile", "compile_macro", is_flag=True, help="Compile the generated macro to a .upi plugin.")
@click.option("--interpreted", is_flag=True, help="Use the generated .cpp directly with -U instead of compiling to .upi.")
@click.option("--no-default-args", is_flag=True, help="Do not pass the default -s -n startup flags to L-Edit.")
@click.option("--macro-first", is_flag=True, help="Pass -U before any extra startup arguments.")
@click.option("--wait-seconds", type=float, default=4.0, show_default=True, help="Wait for L-Edit to execute the macro before checking receipt.")
@click.pass_context
def macro_extract_action_cmd(
    ctx: click.Context,
    action: str,
    def_file: str | None,
    spice_out: str | None,
    target_path: str | None,
    write_node_names: bool,
    write_node_capacitance: bool,
    write_parasitic_cap: bool,
    out_path: Path,
    execute: bool,
    compile_macro: bool,
    interpreted: bool,
    no_default_args: bool,
    macro_first: bool,
    wait_seconds: float,
) -> None:
    """Generate a UPI macro for extraction, netlist, and LVS operations."""
    try:
        # For run-command-file, use --path as the def_file
        effective_def_file = target_path if action == "run-command-file" else def_file
        receipt = write_extract_upi_macro(
            action,
            out_path,
            def_file=effective_def_file,
            spice_out=spice_out,
            write_node_names=write_node_names,
            write_node_capacitance=write_node_capacitance,
            write_parasitic_cap=write_parasitic_cap,
        )
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexExtractAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile extract UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(
                executable_macro,
                wait_seconds=wait_seconds,
                default_args=not no_default_args,
                macro_first=macro_first,
            )
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            receipt_file = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = receipt_file.exists()
            receipt["receipt_text"] = receipt_file.read_text(encoding="utf-8") if receipt_file.exists() else None
            if not receipt["receipt_exists"]:
                receipt["ok"] = False
                receipt["error"] = "L-Edit launched, but the extract macro did not write its receipt file."
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])



@main.command("macro-via-action")
@click.option("--action", type=click.Choice(sorted(VIA_ACTIONS)), required=True)
@click.option("--lower-layer", default=None, help="Lower layer name for add or find-by-layer.")
@click.option("--upper-layer", default=None, help="Upper layer name for add or find-by-layer.")
@click.option("--via-cell", default=None, help="Via cell name for add.")
@click.option("--via-def-name", default=None, help="Via definition cell name for find or fill.")
@click.option("--pitch-x", type=float, default=1.0, show_default=True, help="Via pitch X for add.")
@click.option("--pitch-y", type=float, default=1.0, show_default=True, help="Via pitch Y for add.")
@click.option("--x1", type=float, default=None, help="Fill area lower-left X.")
@click.option("--y1", type=float, default=None, help="Fill area lower-left Y.")
@click.option("--x2", type=float, default=None, help="Fill area upper-right X.")
@click.option("--y2", type=float, default=None, help="Fill area upper-right Y.")
@click.option("--fill-area/--no-fill-area", default=False, show_default=True, help="Fill entire area for fill action.")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/via_action.cpp"), show_default=True)
@click.option("--execute", is_flag=True)
@click.option("--compile", "compile_macro", is_flag=True)
@click.option("--interpreted", is_flag=True)
@click.option("--no-default-args", is_flag=True)
@click.option("--macro-first", is_flag=True)
@click.option("--wait-seconds", type=float, default=4.0, show_default=True)
@click.pass_context
def macro_via_action_cmd(ctx, action, lower_layer, upper_layer, via_cell, via_def_name, pitch_x, pitch_y, x1, y1, x2, y2, fill_area, out_path, execute, compile_macro, interpreted, no_default_args, macro_first, wait_seconds):
    """Generate a UPI macro for via definition and fill operations."""
    try:
        receipt = write_via_upi_macro(action, out_path, lower_layer=lower_layer, upper_layer=upper_layer, via_cell=via_cell, via_def_name=via_def_name, pitch_x=pitch_x, pitch_y=pitch_y, x1=x1, y1=y1, x2=x2, y2=y2, fill_area=fill_area)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexViaAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile via UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(executable_macro, wait_seconds=wait_seconds, default_args=not no_default_args, macro_first=macro_first)
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            rf = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = rf.exists()
            receipt["receipt_text"] = rf.read_text(encoding="utf-8") if rf.exists() else None
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-basepoint-action")
@click.option("--action", type=click.Choice(sorted(BASEPOINT_ACTIONS)), required=True)
@click.option("--enabled/--disabled", default=True, show_default=True, help="Enable or disable basepoint mode for set-mode.")
@click.option("--x", type=float, default=None, help="Base point X coordinate for set.")
@click.option("--y", type=float, default=None, help="Base point Y coordinate for set.")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/basepoint_action.cpp"), show_default=True)
@click.option("--execute", is_flag=True)
@click.option("--compile", "compile_macro", is_flag=True)
@click.option("--interpreted", is_flag=True)
@click.option("--no-default-args", is_flag=True)
@click.option("--macro-first", is_flag=True)
@click.option("--wait-seconds", type=float, default=4.0, show_default=True)
@click.pass_context
def macro_basepoint_action_cmd(ctx, action, enabled, x, y, out_path, execute, compile_macro, interpreted, no_default_args, macro_first, wait_seconds):
    """Generate a UPI macro for basepoint mode and cell basepoint."""
    try:
        receipt = write_basepoint_upi_macro(action, out_path, enabled=enabled, x=x, y=y)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexBasepointAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile basepoint UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(executable_macro, wait_seconds=wait_seconds, default_args=not no_default_args, macro_first=macro_first)
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            rf = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = rf.exists()
            receipt["receipt_text"] = rf.read_text(encoding="utf-8") if rf.exists() else None
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-layer-params-action")
@click.option("--action", type=click.Choice(sorted(LAYER_PARAMS_ACTIONS)), required=True)
@click.option("--layer", required=True, help="Target layer name.")
@click.option("--gds-number", type=int, default=None, help="GDSII layer number.")
@click.option("--gds-datatype", type=int, default=None, help="GDSII data type.")
@click.option("--cif-name", default=None, help="CIF layer name (max 6 chars).")
@click.option("--cap", type=float, default=None, help="Area capacitance in aF/sq.um.")
@click.option("--rho", type=float, default=None, help="Sheet resistivity in ohms/sq.")
@click.option("--fringe-cap", type=float, default=None, help="Fringe capacitance in fF/um.")
@click.option("--locked/--unlocked", default=None, help="Lock or unlock the layer.")
@click.option("--hidden/--visible", default=None, help="Hide or show the layer.")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/layer_params_action.cpp"), show_default=True)
@click.option("--execute", is_flag=True)
@click.option("--compile", "compile_macro", is_flag=True)
@click.option("--interpreted", is_flag=True)
@click.option("--no-default-args", is_flag=True)
@click.option("--macro-first", is_flag=True)
@click.option("--wait-seconds", type=float, default=4.0, show_default=True)
@click.pass_context
def macro_layer_params_action_cmd(ctx, action, layer, gds_number, gds_datatype, cif_name, cap, rho, fringe_cap, locked, hidden, out_path, execute, compile_macro, interpreted, no_default_args, macro_first, wait_seconds):
    """Generate a UPI macro for layer parameters (GDS, CIF, cap, rho, etc.)."""
    try:
        receipt = write_layer_params_upi_macro(action, out_path, layer=layer, gds_number=gds_number, gds_datatype=gds_datatype, cif_name=cif_name, cap=cap, rho=rho, fringe_cap=fringe_cap, locked=locked, hidden=hidden)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexLayerParamsAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile layer-params UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(executable_macro, wait_seconds=wait_seconds, default_args=not no_default_args, macro_first=macro_first)
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            rf = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = rf.exists()
            receipt["receipt_text"] = rf.read_text(encoding="utf-8") if rf.exists() else None
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])



@main.command("macro-technology-action")
@click.option("--action", type=click.Choice(sorted(TECHNOLOGY_ACTIONS)), required=True)
@click.option("--tech-name", default=None, help="Technology name for set-name.")
@click.option("--unit-name", default=None, help="Unit name for set-unit-name.")
@click.option("--unit-num", type=int, default=None, help="Unit numerator for set-unit.")
@click.option("--unit-denom", type=int, default=None, help="Unit denominator for set-unit.")
@click.option("--lambda-num", type=int, default=None, help="Lambda numerator for set-lambda.")
@click.option("--lambda-denom", type=int, default=None, help="Lambda denominator for set-lambda.")
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/technology_action.cpp"), show_default=True)
@click.option("--execute", is_flag=True)
@click.option("--compile", "compile_macro", is_flag=True)
@click.option("--interpreted", is_flag=True)
@click.option("--no-default-args", is_flag=True)
@click.option("--macro-first", is_flag=True)
@click.option("--wait-seconds", type=float, default=4.0, show_default=True)
@click.pass_context
def macro_technology_action_cmd(ctx, action, tech_name, unit_name, unit_num, unit_denom, lambda_num, lambda_denom, out_path, execute, compile_macro, interpreted, no_default_args, macro_first, wait_seconds):
    """Generate a UPI macro for technology setup (name, units, lambda)."""
    try:
        receipt = write_technology_upi_macro(action, out_path, tech_name=tech_name, unit_name=unit_name, unit_num=unit_num, unit_denom=unit_denom, lambda_num=lambda_num, lambda_denom=lambda_denom)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexTechnologyAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile technology UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(executable_macro, wait_seconds=wait_seconds, default_args=not no_default_args, macro_first=macro_first)
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            rf = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = rf.exists()
            receipt["receipt_text"] = rf.read_text(encoding="utf-8") if rf.exists() else None
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


@main.command("macro-cell-info-action")
@click.option("--action", type=click.Choice(sorted(CELL_INFO_ACTIONS)), required=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/cell_info_action.cpp"), show_default=True)
@click.option("--execute", is_flag=True)
@click.option("--compile", "compile_macro", is_flag=True)
@click.option("--interpreted", is_flag=True)
@click.option("--no-default-args", is_flag=True)
@click.option("--macro-first", is_flag=True)
@click.option("--wait-seconds", type=float, default=4.0, show_default=True)
@click.pass_context
def macro_cell_info_action_cmd(ctx, action, out_path, execute, compile_macro, interpreted, no_default_args, macro_first, wait_seconds):
    """Generate a UPI macro for cell information queries."""
    try:
        receipt = write_cell_info_upi_macro(action, out_path)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexCellInfoAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile cell-info UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(executable_macro, wait_seconds=wait_seconds, default_args=not no_default_args, macro_first=macro_first)
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            rf = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = rf.exists()
            receipt["receipt_text"] = rf.read_text(encoding="utf-8") if rf.exists() else None
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])



@main.command("macro-net-info-action")
@click.option("--action", type=click.Choice(sorted(NET_INFO_ACTIONS)), required=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("outputs/net_info_action.cpp"), show_default=True)
@click.option("--execute", is_flag=True)
@click.option("--compile", "compile_macro", is_flag=True)
@click.option("--interpreted", is_flag=True)
@click.option("--no-default-args", is_flag=True)
@click.option("--macro-first", is_flag=True)
@click.option("--wait-seconds", type=float, default=4.0, show_default=True)
@click.pass_context
def macro_net_info_action_cmd(ctx, action, out_path, execute, compile_macro, interpreted, no_default_args, macro_first, wait_seconds):
    """Generate a UPI macro for net information queries."""
    try:
        receipt = write_net_info_upi_macro(action, out_path)
        receipt["execute_command"] = None
        receipt["launch"] = None
        receipt["compile"] = None
        executable_macro = Path(receipt["macro"])
        if interpreted and compile_macro:
            raise click.ClickException("--interpreted cannot be combined with --compile.")
        if not interpreted and (compile_macro or execute):
            compile_receipt = compile_upi_macro(executable_macro, exported_functions=["CodexNetInfoAction"])
            receipt["compile"] = compile_receipt
            if not compile_receipt.get("ok"):
                receipt["ok"] = False
                receipt["error"] = compile_receipt.get("error") or compile_receipt.get("stderr") or "Failed to compile net-info UPI macro."
                ctx.obj["session"].record(receipt)
                emit(receipt, ctx.obj["json"])
                return
            executable_macro = Path(str(compile_receipt["upi"]))
        if execute:
            launch_receipt = execute_upi_macro(executable_macro, wait_seconds=wait_seconds, default_args=not no_default_args, macro_first=macro_first)
            receipt["launch"] = launch_receipt
            receipt["execute_command"] = format_launch_command(launch_receipt, executable_macro)
            rf = Path(str(receipt["receipt_file"]))
            receipt["receipt_exists"] = rf.exists()
            receipt["receipt_text"] = rf.read_text(encoding="utf-8") if rf.exists() else None
    except Exception as exc:
        receipt = {"ok": False, "error": str(exc)}
    ctx.obj["session"].record(receipt)
    emit(receipt, ctx.obj["json"])


def repl(ctx: click.Context) -> None:
    as_json = ctx.obj["json"]
    if as_json:
        emit(
            {
                "ok": True,
                "mode": "repl",
                "message": "Run a subcommand such as square-array for non-interactive JSON use.",
            },
            True,
        )
        return
    click.echo("cli-anything-ledit REPL. Type 'help' or 'quit'.")
    while True:
        command = click.prompt("ledit", default="", show_default=False)
        if command.strip() in {"quit", "exit"}:
            return
        if command.strip() == "help":
            click.echo("Use: square-array ROWS COLS SIZE PITCH [LAYER]")
            continue
        parts = command.split()
        if parts[:1] == ["square-array"] and len(parts) >= 5:
            rows, cols = int(parts[1]), int(parts[2])
            size, pitch = float(parts[3]), float(parts[4])
            layer = parts[5] if len(parts) > 5 else CURRENT_LAYER
            spec = SquareArraySpec(rows=rows, cols=cols, size=size, pitch_x=pitch, pitch_y=pitch, layer=layer)
            receipt = write_square_array(spec, Path("outputs/square_array.tco"))
            ctx.obj["session"].record(receipt)
            emit(receipt, False)
            continue
        click.echo("Unknown command. Type 'help'.")
