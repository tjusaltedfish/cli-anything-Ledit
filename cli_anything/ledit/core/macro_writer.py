from __future__ import annotations

from pathlib import Path

from .script_writer import CURRENT_LAYER, SquareArraySpec, format_number

SELECTION_ACTIONS = {
    "select-all",
    "deselect-all",
    "cut",
    "copy",
    "clear",
    "paste",
    "duplicate",
    "group",
    "ungroup",
    "merge",
    "flatten",
    "flip-horizontal",
    "flip-vertical",
    "snap-to-mfg-grid",
    "move",
    "rotate",
}

FILE_ACTIONS = {
    "new",
    "open",
    "save",
    "saveas",
    "close",
    "open-cell",
    "home-view",
    "move-origin",
    "clear-cell",
}

LAYER_ACTIONS = {
    "ensure",
    "set-current",
    "delete",
    "rename",
    "change-selection-layer",
}

CELL_ACTIONS = {
    "ensure",
    "open",
    "copy",
    "rename",
    "delete",
    "clear",
    "flatten",
}

WINDOW_ACTIONS = {
    "home-visible-cell",
    "make-first-layout-visible",
    "save-visible-image",
    "new-text-window",
    "load-text-window",
    "close-visible-window",
}

IO_ACTIONS = {
    "import-gds",
    "import-cif",
    "export-gds",
}

GRID_ACTIONS = {
    "set-manufacturing-grid",
    "set-display-grid",
    "set-snap-grid",
    "set-major-grid",
}

DRC_ACTIONS = {
    "run",
    "run-command-file",
    "set-rule-set",
    "set-tolerance",
    "set-flags",
    "open-summary",
    "open-statistics",
    "load-results",
    "clear-markers",
    "show-global-markers",
    "hide-global-markers",
    "status",
}

OBJECT_PROPERTY_ACTIONS = {
    "set-gds-datatype",
    "set-net-name",
    "clear-net-name",
    "change-layer",
    "snap-to-grid",
    "snap-to-mfg-grid",
    "copy-to-layer",
    "delete",
    "convert-to-polygon",
}

EXTRACT_ACTIONS = {
    "run",
    "run-command-file",
    "run-hiper",
    "set-options",
    "open-summary",
    "open-statistics",
}


def _c_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _coord_expr(value: float) -> str:
    return f"LFile_DispUtoIntU(file, {format_number(value)})"


def _tdb_save_base(path: Path | str) -> str:
    resolved = Path(path).resolve()
    if resolved.suffix.lower() == ".tdb":
        resolved = resolved.with_suffix("")
    return str(resolved)


def _receipt_helper(receipt_path: Path | None) -> list[str]:
    if receipt_path is None:
        return [
            "static void CodexWriteReceipt(const char* status, int boxes) {",
            "    (void)status;",
            "    (void)boxes;",
            "}",
        ]
    receipt_text = str(receipt_path.resolve())
    return [
        "static void CodexWriteReceipt(const char* status, int boxes) {",
        "    FILE* receipt = fopen(" + _c_string(receipt_text) + ', "w");',
        "    if (receipt) {",
        '        fprintf(receipt, "status=%s\\nboxes=%d\\n", status, boxes);',
        "        fclose(receipt);",
        "    }",
        "}",
    ]


def build_square_array_upi_macro(
    spec: SquareArraySpec,
    receipt_path: Path | None = None,
    tdb_path: Path | None = None,
) -> str:
    spec.validate()
    is_batch_file = tdb_path is not None
    if spec.layer.upper() == CURRENT_LAYER and is_batch_file:
        layer_expr = 'LLayer_Find(file, "CodexLayer")'
        layer_create_lines = [
            "    if (!layer) {",
            '        LLayer_New(file, LLayer_GetList(file), "CodexLayer");',
            '        layer = LLayer_Find(file, "CodexLayer");',
            "    }",
        ]
        layer_comment = "auto-created CodexLayer for batch output"
    elif spec.layer.upper() == CURRENT_LAYER:
        layer_expr = "LLayer_GetCurrent(file)"
        layer_create_lines = []
        layer_comment = "current active layer"
    else:
        layer_expr = f"LLayer_Find(file, {_c_string(spec.layer)})"
        layer_create_lines = [
            "    if (!layer) {",
            f"        LLayer_New(file, LLayer_GetList(file), {_c_string(spec.layer)});",
            f"        layer = LLayer_Find(file, {_c_string(spec.layer)});",
            "    }",
        ]
        layer_comment = spec.layer

    box_lines = []
    for x1, y1, x2, y2 in spec.boxes():
        box_lines.append(
            "    LBox_New(cell, layer, "
            f"{_coord_expr(x1)}, {_coord_expr(y1)}, {_coord_expr(x2)}, {_coord_expr(y2)});"
        )

    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexSquareArray(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            (
                "    LFile file = LFile_New(NULL, "
                + _c_string(tdb_path.stem if tdb_path is not None else "codex_square_array")
                + ");"
                if tdb_path is not None
                else "    LFile file = LFile_GetVisible();"
            ),
            (
                f"    LCell cell = LCell_New(file, {_c_string(spec.cell)});"
                if tdb_path is not None
                else "    LCell cell = LCell_GetVisible();"
            ),
            "    if (!file || !cell) {",
            '        CodexWriteReceipt("missing_file_or_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    // Target layer: {layer_comment}",
            f"    LLayer layer = {layer_expr};",
            *layer_create_lines,
            "    if (!layer) {",
            '        CodexWriteReceipt("missing_layer", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    LLayer_SetCurrent(file, layer);",
            "    LCell_MakeVisible(cell);",
            *box_lines,
            (
                "    LFile_SaveAs(file, " + _c_string(str(tdb_path.resolve().with_suffix(""))) + ", LTdbFile);"
                if tdb_path is not None
                else "    LFile_Save(file);"
            ),
            "    LDisplay_Refresh();",
            f'    CodexWriteReceipt("ok", {spec.count});',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Square Array", "CodexSquareArray");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_square_array_upi_macro(
    spec: SquareArraySpec,
    out_path: Path,
    receipt_path: Path | None = None,
    tdb_path: Path | None = None,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_square_array_upi_macro(spec, receipt_path, tdb_path), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "tdb_file": str(tdb_path.resolve()) if tdb_path is not None else None,
        "spec": spec.to_dict(),
        "box_count": spec.count,
        "bounds": spec.bounds,
    }


def build_upi_smoke_macro(receipt_path: Path) -> str:
    receipt_text = str(receipt_path.resolve())
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            'extern "C" void CodexSmokeMacro(void) {',
            "    FILE* receipt = fopen(" + _c_string(receipt_text) + ', "w");',
            "    if (receipt) {",
            '        fprintf(receipt, "status=ok\\nmacro=CodexSmokeMacro\\n");',
            "        fclose(receipt);",
            "    }",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            "    CodexSmokeMacro();",
            '    LMacro_Register("Codex Smoke Macro", "CodexSmokeMacro");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_upi_smoke_macro(out_path: Path, receipt_path: Path | None = None) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_upi_smoke_macro(receipt_path), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
    }


def _selection_action_lines(action: str, *, dx: float, dy: float, angle: float, group_name: str) -> list[str]:
    if action not in SELECTION_ACTIONS:
        raise ValueError(f"unsupported selection action: {action}")
    if action == "select-all":
        return ["    LSelection_SelectAll();"]
    if action == "deselect-all":
        return ["    LSelection_DeselectAll();"]
    if action == "cut":
        return ["    status = LSelection_Cut();"]
    if action == "copy":
        return ["    status = LSelection_Copy();"]
    if action == "clear":
        return ["    status = LSelection_Clear();"]
    if action == "paste":
        return ["    status = LSelection_Paste();"]
    if action == "duplicate":
        return ["    status = LSelection_Duplicate();"]
    if action == "group":
        return [f"    status = LSelection_Group({_c_string(group_name)});"]
    if action == "ungroup":
        return ["    status = LSelection_UnGroup();"]
    if action == "merge":
        return ["    status = LSelection_Merge();"]
    if action == "flatten":
        return ["    status = LSelection_Flatten();"]
    if action == "flip-horizontal":
        return ["    status = LSelection_FlipHorizontal();"]
    if action == "flip-vertical":
        return ["    status = LSelection_FlipVertical();"]
    if action == "snap-to-mfg-grid":
        return ["    status = LSelection_SnapToMfgGrid();"]
    if action == "move":
        return [
            "    status = LSelection_Move("
            f"LFile_DispUtoIntU(file, {format_number(dx)}), "
            f"LFile_DispUtoIntU(file, {format_number(dy)}));"
        ]
    if action == "rotate":
        return [
            "    status = LSelection_RotateAroundPoint("
            f"{format_number(angle)}, "
            f"LFile_DispUtoIntU(file, {format_number(dx)}), "
            f"LFile_DispUtoIntU(file, {format_number(dy)}), 0);"
        ]
    raise ValueError(f"unsupported selection action: {action}")


def build_selection_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    dx: float = 0.0,
    dy: float = 0.0,
    angle: float = 0.0,
    group_name: str = "CodexGroup",
) -> str:
    action = action.lower()
    action_lines = _selection_action_lines(action, dx=dx, dy=dy, angle=angle, group_name=group_name)
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexSelectionAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LFile file = LFile_GetVisible();",
            "    LCell cell = LCell_GetVisible();",
            "    LStatus status = LStatusOK;",
            "    if (!file || !cell) {",
            '        CodexWriteReceipt("missing_file_or_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            *action_lines,
            "    LFile_Save(file);",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Selection Action", "CodexSelectionAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_selection_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    *,
    dx: float = 0.0,
    dy: float = 0.0,
    angle: float = 0.0,
    group_name: str = "CodexGroup",
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        build_selection_upi_macro(action, receipt_path, dx=dx, dy=dy, angle=angle, group_name=group_name),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "dx": dx,
        "dy": dy,
        "angle": angle,
        "group_name": group_name,
    }


def _layer_lookup_lines(layer_name: str) -> list[str]:
    if layer_name.upper() == CURRENT_LAYER:
        return [
            "    LLayer layer = LLayer_GetCurrent(file);",
        ]
    return [
        f"    LLayer layer = LLayer_Find(file, {_c_string(layer_name)});",
        "    if (!layer) {",
        f"        LLayer_New(file, LLayer_GetList(file), {_c_string(layer_name)});",
        f"        layer = LLayer_Find(file, {_c_string(layer_name)});",
        "    }",
    ]


def build_object_upi_macro(
    kind: str,
    receipt_path: Path | None = None,
    *,
    layer: str = CURRENT_LAYER,
    cell: str = "TOP",
    x: float = 0.0,
    y: float = 0.0,
    radius: float = 1.0,
    inner_radius: float = 0.5,
    outer_radius: float = 1.0,
    start_angle: float = 0.0,
    stop_angle: float = 360.0,
    x1: float = 0.0,
    y1: float = 0.0,
    x2: float = 1.0,
    y2: float = 1.0,
    label: str = "PORT",
) -> str:
    kind = kind.lower()
    if kind not in {"circle", "port", "torus", "pie"}:
        raise ValueError(f"unsupported object macro kind: {kind}")
    if kind == "circle" and radius <= 0:
        raise ValueError("circle radius must be greater than zero")
    if kind == "circle":
        object_lines = [
            "    LPoint center = LPoint_Set("
            f"LFile_DispUtoIntU(file, {format_number(x)}), "
            f"LFile_DispUtoIntU(file, {format_number(y)}));",
            f"    LObject object = LCircle_New(cell, layer, center, LFile_DispUtoIntU(file, {format_number(radius)}));",
            "    if (!object) {",
            '        CodexWriteReceipt("create_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
        ]
    elif kind == "torus":
        object_lines = [
            "    LTorusParams torusParams;",
            f"    torusParams.ptCenter = LPoint_Set(LFile_DispUtoIntU(file, {format_number(x)}), LFile_DispUtoIntU(file, {format_number(y)}));",
            f"    torusParams.nInnerRadius = LFile_DispUtoIntU(file, {format_number(inner_radius)});",
            f"    torusParams.nOuterRadius = LFile_DispUtoIntU(file, {format_number(outer_radius)});",
            f"    torusParams.dStartAngle = {format_number(start_angle)};",
            f"    torusParams.dStopAngle = {format_number(stop_angle)};",
            "    LObject object = LTorus_CreateNew(cell, layer, &torusParams);",
            "    if (!object) {",
            '        CodexWriteReceipt("create_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
        ]
    elif kind == "pie":
        object_lines = [
            "    LPieParams pieParams;",
            f"    pieParams.ptCenter = LPoint_Set(LFile_DispUtoIntU(file, {format_number(x)}), LFile_DispUtoIntU(file, {format_number(y)}));",
            f"    pieParams.nRadius = LFile_DispUtoIntU(file, {format_number(radius)});",
            f"    pieParams.dStartAngle = {format_number(start_angle)};",
            f"    pieParams.dStopAngle = {format_number(stop_angle)};",
            "    LObject object = LPie_CreateNew(cell, layer, &pieParams);",
            "    if (!object) {",
            '        CodexWriteReceipt("create_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
        ]
    else:
        object_lines = [
            "    LPort port = LPort_New(cell, layer, "
            f"{_c_string(label)}, "
            f"LFile_DispUtoIntU(file, {format_number(x1)}), "
            f"LFile_DispUtoIntU(file, {format_number(y1)}), "
            f"LFile_DispUtoIntU(file, {format_number(x2)}), "
            f"LFile_DispUtoIntU(file, {format_number(y2)}));",
            "    if (!port) {",
            '        CodexWriteReceipt("create_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
        ]
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexObjectAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LFile file = LFile_GetVisible();",
            "    LCell cell = LCell_GetVisible();",
            "    if (!file || !cell) {",
            '        CodexWriteReceipt("missing_file_or_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            *_layer_lookup_lines(layer),
            "    if (!layer) {",
            '        CodexWriteReceipt("missing_layer", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    // Target cell hint from CLI: {_c_string(cell)}",
            *object_lines,
            "    LFile_Save(file);",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt("ok", 1);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Object Action", "CodexObjectAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_object_upi_macro(
    kind: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_object_upi_macro(kind, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "kind": kind.lower(),
        "params": kwargs,
    }


def _file_action_lines(
    action: str,
    *,
    path: str | None,
    cell: str,
    x: float,
    y: float,
) -> list[str]:
    if action not in FILE_ACTIONS:
        raise ValueError(f"unsupported file action: {action}")
    if action in {"new", "open", "saveas"} and not path:
        raise ValueError(f"{action} requires --path")
    if action == "new":
        tdb_name = Path(str(path)).resolve().stem
        return [
            f"    file = LFile_New(NULL, {_c_string(tdb_name)});",
            "    if (!file) {",
            '        CodexWriteReceipt("new_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    cell = LCell_Find(file, {_c_string(cell)});",
            "    if (!cell) {",
            f"        cell = LCell_New(file, {_c_string(cell)});",
            "    }",
            f"    status = LFile_SaveAs(file, {_c_string(_tdb_save_base(str(path)))}, LTdbFile);",
        ]
    if action == "open":
        return [
            f"    file = LFile_Open({_c_string(str(Path(str(path)).resolve()))}, LTdbFile);",
            "    if (!file) {",
            '        CodexWriteReceipt("open_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    cell = LCell_Find(file, {_c_string(cell)});",
            "    if (!cell) {",
            f"        cell = LCell_New(file, {_c_string(cell)});",
            "    }",
            "    LCell_MakeVisible(cell);",
            "    status = LStatusOK;",
        ]
    if action == "save":
        return [
            "    file = LFile_GetVisible();",
            "    cell = LCell_GetVisible();",
            "    if (!file || !cell) {",
            '        CodexWriteReceipt("missing_file_or_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LFile_Save(file);",
        ]
    if action == "saveas":
        return [
            "    file = LFile_GetVisible();",
            "    cell = LCell_GetVisible();",
            "    if (!file || !cell) {",
            '        CodexWriteReceipt("missing_file_or_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    status = LFile_SaveAs(file, {_c_string(_tdb_save_base(str(path)))}, LTdbFile);",
        ]
    if action == "close":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LFile_Close(file);",
        ]
    if action == "open-cell":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    LWindow window = LFile_OpenCell(file, {_c_string(cell)});",
            "    if (!window) {",
            '        CodexWriteReceipt("open_cell_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LWindow_MakeVisible(window);",
        ]
    if action == "home-view":
        return [
            "    file = LFile_GetVisible();",
            "    cell = LCell_GetVisible();",
            "    if (!file || !cell) {",
            '        CodexWriteReceipt("missing_file_or_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LCell_HomeView(cell);",
        ]
    if action == "move-origin":
        return [
            "    file = LFile_GetVisible();",
            "    cell = LCell_GetVisible();",
            "    if (!file || !cell) {",
            '        CodexWriteReceipt("missing_file_or_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    status = LCell_MoveOrigin(cell, {_coord_expr(x)}, {_coord_expr(y)});",
        ]
    if action == "clear-cell":
        return [
            "    file = LFile_GetVisible();",
            "    cell = LCell_GetVisible();",
            "    if (!file || !cell) {",
            '        CodexWriteReceipt("missing_file_or_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LCell_ClearContents(cell);",
        ]
    raise ValueError(f"unsupported file action: {action}")


def build_file_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    path: str | None = None,
    cell: str = "TOP",
    x: float = 0.0,
    y: float = 0.0,
) -> str:
    action = action.lower()
    action_lines = _file_action_lines(action, path=path, cell=cell, x=x, y=y)
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexFileAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LCell cell = NULL;",
            *action_lines,
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex File Action", "CodexFileAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_file_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_file_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


def _layer_require_name(action: str, value: str | None, option: str = "--layer") -> str:
    if not value:
        raise ValueError(f"{action} requires {option}")
    if value.upper() == CURRENT_LAYER:
        raise ValueError(f"{action} requires a real layer name, not CURRENT")
    return value


def _layer_action_lines(
    action: str,
    *,
    layer: str | None,
    new_name: str | None,
    source_layer: str | None,
    target_layer: str | None,
) -> list[str]:
    if action not in LAYER_ACTIONS:
        raise ValueError(f"unsupported layer action: {action}")
    if action in {"ensure", "set-current", "delete", "rename"}:
        layer = _layer_require_name(action, layer)
    if action == "rename":
        new_name = _layer_require_name(action, new_name, "--new-name")
    if action == "change-selection-layer":
        source_layer = _layer_require_name(action, source_layer, "--source-layer")
        target_layer = _layer_require_name(action, target_layer, "--target-layer")

    if action == "ensure":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    layer = LLayer_Find(file, {_c_string(str(layer))});",
            "    if (!layer) {",
            f"        status = LLayer_New(file, LLayer_GetList(file), {_c_string(str(layer))});",
            f"        layer = LLayer_Find(file, {_c_string(str(layer))});",
            "    }",
            "    if (!layer) {",
            '        CodexWriteReceipt("layer_create_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LLayer_SetCurrent(file, layer);",
        ]
    if action == "set-current":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    layer = LLayer_Find(file, {_c_string(str(layer))});",
            "    if (!layer) {",
            '        CodexWriteReceipt("missing_layer", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LLayer_SetCurrent(file, layer);",
        ]
    if action == "delete":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    layer = LLayer_Find(file, {_c_string(str(layer))});",
            "    if (!layer) {",
            '        CodexWriteReceipt("missing_layer", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LLayer_Delete(file, layer);",
        ]
    if action == "rename":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    layer = LLayer_Find(file, {_c_string(str(layer))});",
            "    if (!layer) {",
            '        CodexWriteReceipt("missing_layer", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    status = LLayer_SetName(layer, {_c_string(str(new_name))});",
        ]
    if action == "change-selection-layer":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    sourceLayer = LLayer_Find(file, {_c_string(str(source_layer))});",
            "    if (!sourceLayer) {",
            '        CodexWriteReceipt("missing_source_layer", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    targetLayer = LLayer_Find(file, {_c_string(str(target_layer))});",
            "    if (!targetLayer) {",
            f"        status = LLayer_New(file, LLayer_GetList(file), {_c_string(str(target_layer))});",
            f"        targetLayer = LLayer_Find(file, {_c_string(str(target_layer))});",
            "    }",
            "    if (!targetLayer) {",
            '        CodexWriteReceipt("target_layer_create_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LSelection_ChangeLayer(sourceLayer, targetLayer);",
        ]
    raise ValueError(f"unsupported layer action: {action}")


def build_layer_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    layer: str | None = None,
    new_name: str | None = None,
    source_layer: str | None = None,
    target_layer: str | None = None,
) -> str:
    action = action.lower()
    action_lines = _layer_action_lines(
        action,
        layer=layer,
        new_name=new_name,
        source_layer=source_layer,
        target_layer=target_layer,
    )
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexLayerAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LLayer layer = NULL;",
            "    LLayer sourceLayer = NULL;",
            "    LLayer targetLayer = NULL;",
            *action_lines,
            "    if (file) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Layer Action", "CodexLayerAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_layer_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_layer_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


def _cell_require_name(action: str, value: str | None, option: str = "--cell") -> str:
    if not value:
        raise ValueError(f"{action} requires {option}")
    return value


def _cell_action_lines(
    action: str,
    *,
    cell: str | None,
    new_name: str | None,
    source_cell: str | None,
    target_cell: str | None,
) -> list[str]:
    if action not in CELL_ACTIONS:
        raise ValueError(f"unsupported cell action: {action}")
    if action in {"ensure", "open", "rename", "delete", "clear", "flatten"}:
        cell = _cell_require_name(action, cell)
    if action == "rename":
        new_name = _cell_require_name(action, new_name, "--new-name")
    if action == "copy":
        source_cell = _cell_require_name(action, source_cell, "--source-cell")
        target_cell = _cell_require_name(action, target_cell, "--target-cell")

    if action == "ensure":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    cell = LCell_Find(file, {_c_string(str(cell))});",
            "    if (!cell) {",
            f"        cell = LCell_New(file, {_c_string(str(cell))});",
            "    }",
            "    if (!cell) {",
            '        CodexWriteReceipt("cell_create_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LCell_MakeVisible(cell);",
        ]
    if action == "open":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    cell = LCell_Find(file, {_c_string(str(cell))});",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LCell_MakeVisible(cell);",
        ]
    if action == "copy":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    sourceCell = LCell_Find(file, {_c_string(str(source_cell))});",
            "    if (!sourceCell) {",
            '        CodexWriteReceipt("missing_source_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    status = LCell_Copy(file, sourceCell, file, {_c_string(str(target_cell))});",
        ]
    if action == "rename":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    cell = LCell_Find(file, {_c_string(str(cell))});",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    status = LCell_SetName(file, cell, {_c_string(str(new_name))});",
        ]
    if action == "delete":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    cell = LCell_Find(file, {_c_string(str(cell))});",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LCell_Delete(cell);",
        ]
    if action == "clear":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    cell = LCell_Find(file, {_c_string(str(cell))});",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LCell_ClearContents(cell);",
        ]
    if action == "flatten":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    cell = LCell_Find(file, {_c_string(str(cell))});",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    LCell flattened = LCell_Flatten(cell);",
            "    if (!flattened) {",
            '        CodexWriteReceipt("flatten_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    cell = flattened;",
            "    status = LStatusOK;",
        ]
    raise ValueError(f"unsupported cell action: {action}")


def build_cell_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    cell: str | None = None,
    new_name: str | None = None,
    source_cell: str | None = None,
    target_cell: str | None = None,
) -> str:
    action = action.lower()
    action_lines = _cell_action_lines(
        action,
        cell=cell,
        new_name=new_name,
        source_cell=source_cell,
        target_cell=target_cell,
    )
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexCellAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LCell cell = NULL;",
            "    LCell sourceCell = NULL;",
            *action_lines,
            "    if (file) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Cell Action", "CodexCellAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_cell_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_cell_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


def _window_require_path(action: str, value: str | None, option: str = "--path") -> str:
    if not value:
        raise ValueError(f"{action} requires {option}")
    return value


def _window_action_lines(action: str, *, path: str | None, text: str | None) -> list[str]:
    if action not in WINDOW_ACTIONS:
        raise ValueError(f"unsupported window action: {action}")

    if action == "home-visible-cell":
        return [
            "    cell = LCell_GetVisible();",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LCell_HomeView(cell);",
        ]
    if action == "make-first-layout-visible":
        return [
            "    for (window = LWindow_GetList(); window; window = LWindow_GetNext(window)) {",
            "        LWindowType windowType = LWindow_GetType(window);",
            "        if (windowType == LAYOUT || windowType == CROSS_SECTION) {",
            "            status = LWindow_MakeVisible(window);",
            "            break;",
            "        }",
            "    }",
            "    if (!window) {",
            '        CodexWriteReceipt("missing_layout_window", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
        ]
    if action == "save-visible-image":
        image_path = _window_require_path(action, path)
        return [
            "    window = LWindow_GetVisible();",
            "    if (!window) {",
            '        CodexWriteReceipt("missing_window", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    status = LWindow_SaveImageToFile(window, {_c_string(str(Path(image_path).resolve()))});",
        ]
    if action == "new-text-window":
        window_text = text if text is not None else ""
        return [
            "    window = LWindow_NewTextWindow(NULL, TEXT);",
            "    if (!window) {",
            '        CodexWriteReceipt("text_window_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    status = LWindow_SetText(window, {_c_string(window_text)});",
            "    if (status == LStatusOK) {",
            "        status = LWindow_MakeVisible(window);",
            "    }",
        ]
    if action == "load-text-window":
        text_path = _window_require_path(action, path)
        return [
            f"    window = LWindow_LoadTextFile({_c_string(str(Path(text_path).resolve()))}, TEXT);",
            "    if (!window) {",
            '        CodexWriteReceipt("load_text_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LWindow_MakeVisible(window);",
        ]
    if action == "close-visible-window":
        return [
            "    window = LWindow_GetVisible();",
            "    if (!window) {",
            '        CodexWriteReceipt("missing_window", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    if (LWindow_IsLast(window) != 0) {",
            '        CodexWriteReceipt("refuse_close_last_window", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LWindow_Close(window);",
        ]
    raise ValueError(f"unsupported window action: {action}")


def build_window_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    path: str | None = None,
    text: str | None = None,
) -> str:
    action = action.lower()
    action_lines = _window_action_lines(action, path=path, text=text)
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexWindowAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LWindow window = NULL;",
            "    LCell cell = NULL;",
            *action_lines,
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Window Action", "CodexWindowAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_window_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_window_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


def _io_require_path(action: str, value: str | None, option: str = "--path") -> str:
    if not value:
        raise ValueError(f"{action} requires {option}")
    return str(Path(value).resolve())


def _io_action_lines(
    action: str,
    *,
    path: str | None,
    log_path: str | None,
    cell: str | None,
    include_hierarchy: bool,
    hidden_objects: bool,
    use_gds_datatype: bool,
    polygon_as_rect: bool,
    overwrite: str,
) -> list[str]:
    if action not in IO_ACTIONS:
        raise ValueError(f"unsupported IO action: {action}")
    target_path = _io_require_path(action, path)
    log_expr = _c_string(str(Path(log_path).resolve())) if log_path else "NULL"
    overwrite_map = {
        "all": "cOverwriteAllCells",
        "top": "cOverwriteCellsInTopDesignOnly",
        "none": "cDontOverwriteCells",
    }
    if overwrite not in overwrite_map:
        raise ValueError("--overwrite must be one of: all, top, none")
    overwrite_expr = overwrite_map[overwrite]

    if action == "import-gds":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LFile_ImportGDSII(",
            "        file,",
            f"        {_c_string(target_path)},",
            f"        {'LTRUE' if use_gds_datatype else 'LFALSE'},",
            f"        {overwrite_expr},",
            "        LTRUE,",
            "        0.0,",
            f"        {log_expr});",
        ]
    if action == "import-cif":
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    status = LFile_ImportCIF(",
            "        file,",
            f"        {_c_string(target_path)},",
            f"        {'LTRUE' if polygon_as_rect else 'LFALSE'},",
            f"        {overwrite_expr},",
            f"        {log_expr});",
        ]
    if action == "export-gds":
        if cell is not None and not cell:
            raise ValueError("export-gds requires a non-empty --cell when provided")
        return [
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    LGDSParamEx gdsParam = {0};",
            f"    gdsParam.cszDestFileName = {_c_string(target_path)};",
            "    gdsParam.bZipOutputFile = LFALSE;",
            f"    gdsParam.ExportScope = {'gdsExportSpecifiedCell' if cell else 'gdsExportActiveCell'};",
            f"    gdsParam.cszSpecifiedCell = {_c_string(cell) if cell else 'NULL'};",
            "    gdsParam.cpszIncludeLibraries = NULL;",
            f"    gdsParam.bIncludeHierarchy = {'LTRUE' if include_hierarchy else 'LFALSE'};",
            "    gdsParam.cpszExcludeLibraries = NULL;",
            "    gdsParam.bUseDefaultUnits = LTRUE;",
            "    gdsParam.dMicrons = 0.0;",
            "    gdsParam.dUserUnits = 0.0;",
            "    gdsParam.nUpcaseCellName = 0;",
            "    gdsParam.nCellNameLength = 32;",
            "    gdsParam.cszMapFileName = NULL;",
            f"    gdsParam.bDoNotExportHiddenObjects = {'LFALSE' if hidden_objects else 'LTRUE'};",
            "    gdsParam.bOverwriteGDSIIDataType = LFALSE;",
            "    gdsParam.bCalcChecksum = LFALSE;",
            "    gdsParam.bCheckSelfIntersections = LTRUE;",
            "    gdsParam.bFracture = LFALSE;",
            "    gdsParam.nFractureLimit = -1;",
            "    LGDSExportLogParams logParam = {0};",
            f"    logParam.szLogFileName = {log_expr};",
            "    logParam.bOpenLogInWindow = LFALSE;",
            f"    status = LFile_ExportGDSII(file, &gdsParam, {('&logParam' if log_path else 'NULL')});",
        ]
    raise ValueError(f"unsupported IO action: {action}")


def build_io_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    path: str | None = None,
    log_path: str | None = None,
    cell: str | None = None,
    include_hierarchy: bool = True,
    hidden_objects: bool = False,
    use_gds_datatype: bool = True,
    polygon_as_rect: bool = False,
    overwrite: str = "none",
) -> str:
    action = action.lower()
    overwrite = overwrite.lower()
    action_lines = _io_action_lines(
        action,
        path=path,
        log_path=log_path,
        cell=cell,
        include_hierarchy=include_hierarchy,
        hidden_objects=hidden_objects,
        use_gds_datatype=use_gds_datatype,
        polygon_as_rect=polygon_as_rect,
        overwrite=overwrite,
    )
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexIOAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            *action_lines,
            "    if (file && status == LStatusOK) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex IO Action", "CodexIOAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_io_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_io_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


def _grid_action_lines(
    action: str,
    *,
    value: float,
    x: float | None,
    y: float | None,
) -> list[str]:
    if action not in GRID_ACTIONS:
        raise ValueError(f"unsupported grid action: {action}")
    if value <= 0:
        raise ValueError("--value must be greater than zero")
    x_value = value if x is None else x
    y_value = value if y is None else y
    if x_value <= 0 or y_value <= 0:
        raise ValueError("--x and --y must be greater than zero")

    lines = [
        "    file = LFile_GetVisible();",
        "    if (!file) {",
        '        CodexWriteReceipt("missing_file", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
        "    status = LFile_GetGrid_v16_30(file, &grid);",
        "    if (status != LStatusOK) {",
        '        CodexWriteReceipt("get_grid_failed", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
    ]
    if action == "set-manufacturing-grid":
        lines.extend(
            [
                f"    grid.manufacturing_grid_size = {_coord_expr(value)};",
                "    grid.display_curves_using_manufacturing_grid = LTRUE;",
            ]
        )
    elif action == "set-display-grid":
        lines.append(f"    grid.displayed_grid_size = {_coord_expr(value)};")
    elif action == "set-snap-grid":
        lines.extend(
            [
                f"    grid.mouse_snap_grid_size_x = {_coord_expr(x_value)};",
                f"    grid.mouse_snap_grid_size_y = {_coord_expr(y_value)};",
            ]
        )
    elif action == "set-major-grid":
        lines.append(f"    grid.displayed_majorgrid_size = {_coord_expr(value)};")
    lines.append("    status = LFile_SetGrid_v16_30(file, &grid);")
    return lines


def build_grid_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    value: float,
    x: float | None = None,
    y: float | None = None,
) -> str:
    action = action.lower()
    action_lines = _grid_action_lines(action, value=value, x=x, y=y)
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexGridAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LGrid_v16_30 grid;",
            *action_lines,
            "    if (file && status == LStatusOK) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Grid Action", "CodexGridAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_grid_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_grid_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


def _drc_require_path(action: str, value: str | None, option: str = "--path") -> str:
    if not value:
        raise ValueError(f"{action} requires {option}")
    return str(Path(value).resolve())


def _rect_declaration(rect_name: str, *, x1: float | None, y1: float | None, x2: float | None, y2: float | None) -> list[str]:
    values = [x1, y1, x2, y2]
    if all(value is None for value in values):
        return [f"    LRect* {rect_name}Ptr = NULL;"]
    if any(value is None for value in values):
        raise ValueError("DRC area requires all of --x1 --y1 --x2 --y2")
    return [
        f"    LRect {rect_name} = LRect_Set({_coord_expr(float(x1))}, {_coord_expr(float(y1))}, {_coord_expr(float(x2))}, {_coord_expr(float(y2))});",
        f"    LRect* {rect_name}Ptr = &{rect_name};",
    ]


def _drc_action_lines(
    action: str,
    *,
    path: str | None,
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
) -> list[str]:
    if action not in DRC_ACTIONS:
        raise ValueError(f"unsupported DRC action: {action}")
    if tolerance < 0:
        raise ValueError("--tolerance must be zero or greater")
    lines = [
        "    file = LFile_GetVisible();",
        "    if (!file) {",
        '        CodexWriteReceipt("missing_file", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
        "    cell = LCell_GetVisible();",
        "    if (!cell) {",
        '        CodexWriteReceipt("missing_cell", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
    ]

    if action == "run":
        lines.extend(_rect_declaration("drcArea", x1=x1, y1=y1, x2=x2, y2=y2))
        lines.extend(
            [
                "    status = LCell_RunDRC(cell, drcAreaPtr, &numErrors);",
                "    if (status == LStatusOK) {",
                '        CodexWriteReceipt(numErrors == 0 ? "ok" : "drc_errors", (int)numErrors);',
                "    } else {",
                '        CodexWriteReceipt("status_error", (int)numErrors);',
                "    }",
                "    LUpi_SetQuietMode(quiet);",
                "    return;",
            ]
        )
        return lines
    if action == "run-command-file":
        command_path = _drc_require_path(action, path)
        lines.extend(_rect_declaration("drcArea", x1=x1, y1=y1, x2=x2, y2=y2))
        lines.extend(
            [
                f"    status = LCell_RunDRCCommandFile(cell, {_c_string(command_path)}, drcAreaPtr, &numErrors);",
                "    if (status == LStatusOK) {",
                '        CodexWriteReceipt(numErrors == 0 ? "ok" : "drc_errors", (int)numErrors);',
                "    } else {",
                '        CodexWriteReceipt("status_error", (int)numErrors);',
                "    }",
                "    LUpi_SetQuietMode(quiet);",
                "    return;",
            ]
        )
        return lines
    if action == "set-rule-set":
        if not rule_set:
            raise ValueError("set-rule-set requires --rule-set")
        lines.append(f"    status = LDrcRule_SetRuleSet(file, {_c_string(rule_set)});")
        return lines
    if action == "set-tolerance":
        lines.append(f"    status = LDrcRule_SetTolerance(file, {int(tolerance)});")
        return lines
    if action == "set-flags":
        lines.extend(
            [
                "    LDrcFlags flags;",
                f"    flags.bFlagAcuteAngles = {'LTRUE' if flag_acute else 'LFALSE'};",
                f"    flags.bFlagAllAngleEdges = {'LTRUE' if flag_all_angle else 'LFALSE'};",
                f"    flags.bFlagOffGridObjects = {'LTRUE' if flag_off_grid else 'LFALSE'};",
                "    status = LFile_SetDrcFlags(file, &flags);",
            ]
        )
        return lines
    if action == "open-summary":
        lines.extend(
            [
                "    window = LCell_OpenDRCSummary(cell);",
                "    if (!window) {",
                '        CodexWriteReceipt("open_summary_failed", 0);',
                "        LUpi_SetQuietMode(quiet);",
                "        return;",
                "    }",
                "    status = LStatusOK;",
            ]
        )
        return lines
    if action == "open-statistics":
        lines.extend(
            [
                "    window = LCell_OpenDRCStatistics(cell);",
                "    if (!window) {",
                '        CodexWriteReceipt("open_statistics_failed", 0);',
                "        LUpi_SetQuietMode(quiet);",
                "        return;",
                "    }",
                "    status = LStatusOK;",
            ]
        )
        return lines
    if action == "load-results":
        result_path = _drc_require_path(action, path)
        lines.append(
            f"    status = LCell_LoadResultsIntoDRCErrorNavigator(cell, {_c_string(result_path)}, {'LTRUE' if show_browser else 'LFALSE'});"
        )
        return lines
    if action == "clear-markers":
        lines.extend(
            [
                "    LCell_RemoveAllMarkers(cell);",
                "    LCell_RemoveGlobalMarkers(cell);",
                "    LCell_RefreshMarkers(cell);",
                "    status = LStatusOK;",
            ]
        )
        return lines
    if action == "show-global-markers":
        lines.extend(["    LMarker_SetShowGlobal(LTRUE);", "    status = LStatusOK;"])
        return lines
    if action == "hide-global-markers":
        lines.extend(["    LMarker_SetShowGlobal(LFALSE);", "    status = LStatusOK;"])
        return lines
    if action == "status":
        lines.extend(
            [
                "    numErrors = LCell_GetDRCNumErrors(cell);",
                "    drcStatus = LCell_GetDRCStatus(cell);",
                '    CodexWriteReceipt(drcStatus == LDrcStatus_Passed ? "passed" : (drcStatus == LDrcStatus_Failed ? "failed" : "needed"), (int)numErrors);',
                "    LUpi_SetQuietMode(quiet);",
                "    return;",
            ]
        )
        return lines
    raise ValueError(f"unsupported DRC action: {action}")


def build_drc_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    path: str | None = None,
    rule_set: str | None = None,
    tolerance: int = 0,
    flag_acute: bool = False,
    flag_all_angle: bool = False,
    flag_off_grid: bool = False,
    show_browser: bool = False,
    x1: float | None = None,
    y1: float | None = None,
    x2: float | None = None,
    y2: float | None = None,
) -> str:
    action = action.lower()
    action_lines = _drc_action_lines(
        action,
        path=path,
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
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexDRCAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LCell cell = NULL;",
            "    LWindow window = NULL;",
            "    unsigned int numErrors = 0;",
            "    LDrcStatus drcStatus = LDrcStatus_Needed;",
            *action_lines,
            "    if (file && status == LStatusOK) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", (int)numErrors);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex DRC Action", "CodexDRCAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_drc_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_drc_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


def _object_property_require_layer(action: str, value: str | None) -> str:
    if not value:
        raise ValueError(f"{action} requires --layer")
    if value.upper() == CURRENT_LAYER:
        raise ValueError(f"{action} requires a real layer name, not CURRENT")
    return value


def _object_property_loop_lines(
    action: str,
    *,
    gds_datatype: int,
    net_name: str | None,
    layer: str | None,
    grid: float,
) -> list[str]:
    if action not in OBJECT_PROPERTY_ACTIONS:
        raise ValueError(f"unsupported object-property action: {action}")
    if gds_datatype < -32768 or gds_datatype > 32767:
        raise ValueError("--gds-datatype must be between -32768 and 32767")
    if grid <= 0:
        raise ValueError("--grid must be greater than zero")
    if action == "set-net-name" and not net_name:
        raise ValueError("set-net-name requires --net-name")
    if action in {"change-layer", "copy-to-layer"}:
        layer = _object_property_require_layer(action, layer)

    setup_lines: list[str] = []
    post_loop_lines: list[str] = []
    status_lines: list[str]
    if action in {"change-layer", "copy-to-layer"}:
        setup_lines.extend(
            [
                f"    targetLayer = LLayer_Find(file, {_c_string(str(layer))});",
                "    if (!targetLayer) {",
                f"        status = LLayer_New(file, LLayer_GetList(file), {_c_string(str(layer))});",
                f"        targetLayer = LLayer_Find(file, {_c_string(str(layer))});",
                "    }",
                "    if (!targetLayer) {",
                '        CodexWriteReceipt("target_layer_create_failed", 0);',
                "        LUpi_SetQuietMode(quiet);",
                "        return;",
                "    }",
            ]
        )
    if action == "convert-to-polygon":
        setup_lines.append("    objectCount = 0;")
        post_loop_lines.extend(
            [
                "    if (objectCount == 0) {",
                '        CodexWriteReceipt("empty_selection", 0);',
                "        LUpi_SetQuietMode(quiet);",
                "        return;",
                "    }",
                "    status = LObject_ConvertToPolygon(cell, objects, objectCount);",
            ]
        )

    if action == "set-gds-datatype":
        status_lines = [f"        status = LObject_SetGDSIIDataTypeEx(object, {int(gds_datatype)});"]
    elif action == "set-net-name":
        status_lines = [f"        status = LObject_SetNetName(object, {_c_string(str(net_name))});"]
    elif action == "clear-net-name":
        status_lines = ['        status = LObject_SetNetName(object, "");']
    elif action == "change-layer":
        status_lines = ["        status = LObject_ChangeLayer(cell, object, targetLayer);"]
    elif action == "snap-to-grid":
        status_lines = [
            f"        if (!LObject_SnapToGrid(object, {_coord_expr(grid)})) {{",
            "            status = LBadParameters;",
            "        }",
        ]
    elif action == "snap-to-mfg-grid":
        status_lines = [
            "        if (!LObject_SnapToMfgGrid(object, file)) {",
            "            status = LBadParameters;",
            "        }",
        ]
    elif action == "copy-to-layer":
        status_lines = [
            "        if (!LObject_Copy(cell, targetLayer, object)) {",
            "            status = LCreateError;",
            "        }",
        ]
    elif action == "delete":
        status_lines = ["        status = LObject_Delete(cell, object);"]
    elif action == "convert-to-polygon":
        status_lines = [
            "        if (objectCount < 4096) {",
            "            objects[objectCount++] = object;",
            "            status = LStatusOK;",
            "        } else {",
            "            status = LBadParameters;",
            "        }",
        ]
    else:
        raise ValueError(f"unsupported object-property action: {action}")

    return [
        *setup_lines,
        "    for (selection = LSelection_GetList(); selection; selection = LSelection_GetNext(selection)) {",
        "        object = LSelection_GetObject(selection);",
        "        if (!object) {",
        "            continue;",
        "        }",
        *status_lines,
        "        if (status != LStatusOK) {",
        "            break;",
        "        }",
        "        changedCount++;",
        "    }",
        *post_loop_lines,
        "    if (changedCount == 0 && status == LStatusOK) {",
        '        CodexWriteReceipt("empty_selection", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
    ]


def build_object_property_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    gds_datatype: int = 0,
    net_name: str | None = None,
    layer: str | None = None,
    grid: float = 1.0,
) -> str:
    action = action.lower()
    action_lines = _object_property_loop_lines(
        action,
        gds_datatype=gds_datatype,
        net_name=net_name,
        layer=layer,
        grid=grid,
    )
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexObjectPropertyAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    LCell cell = LCell_GetVisible();",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    LSelection selection = NULL;",
            "    LObject object = NULL;",
            "    LLayer targetLayer = NULL;",
            "    unsigned int changedCount = 0;",
            "    unsigned int objectCount = 0;",
            "    LObject objects[4096];",
            *action_lines,
            "    if (file && status == LStatusOK) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", (int)changedCount);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Object Property Action", "CodexObjectPropertyAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_object_property_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_object_property_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


VIA_ACTIONS = {
    "add",
    "delete-all",
    "fill",
    "find",
    "find-by-layer",
    "count",
}


def _via_require_str(action: str, value: str | None, option: str) -> str:
    if not value:
        raise ValueError(f"{action} requires {option}")
    return value


def _via_action_lines(
    action: str,
    *,
    lower_layer: str | None,
    upper_layer: str | None,
    via_cell: str | None,
    via_def_name: str | None,
    pitch_x: float,
    pitch_y: float,
    x1: float | None,
    y1: float | None,
    x2: float | None,
    y2: float | None,
    fill_area: bool,
) -> list[str]:
    if action not in VIA_ACTIONS:
        raise ValueError(f"unsupported via action: {action}")

    lines = [
        "    file = LFile_GetVisible();",
        "    if (!file) {",
        '        CodexWriteReceipt("missing_file", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
        "    cell = LCell_GetVisible();",
        "    if (!cell) {",
        '        CodexWriteReceipt("missing_cell", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
    ]

    if action == "count":
        lines.extend([
            "    count = LFile_GetViaCount(file);",
            '    CodexWriteReceipt("ok", count);',
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "delete-all":
        lines.extend([
            "    status = LFile_DeleteAllVias(file);",
            "    if (status == LStatusOK) {",
            '        CodexWriteReceipt("ok", 0);',
            "    } else {",
            '        CodexWriteReceipt("status_error", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "add":
        ll = _via_require_str(action, lower_layer, "--lower-layer")
        ul = _via_require_str(action, upper_layer, "--upper-layer")
        vc = _via_require_str(action, via_cell, "--via-cell")
        lines.extend([
            f"    status = LFile_AddVia(file, {_c_string(ll)}, {_c_string(ul)}, {_c_string(vc)}, {_coord_expr(pitch_x)}, {_coord_expr(pitch_y)});",
            "    if (status == LStatusOK) {",
            '        CodexWriteReceipt("ok", 0);',
            "    } else {",
            '        CodexWriteReceipt("status_error", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "find":
        name = _via_require_str(action, via_def_name, "--via-def-name")
        lines.extend([
            f"    viaCell = LVia_Find(file, {_c_string(name)});",
            "    if (viaCell) {",
            '        CodexWriteReceipt("found", 1);',
            "    } else {",
            '        CodexWriteReceipt("not_found", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "find-by-layer":
        ll = _via_require_str(action, lower_layer, "--lower-layer")
        ul = _via_require_str(action, upper_layer, "--upper-layer")
        lines.extend([
            f"    viaCell = LVia_FindByLayer(file, {_c_string(ll)}, {_c_string(ul)});",
            "    if (viaCell) {",
            '        CodexWriteReceipt("found", 1);',
            "    } else {",
            '        CodexWriteReceipt("not_found", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "fill":
        name = _via_require_str(action, via_def_name, "--via-def-name")
        if any(v is None for v in [x1, y1, x2, y2]):
            raise ValueError("fill requires --x1 --y1 --x2 --y2")
        lines.extend([
            f"    viaCell = LVia_Find(file, {_c_string(name)});",
            "    if (!viaCell) {",
            '        CodexWriteReceipt("via_not_found", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    LRect area = LRect_Set({_coord_expr(float(x1))}, {_coord_expr(float(y1))}, {_coord_expr(float(x2))}, {_coord_expr(float(y2))});",
            f"    LVia_Fill(cell, viaCell, area, {'LTRUE' if fill_area else 'LFALSE'});",
            "    status = LStatusOK;",
        ])
        return lines

    raise ValueError(f"unsupported via action: {action}")


def build_via_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    lower_layer: str | None = None,
    upper_layer: str | None = None,
    via_cell: str | None = None,
    via_def_name: str | None = None,
    pitch_x: float = 1.0,
    pitch_y: float = 1.0,
    x1: float | None = None,
    y1: float | None = None,
    x2: float | None = None,
    y2: float | None = None,
    fill_area: bool = False,
) -> str:
    action = action.lower()
    action_lines = _via_action_lines(
        action,
        lower_layer=lower_layer,
        upper_layer=upper_layer,
        via_cell=via_cell,
        via_def_name=via_def_name,
        pitch_x=pitch_x,
        pitch_y=pitch_y,
        x1=x1, y1=y1, x2=x2, y2=y2,
        fill_area=fill_area,
    )
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexViaAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LCell cell = NULL;",
            "    LCell viaCell = NULL;",
            "    int count = 0;",
            *action_lines,
            "    if (file && status == LStatusOK) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Via Action", "CodexViaAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_via_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_via_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


BASEPOINT_ACTIONS = {
    "get-mode",
    "set-mode",
    "set",
    "get",
}


def _basepoint_action_lines(
    action: str,
    *,
    enabled: bool,
    x: float | None,
    y: float | None,
) -> list[str]:
    if action not in BASEPOINT_ACTIONS:
        raise ValueError(f"unsupported basepoint action: {action}")

    lines = []

    if action == "get-mode":
        lines.extend([
            "    {",
            "        LBoolean mode = LApp_GetBasePointMode();",
            '        CodexWriteReceipt(mode ? "basepoint_on" : "basepoint_off", mode ? 1 : 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "set-mode":
        lines.extend([
            f"    status = LApp_SetBasePointMode({'LTRUE' if enabled else 'LFALSE'});",
            "    if (status == LStatusOK) {",
            f'        CodexWriteReceipt("ok", {"1" if enabled else "0"});',
            "    } else {",
            '        CodexWriteReceipt("status_error", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "get":
        lines.extend([
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    cell = LCell_GetVisible();",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    {",
            "        LPoint bp = LCell_GetBasePoint(cell);",
            '        CodexWriteReceipt("ok", 1);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "set":
        if x is None or y is None:
            raise ValueError("set requires --x and --y")
        lines.extend([
            "    file = LFile_GetVisible();",
            "    if (!file) {",
            '        CodexWriteReceipt("missing_file", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    cell = LCell_GetVisible();",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            f"    status = LCell_SetBasePoint(cell, {_coord_expr(x)}, {_coord_expr(y)});",
            "    if (status == LStatusOK) {",
            '        CodexWriteReceipt("ok", 1);',
            "    } else {",
            '        CodexWriteReceipt("status_error", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    raise ValueError(f"unsupported basepoint action: {action}")


def build_basepoint_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    enabled: bool = True,
    x: float | None = None,
    y: float | None = None,
) -> str:
    action = action.lower()
    action_lines = _basepoint_action_lines(action, enabled=enabled, x=x, y=y)
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexBasepointAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LCell cell = NULL;",
            *action_lines,
            "    if (file && status == LStatusOK) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Basepoint Action", "CodexBasepointAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_basepoint_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_basepoint_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


LAYER_PARAMS_ACTIONS = {
    "get",
    "set",
    "set-cap",
    "set-rho",
    "set-fringe-cap",
}


def _layer_params_action_lines(
    action: str,
    *,
    layer: str | None,
    gds_number: int | None,
    gds_datatype: int | None,
    cif_name: str | None,
    cap: float | None,
    rho: float | None,
    fringe_cap: float | None,
    locked: bool | None,
    hidden: bool | None,
) -> list[str]:
    if action not in LAYER_PARAMS_ACTIONS:
        raise ValueError(f"unsupported layer-params action: {action}")
    if not layer:
        raise ValueError(f"{action} requires --layer")

    lines = [
        "    file = LFile_GetVisible();",
        "    if (!file) {",
        '        CodexWriteReceipt("missing_file", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
        f"    targetLayer = LLayer_Find(file, {_c_string(layer)});",
        "    if (!targetLayer) {",
        '        CodexWriteReceipt("layer_not_found", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
    ]

    if action == "get":
        lines.extend([
            "    status = LLayer_GetParametersEx1512(targetLayer, &params);",
            "    if (status == LStatusOK) {",
            '        CodexWriteReceipt("ok", 1);',
            "    } else {",
            '        CodexWriteReceipt("status_error", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action in ("set", "set-cap", "set-rho", "set-fringe-cap"):
        lines.extend([
            "    status = LLayer_GetParametersEx1512(targetLayer, &params);",
            "    if (status != LStatusOK) {",
            '        CodexWriteReceipt("get_params_failed", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
        ])
        if action == "set":
            if gds_number is not None:
                lines.append(f"    params.GDSNumber = {int(gds_number)};")
            if gds_datatype is not None:
                lines.append(f"    params.GDSDataType = {int(gds_datatype)};")
            if cif_name is not None:
                lines.append(f"    strncpy(params.CIFName, {_c_string(cif_name)}, sizeof(params.CIFName) - 1);")
                lines.append("    params.CIFName[sizeof(params.CIFName) - 1] = '\0';")
            if cap is not None:
                lines.append(f"    params.AreaCapacitance = {cap};")
            if fringe_cap is not None:
                lines.append(f"    params.FringeCapacitance = {fringe_cap};")
            if rho is not None:
                lines.append(f"    params.Resistivity = {rho};")
            if locked is not None:
                lines.append(f"    params.Locked = {'LTRUE' if locked else 'LFALSE'};")
            if hidden is not None:
                lines.append(f"    params.Hidden = {'LTRUE' if hidden else 'LFALSE'};")
            lines.append("    status = LLayer_SetParametersEx1512(targetLayer, &params);")
        elif action == "set-cap":
            if cap is None:
                raise ValueError("set-cap requires --cap")
            lines.append(f"    status = LLayer_SetCap(targetLayer, {cap});")
        elif action == "set-rho":
            if rho is None:
                raise ValueError("set-rho requires --rho")
            lines.append(f"    status = LLayer_SetRho(targetLayer, {rho});")
        elif action == "set-fringe-cap":
            if fringe_cap is None:
                raise ValueError("set-fringe-cap requires --fringe-cap")
            lines.append(f"    status = LLayer_SetFringeCap(targetLayer, {fringe_cap});")
        lines.extend([
            "    if (status == LStatusOK) {",
            '        CodexWriteReceipt("ok", 1);',
            "    } else {",
            '        CodexWriteReceipt("status_error", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    raise ValueError(f"unsupported layer-params action: {action}")


def build_layer_params_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    layer: str | None = None,
    gds_number: int | None = None,
    gds_datatype: int | None = None,
    cif_name: str | None = None,
    cap: float | None = None,
    rho: float | None = None,
    fringe_cap: float | None = None,
    locked: bool | None = None,
    hidden: bool | None = None,
) -> str:
    action = action.lower()
    action_lines = _layer_params_action_lines(
        action,
        layer=layer,
        gds_number=gds_number,
        gds_datatype=gds_datatype,
        cif_name=cif_name,
        cap=cap,
        rho=rho,
        fringe_cap=fringe_cap,
        locked=locked,
        hidden=hidden,
    )
    return "\n".join(
        [
            "#include <stdio.h>",
            "#include <string.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexLayerParamsAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LLayer targetLayer = NULL;",
            "    LLayerParamEx1512 params;",
            "    memset(&params, 0, sizeof(params));",
            *action_lines,
            "    if (file && status == LStatusOK) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Layer Params Action", "CodexLayerParamsAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_layer_params_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_layer_params_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


TECHNOLOGY_ACTIONS = {
    "get",
    "set-name",
    "set-unit-name",
    "set-unit",
    "set-lambda",
}


def _technology_action_lines(
    action: str,
    *,
    tech_name: str | None,
    unit_name: str | None,
    unit_num: int | None,
    unit_denom: int | None,
    lambda_num: int | None,
    lambda_denom: int | None,
) -> list[str]:
    if action not in TECHNOLOGY_ACTIONS:
        raise ValueError(f"unsupported technology action: {action}")

    lines = [
        "    file = LFile_GetVisible();",
        "    if (!file) {",
        '        CodexWriteReceipt("missing_file", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
    ]

    if action == "get":
        lines.extend([
            "    status = LFile_GetTechnologyEx840(file, &tech);",
            "    if (status == LStatusOK) {",
            '        CodexWriteReceipt("ok", 1);',
            "    } else {",
            '        CodexWriteReceipt("status_error", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "set-name":
        if not tech_name:
            raise ValueError("set-name requires --tech-name")
        lines.extend([
            f"    LFile_SetTechnologyName(file, {_c_string(tech_name)});",
            "    status = LStatusOK;",
        ])
        return lines

    if action == "set-unit-name":
        if not unit_name:
            raise ValueError("set-unit-name requires --unit-name")
        lines.extend([
            f"    status = LFile_SetTechnologyUnitName(file, {_c_string(unit_name)});",
        ])
        return lines

    if action == "set-unit":
        if unit_num is None or unit_denom is None:
            raise ValueError("set-unit requires --unit-num and --unit-denom")
        lines.extend([
            f"    status = LFile_SetTechnologyUnitNum(file, {int(unit_num)});",
            "    if (status == LStatusOK) {",
            f"        status = LFile_SetTechnologyUnitDenom(file, {int(unit_denom)});",
            "    }",
        ])
        return lines

    if action == "set-lambda":
        if lambda_num is None or lambda_denom is None:
            raise ValueError("set-lambda requires --lambda-num and --lambda-denom")
        lines.extend([
            f"    status = LFile_SetTechnologyLambdaNum(file, {int(lambda_num)});",
            "    if (status == LStatusOK) {",
            f"        status = LFile_SetTechnologyLambdaDenom(file, {int(lambda_denom)});",
            "    }",
        ])
        return lines

    raise ValueError(f"unsupported technology action: {action}")


def build_technology_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    tech_name: str | None = None,
    unit_name: str | None = None,
    unit_num: int | None = None,
    unit_denom: int | None = None,
    lambda_num: int | None = None,
    lambda_denom: int | None = None,
) -> str:
    action = action.lower()
    action_lines = _technology_action_lines(
        action,
        tech_name=tech_name,
        unit_name=unit_name,
        unit_num=unit_num,
        unit_denom=unit_denom,
        lambda_num=lambda_num,
        lambda_denom=lambda_denom,
    )
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexTechnologyAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LTechnologyEx840 tech;",
            *action_lines,
            "    if (file && status == LStatusOK) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Technology Action", "CodexTechnologyAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_technology_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_technology_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


CELL_INFO_ACTIONS = {
    "list",
    "get-name",
    "get-visible",
}


def _cell_info_action_lines(
    action: str,
) -> list[str]:
    if action not in CELL_INFO_ACTIONS:
        raise ValueError(f"unsupported cell-info action: {action}")

    lines = [
        "    file = LFile_GetVisible();",
        "    if (!file) {",
        '        CodexWriteReceipt("missing_file", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
    ]

    if action == "list":
        lines.extend([
            "    {",
            "        int count = 0;",
            "        LCell c = LCell_GetList(file);",
            "        while (c) {",
            "            count++;",
            "            c = LCell_GetNext(c);",
            "        }",
            '        CodexWriteReceipt("ok", count);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "get-name":
        lines.extend([
            "    cell = LCell_GetVisible();",
            "    if (!cell) {",
            '        CodexWriteReceipt("missing_cell", 0);',
            "        LUpi_SetQuietMode(quiet);",
            "        return;",
            "    }",
            "    {",
            "        char name[256];",
            "        LCell_GetName(cell, name, sizeof(name));",
            '        CodexWriteReceipt("ok", 1);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    if action == "get-visible":
        lines.extend([
            "    cell = LCell_GetVisible();",
            "    if (cell) {",
            '        CodexWriteReceipt("ok", 1);',
            "    } else {",
            '        CodexWriteReceipt("no_visible_cell", 0);',
            "    }",
            "    LUpi_SetQuietMode(quiet);",
            "    return;",
        ])
        return lines

    raise ValueError(f"unsupported cell-info action: {action}")


def build_cell_info_upi_macro(
    action: str,
    receipt_path: Path | None = None,
) -> str:
    action = action.lower()
    action_lines = _cell_info_action_lines(action)
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexCellInfoAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LFile file = NULL;",
            "    LCell cell = NULL;",
            *action_lines,
            "    LDisplay_Refresh();",
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Cell Info Action", "CodexCellInfoAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_cell_info_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_cell_info_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


NET_INFO_ACTIONS = {
    "list",
    "count",
}


def _net_info_action_lines(
    action: str,
) -> list[str]:
    if action not in NET_INFO_ACTIONS:
        raise ValueError(f"unsupported net-info action: {action}")

    lines = [
        "    file = LFile_GetVisible();",
        "    if (!file) {",
        '        CodexWriteReceipt("missing_file", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
        "    cell = LCell_GetVisible();",
        "    if (!cell) {",
        '        CodexWriteReceipt("missing_cell", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
    ]

    lines.extend([
        "    {",
        "        int count = 0;",
        "        LNet net = LCell_GetNetList(cell);",
        "        while (net) {",
        "            count++;",
        "            net = LNet_GetNext(net);",
        "        }",
        '        CodexWriteReceipt("ok", count);',
        "    }",
        "    LUpi_SetQuietMode(quiet);",
        "    return;",
    ])
    return lines


def build_net_info_upi_macro(
    action: str,
    receipt_path: Path | None = None,
) -> str:
    action = action.lower()
    action_lines = _net_info_action_lines(action)
    return "\n".join(
        [
            "#include <stdio.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexNetInfoAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LFile file = NULL;",
            "    LCell cell = NULL;",
            *action_lines,
            "    LDisplay_Refresh();",
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Net Info Action", "CodexNetInfoAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_net_info_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_net_info_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }


def build_upi_def(module_name: str = "codex_square_array") -> str:
    return "\n".join(
        [
            f"LIBRARY {module_name}",
            "EXPORTS",
            "    UPI_Entry_Point",
            "    CodexSquareArray",
            "",
        ]
    )


def write_upi_def(out_path: Path, module_name: str = "codex_square_array") -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_upi_def(module_name), encoding="utf-8")
    return {"ok": True, "def_file": str(out_path)}

def _extract_require_path(action: str, value: str | None, option: str = "--path") -> str:
    if not value:
        raise ValueError(f"{action} requires {option}")
    return str(Path(value).resolve())


def _extract_action_lines(
    action: str,
    *,
    def_file: str | None,
    spice_out: str | None,
    write_node_names: bool,
    write_node_capacitance: bool,
    write_parasitic_cap: bool,
) -> list[str]:
    if action not in EXTRACT_ACTIONS:
        raise ValueError(f"unsupported extract action: {action}")

    lines = [
        "    file = LFile_GetVisible();",
        "    if (!file) {",
        '        CodexWriteReceipt("missing_file", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
        "    cell = LCell_GetVisible();",
        "    if (!cell) {",
        '        CodexWriteReceipt("missing_cell", 0);',
        "        LUpi_SetQuietMode(quiet);",
        "        return;",
        "    }",
    ]

    if action == "run":
        resolved_def = _extract_require_path(action, def_file, "--def-file")
        resolved_spice = _extract_require_path(action, spice_out, "--spice-out")
        nn = "1" if write_node_names else "0"
        nc = "1" if write_node_capacitance else "0"
        lines.extend(
            [
                f"    status = LExtract_Run(cell, {_c_string(resolved_def)}, {_c_string(resolved_spice)}, {nn}, {nc});",
                "    if (status == LStatusOK) {",
                '        CodexWriteReceipt("ok", 0);',
                "    } else {",
                '        CodexWriteReceipt("status_error", 0);',
                "    }",
                "    LUpi_SetQuietMode(quiet);",
                "    return;",
            ]
        )
        return lines

    if action == "run-command-file":
        command_path = _extract_require_path(action, def_file, "--path")
        resolved_spice = _extract_require_path(action, spice_out, "--spice-out")
        lines.extend(
            [
                f"    status = LExtract_RunCommandFile(cell, {_c_string(command_path)}, {_c_string(resolved_spice)});",
                "    if (status == LStatusOK) {",
                '        CodexWriteReceipt("ok", 0);',
                "    } else {",
                '        CodexWriteReceipt("status_error", 0);',
                "    }",
                "    LUpi_SetQuietMode(quiet);",
                "    return;",
            ]
        )
        return lines

    if action == "run-hiper":
        lines.extend(
            [
                "    status = LExtract_RunHiPer(cell);",
                "    if (status == LStatusOK) {",
                '        CodexWriteReceipt("ok", 0);',
                "    } else {",
                '        CodexWriteReceipt("status_error", 0);',
                "    }",
                "    LUpi_SetQuietMode(quiet);",
                "    return;",
            ]
        )
        return lines

    if action == "set-options":
        resolved_def = str(Path(def_file).resolve()) if def_file else ""
        resolved_spice = str(Path(spice_out).resolve()) if spice_out else ""
        lines.extend(
            [
                "    status = LExtract_GetOptionsEx840(cell, &options);",
                "    if (status != LStatusOK) {",
                '        CodexWriteReceipt("get_options_failed", 0);',
                "        LUpi_SetQuietMode(quiet);",
                "        return;",
                "    }",
            ]
        )
        if resolved_def:
            lines.append(
                f"    strncpy(options.szExtDefnFile, {_c_string(resolved_def)}, sizeof(options.szExtDefnFile) - 1);"
            )
            lines.append("    options.szExtDefnFile[sizeof(options.szExtDefnFile) - 1] = '\\0';")
        if resolved_spice:
            lines.append(
                f"    strncpy(options.szExtOutFile, {_c_string(resolved_spice)}, sizeof(options.szExtOutFile) - 1);"
            )
            lines.append("    options.szExtOutFile[sizeof(options.szExtOutFile) - 1] = '\\0';")
        lines.append(f"    options.bWriteNodeNames = {'LTRUE' if write_node_names else 'LFALSE'};")
        lines.append(f"    options.bWriteParasiticCap = {'LTRUE' if write_parasitic_cap else 'LFALSE'};")
        lines.append("    status = LExtract_SetOptionsEx840(cell, &options);")
        return lines

    if action == "open-summary":
        lines.extend(
            [
                "    window = LCell_OpenExtractSummary(cell);",
                "    if (!window) {",
                '        CodexWriteReceipt("open_summary_failed", 0);',
                "        LUpi_SetQuietMode(quiet);",
                "        return;",
                "    }",
                "    status = LStatusOK;",
            ]
        )
        return lines

    if action == "open-statistics":
        lines.extend(
            [
                "    window = LCell_OpenExtractStatistics(cell);",
                "    if (!window) {",
                '        CodexWriteReceipt("open_statistics_failed", 0);',
                "        LUpi_SetQuietMode(quiet);",
                "        return;",
                "    }",
                "    status = LStatusOK;",
            ]
        )
        return lines

    raise ValueError(f"unsupported extract action: {action}")


def build_extract_upi_macro(
    action: str,
    receipt_path: Path | None = None,
    *,
    def_file: str | None = None,
    spice_out: str | None = None,
    write_node_names: bool = False,
    write_node_capacitance: bool = False,
    write_parasitic_cap: bool = False,
) -> str:
    action = action.lower()
    action_lines = _extract_action_lines(
        action,
        def_file=def_file,
        spice_out=spice_out,
        write_node_names=write_node_names,
        write_node_capacitance=write_node_capacitance,
        write_parasitic_cap=write_parasitic_cap,
    )
    return "\n".join(
        [
            "#include <stdio.h>",
            "#include <string.h>",
            '#include "ldata.h"',
            "",
            *_receipt_helper(receipt_path),
            "",
            'extern "C" void CodexExtractAction(void) {',
            '    CodexWriteReceipt("entered", 0);',
            "    int quiet = LUpi_InQuietMode();",
            "    LUpi_SetQuietMode(1);",
            "    LStatus status = LStatusOK;",
            "    LFile file = NULL;",
            "    LCell cell = NULL;",
            "    LWindow window = NULL;",
            "    LExtractOptionsEx840 options;",
            "    memset(&options, 0, sizeof(options));",
            *action_lines,
            "    if (file && status == LStatusOK) {",
            "        LFile_Save(file);",
            "    }",
            "    LDisplay_Refresh();",
            '    CodexWriteReceipt(status == LStatusOK ? "ok" : "status_error", 0);',
            "    LUpi_SetQuietMode(quiet);",
            "}",
            "",
            'extern "C" int UPI_Entry_Point(void) {',
            '    LMacro_Register("Codex Extract Action", "CodexExtractAction");',
            "    return 1;",
            "}",
            "",
        ]
    )


def write_extract_upi_macro(
    action: str,
    out_path: Path,
    receipt_path: Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if receipt_path is None:
        receipt_path = out_path.with_suffix(".receipt.txt")
    receipt_path = receipt_path.resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_extract_upi_macro(action, receipt_path, **kwargs), encoding="utf-8")
    return {
        "ok": True,
        "macro": str(out_path),
        "receipt_file": str(receipt_path),
        "action": action.lower(),
        "params": kwargs,
    }
