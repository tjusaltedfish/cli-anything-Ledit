from pathlib import Path
import tempfile
import unittest

from cli_anything.ledit.core.script_writer import (
    LayoutScriptSpec,
    LayerProbeSpec,
    SquareArraySpec,
    build_layout_script_tco,
    build_layer_probe_tco,
    build_run_command,
    build_square_array_tco,
    write_layout_script,
    write_layer_probe,
    write_square_array,
)
from cli_anything.ledit.core.macro_writer import (
    build_cell_upi_macro,
    build_drc_upi_macro,
    build_file_upi_macro,
    build_grid_upi_macro,
    build_io_upi_macro,
    build_layer_upi_macro,
    build_object_upi_macro,
    build_basepoint_upi_macro,
    build_cell_info_upi_macro,
    build_extract_upi_macro,
    build_layer_params_upi_macro,
    build_net_info_upi_macro,
    build_object_property_upi_macro,
    build_selection_upi_macro,
    build_square_array_upi_macro,
    build_technology_upi_macro,
    build_upi_smoke_macro,
    build_via_upi_macro,
    build_window_upi_macro,
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
from cli_anything.ledit.core.verify import verify_layout_script, verify_square_array_script


class SquareArrayWriterTest(unittest.TestCase):
    def test_generates_expected_box_commands(self):
        spec = SquareArraySpec(rows=2, cols=3, size=2, pitch_x=5, pitch_y=4, layer="Metal1")
        script = build_square_array_tco(spec)

        self.assertIn("cell TOP", script)
        self.assertIn("layer Metal1", script)
        self.assertEqual(script.count("box -!"), 6)
        self.assertIn("box -! 0 0 2 2", script)
        self.assertIn("box -! 10 4 12 6", script)
        self.assertTrue(script.endswith("save\n"))

    def test_current_layer_omits_layer_command(self):
        spec = SquareArraySpec(rows=1, cols=2, size=1, pitch_x=2, pitch_y=2, layer="CURRENT")
        script = build_square_array_tco(spec)

        self.assertIn("cell TOP", script)
        self.assertIn("Using current active L-Edit layer", script)
        self.assertNotIn("\nlayer ", script)
        self.assertEqual(script.count("box -!"), 2)

    def test_bounds_include_last_square(self):
        spec = SquareArraySpec(rows=3, cols=2, size=1.5, pitch_x=2, pitch_y=3, origin_x=10, origin_y=20)
        self.assertEqual(spec.bounds, (10, 20, 13.5, 27.5))

    def test_rejects_invalid_geometry(self):
        spec = SquareArraySpec(rows=0, cols=1, size=1, pitch_x=1, pitch_y=1)
        with self.assertRaises(ValueError):
            spec.validate()

    def test_verifies_generated_square_array_script(self):
        spec = SquareArraySpec(rows=3, cols=5, size=1.25, pitch_x=2.5, pitch_y=3, origin_x=10, origin_y=20)
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "array.tco"
            write_receipt = write_square_array(spec, out_path)

            receipt = verify_square_array_script(out_path, spec)
            self.assertTrue(Path(write_receipt["run_file"]).exists())
            self.assertEqual(
                Path(write_receipt["run_file"]).read_text(encoding="utf-8"),
                build_run_command(out_path.resolve()) + "\n",
            )
            self.assertTrue(Path(write_receipt["powershell_open_file"]).exists())
            open_script = Path(write_receipt["powershell_open_file"]).read_text(encoding="utf-8")
            self.assertIn("Set-Clipboard", open_script)
            self.assertIn("Important: do not run this line in PowerShell", open_script)

        self.assertTrue(receipt.ok, receipt.errors)
        self.assertEqual(receipt.box_count, 15)
        self.assertEqual(receipt.expected_box_count, 15)
        self.assertEqual(receipt.bounds, (10, 20, 21.25, 27.25))
        self.assertEqual(receipt.first_box, (10, 20, 11.25, 21.25))
        self.assertEqual(receipt.last_box, (20, 26, 21.25, 27.25))

    def test_verification_reports_mismatched_spec(self):
        actual = SquareArraySpec(rows=2, cols=2, size=1, pitch_x=2, pitch_y=2)
        expected = SquareArraySpec(rows=2, cols=3, size=1, pitch_x=2, pitch_y=2)
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "array.tco"
            write_square_array(actual, out_path)

            receipt = verify_square_array_script(out_path, expected)

        self.assertFalse(receipt.ok)
        self.assertIn("Expected 6 boxes but found 4.", receipt.errors)

    def test_layer_probe_generates_named_layer_script(self):
        spec = LayerProbeSpec(layer="Probe Metal", cell="TOP", origin_x=1, origin_y=2, marker_size=0.5)
        script = build_layer_probe_tco(spec)

        self.assertIn("cell TOP", script)
        self.assertIn('layer "Probe Metal"', script)
        self.assertIn("box -! 1 2 1.5 2.5", script)
        self.assertTrue(script.endswith("save\n"))

    def test_layer_probe_rejects_current_layer(self):
        spec = LayerProbeSpec(layer="CURRENT")

        with self.assertRaises(ValueError):
            spec.validate()

    def test_write_layer_probe_sidecars(self):
        spec = LayerProbeSpec(layer="Metal1")
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "probe.tco"
            receipt = write_layer_probe(spec, out_path)

            self.assertTrue(Path(receipt["script"]).exists())
            self.assertEqual(
                Path(receipt["run_file"]).read_text(encoding="utf-8"),
                build_run_command(out_path.resolve()) + "\n",
            )
            self.assertTrue(Path(receipt["powershell_open_file"]).exists())

    def test_layout_script_generates_mixed_commands(self):
        spec = LayoutScriptSpec(
            cell="TOP",
            layer="CURRENT",
            operations=[
                {"op": "comment", "text": "mixed geometry"},
                {"op": "box", "x1": 0, "y1": 0, "x2": 2, "y2": 1},
                {"op": "path", "points": [[0, 0], [3, 0], [3, 2]], "width": 0.4},
                {"op": "polygon", "points": [[5, 0], [7, 0], [6, 2]]},
                {"op": "text", "label": "IN 1", "x": 1, "y": 1},
                {"op": "square-array", "rows": 2, "cols": 2, "size": 0.5, "pitch": 1.0, "origin_x": 10, "origin_y": 20},
            ],
        )

        script = build_layout_script_tco(spec)

        self.assertIn("cell TOP", script)
        self.assertIn("// mixed geometry", script)
        self.assertIn("box -! 0 0 2 1", script)
        self.assertIn("path -! 0 0 3 0 3 2 -pw 0.4", script)
        self.assertIn("polygon -! 5 0 7 0 6 2", script)
        self.assertIn('text "IN 1" -! 1 1', script)
        self.assertEqual(script.count("box -!"), 5)
        self.assertTrue(script.endswith("save\n"))

    def test_layout_script_supports_per_operation_layer(self):
        spec = LayoutScriptSpec(
            cell="TOP",
            layer="CURRENT",
            operations=[
                {"op": "box", "x1": 0, "y1": 0, "x2": 1, "y2": 1, "layer": "Metal 1"},
                {"op": "text", "label": "NET_A", "x": 0.5, "y": 0.5, "layer": "Metal 1"},
            ],
        )

        script = build_layout_script_tco(spec)

        self.assertIn('box -! 0 0 1 1 -l "Metal 1"', script)
        self.assertIn('text NET_A -! 0.5 0.5 -l "Metal 1"', script)

    def test_layout_script_generates_basic_editing_commands(self):
        spec = LayoutScriptSpec(
            cell="TOP",
            layer="CURRENT",
            operations=[
                {"op": "width", "value": 0.7},
                {"op": "goto", "x": 10, "y": 20},
                {"op": "instance", "cell": "DFF R2", "x": 1, "y": 2, "file": "main lib.tdb"},
                {"op": "array", "cols": 3, "rows": 2, "pitch_x": 5, "pitch_y": -4},
                {"op": "copy"},
                {"op": "copy", "x": 12, "y": 13, "layer": "Metal1"},
                {"op": "move", "x": -2, "y": 3, "mode": "relative"},
                {"op": "move", "x": 4, "y": 5},
                {"op": "paste", "x": 6, "y": 7, "layer": "Metal1"},
                {"op": "rotate", "angle": 90, "x": 0, "y": 0},
                {"op": "saveas", "path": "C:\\tmp\\demo.tdb"},
            ],
        )

        script = build_layout_script_tco(spec)

        self.assertIn("width 0.7", script)
        self.assertIn("goto -! 10 20", script)
        self.assertIn('instance "DFF R2" -! 1 2 -f "main lib.tdb"', script)
        self.assertIn("array 3 2 5 -4", script)
        self.assertIn("\ncopy\n", script)
        self.assertIn("copy -! 12 13 -l Metal1", script)
        self.assertIn("move -2 3", script)
        self.assertIn("move -! 4 5", script)
        self.assertIn("paste -! 6 7 -l Metal1", script)
        self.assertIn("rotate 90 -! 0 0", script)
        self.assertIn('saveas "C:\\\\tmp\\\\demo.tdb"', script)

    def test_layout_script_rejects_bad_array_and_rotate(self):
        bad_array = LayoutScriptSpec(operations=[{"op": "array", "cols": 2, "rows": 1, "pitch_x": 0, "pitch_y": 1}])
        bad_rotate = LayoutScriptSpec(operations=[{"op": "rotate", "angle": 360, "x": 0, "y": 0}])

        with self.assertRaises(ValueError):
            build_layout_script_tco(bad_array)
        with self.assertRaises(ValueError):
            build_layout_script_tco(bad_rotate)

    def test_layout_script_rejects_nested_run(self):
        spec = LayoutScriptSpec(operations=[{"op": "raw", "command": "run other.tco"}])

        with self.assertRaises(ValueError):
            build_layout_script_tco(spec)

    def test_write_layout_script_sidecars(self):
        spec = LayoutScriptSpec(operations=[{"op": "box", "x1": 0, "y1": 0, "x2": 1, "y2": 1}])
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "layout.tco"
            receipt = write_layout_script(spec, out_path)

            self.assertTrue(Path(receipt["script"]).exists())
            self.assertEqual(
                Path(receipt["run_file"]).read_text(encoding="utf-8"),
                build_run_command(out_path.resolve()) + "\n",
            )
            self.assertTrue(Path(receipt["powershell_open_file"]).exists())

    def test_verify_layout_script_summarizes_commands(self):
        spec = LayoutScriptSpec(
            operations=[
                {"op": "box", "x1": 0, "y1": 0, "x2": 1, "y2": 1},
                {"op": "path", "points": [[0, 0], [1, 1]], "width": 0.1},
                {"op": "polygon", "points": [[2, 0], [3, 0], [2.5, 1]]},
                {"op": "text", "label": "A", "x": 0, "y": 0},
                {"op": "instance", "cell": "SUB", "x": 1, "y": 2},
                {"op": "raw", "command": "zoom in"},
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "layout.tco"
            write_layout_script(spec, out_path)

            receipt = verify_layout_script(out_path)

        self.assertTrue(receipt.ok, receipt.errors)
        self.assertEqual(receipt.counts["box"], 1)
        self.assertEqual(receipt.counts["path"], 1)
        self.assertEqual(receipt.counts["polygon"], 1)
        self.assertEqual(receipt.counts["text"], 1)
        self.assertEqual(receipt.counts["instance"], 1)
        self.assertEqual(receipt.counts["save"], 1)
        self.assertEqual(receipt.raw_count, 1)
        self.assertIn("unclassified raw command: zoom", receipt.warnings[0])

    def test_verify_layout_script_rejects_nested_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "bad.tco"
            out_path.write_text('cell TOP\nrun "C:/tmp/other.tco"\n', encoding="utf-8")

            receipt = verify_layout_script(out_path)

        self.assertFalse(receipt.ok)
        self.assertIn("Nested run command is not allowed", receipt.errors[0])

    def test_upi_macro_uses_current_layer_and_draws_boxes(self):
        spec = SquareArraySpec(rows=2, cols=2, size=1, pitch_x=2, pitch_y=3, layer="CURRENT")
        macro = build_square_array_upi_macro(spec)

        self.assertIn('extern "C" int UPI_Entry_Point(void)', macro)
        self.assertIn('CodexWriteReceipt("entered", 0)', macro)
        self.assertIn("LLayer_GetCurrent(file)", macro)
        self.assertIn('LMacro_Register("Codex Square Array", "CodexSquareArray")', macro)
        self.assertEqual(macro.count("LBox_New"), 4)
        self.assertIn("LFile_DispUtoIntU(file, 3)", macro)
        self.assertIn("LFile_Save(file)", macro)
        self.assertIn('CodexWriteReceipt("ok", 4)', macro)

    def test_upi_macro_uses_named_layer(self):
        spec = SquareArraySpec(rows=1, cols=1, size=1, pitch_x=2, pitch_y=2, layer="Metal1")
        macro = build_square_array_upi_macro(spec)

        self.assertIn('LLayer_Find(file, "Metal1")', macro)
        self.assertIn('LLayer_New(file, LLayer_GetList(file), "Metal1")', macro)
        self.assertNotIn("LLayer_GetCurrent(file)", macro)

    def test_write_upi_macro(self):
        spec = SquareArraySpec(rows=1, cols=2, size=1, pitch_x=2, pitch_y=2)
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "array_macro.cpp"
            receipt = write_square_array_upi_macro(spec, out_path)

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertIsNone(receipt["tdb_file"])
            self.assertEqual(receipt["box_count"], 2)
            self.assertIn("CodexSquareArray", out_path.read_text(encoding="utf-8"))

    def test_upi_macro_can_save_tdb_file(self):
        spec = SquareArraySpec(rows=1, cols=1, size=1, pitch_x=2, pitch_y=2)
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "array_macro.cpp"
            tdb_path = Path(tmp) / "array_output.tdb"
            receipt = write_square_array_upi_macro(spec, out_path, tdb_path=tdb_path)
            macro = out_path.read_text(encoding="utf-8")

            self.assertEqual(receipt["tdb_file"], str(tdb_path.resolve()))
            self.assertIn('LFile_New(NULL, "array_output")', macro)
            self.assertIn("LCell_New(file, \"TOP\")", macro)
            self.assertIn('LLayer_New(file, LLayer_GetList(file), "CodexLayer")', macro)
            self.assertIn("LFile_SaveAs(file", macro)

    def test_upi_smoke_macro_writes_receipt_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "smoke.cpp"
            receipt_path = Path(tmp) / "smoke.receipt.txt"
            macro = build_upi_smoke_macro(receipt_path)

            self.assertIn('extern "C" void CodexSmokeMacro(void)', macro)
            self.assertIn('LMacro_Register("Codex Smoke Macro", "CodexSmokeMacro")', macro)
            self.assertIn("CodexSmokeMacro();", macro)
            self.assertIn(str(receipt_path.resolve()).replace("\\", "\\\\"), macro)

            receipt = write_upi_smoke_macro(out_path, receipt_path)
            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(receipt_path.resolve()))

    def test_selection_upi_macro_generates_edit_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "selection.receipt.txt"
            move_macro = build_selection_upi_macro("move", receipt_path, dx=1.5, dy=-2.0)
            group_macro = build_selection_upi_macro("group", receipt_path, group_name="CLI Group")

            self.assertIn('extern "C" void CodexSelectionAction(void)', move_macro)
            self.assertIn("LSelection_Move", move_macro)
            self.assertIn("LFile_DispUtoIntU(file, 1.5)", move_macro)
            self.assertIn("LFile_DispUtoIntU(file, -2)", move_macro)
            self.assertIn('LMacro_Register("Codex Selection Action", "CodexSelectionAction")', move_macro)
            self.assertIn('LSelection_Group("CLI Group")', group_macro)

    def test_write_selection_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "selection.cpp"
            receipt = write_selection_upi_macro("flatten", out_path)

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["action"], "flatten")
            self.assertIn("LSelection_Flatten", out_path.read_text(encoding="utf-8"))

    def test_object_upi_macro_generates_circle_and_port(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "object.receipt.txt"
            circle_macro = build_object_upi_macro("circle", receipt_path, x=2.5, y=3.5, radius=1.25)
            port_macro = build_object_upi_macro(
                "port",
                receipt_path,
                layer="Metal1",
                label="IN A",
                x1=0,
                y1=1,
                x2=2,
                y2=3,
            )

            self.assertIn('extern "C" void CodexObjectAction(void)', circle_macro)
            self.assertIn("LLayer_GetCurrent(file)", circle_macro)
            self.assertIn("LPoint_Set", circle_macro)
            self.assertIn("LCircle_New", circle_macro)
            self.assertIn("LFile_DispUtoIntU(file, 1.25)", circle_macro)
            self.assertIn('LMacro_Register("Codex Object Action", "CodexObjectAction")', circle_macro)
            self.assertIn('LLayer_Find(file, "Metal1")', port_macro)
            self.assertIn('LLayer_New(file, LLayer_GetList(file), "Metal1")', port_macro)
            self.assertIn('LPort_New(cell, layer, "IN A"', port_macro)

    def test_write_object_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "object.cpp"
            receipt = write_object_upi_macro("circle", out_path, x=1, y=2, radius=3)

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["kind"], "circle")
            self.assertEqual(receipt["params"]["radius"], 3)
            self.assertIn("CodexObjectAction", out_path.read_text(encoding="utf-8"))

    def test_file_upi_macro_generates_file_cell_and_view_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "file.receipt.txt"
            tdb_path = Path(tmp) / "demo.tdb"
            new_macro = build_file_upi_macro("new", receipt_path, path=str(tdb_path), cell="TOP")
            open_cell_macro = build_file_upi_macro("open-cell", receipt_path, cell="SUB")
            move_origin_macro = build_file_upi_macro("move-origin", receipt_path, x=1.5, y=-2.0)
            clear_macro = build_file_upi_macro("clear-cell", receipt_path)

            self.assertIn('extern "C" void CodexFileAction(void)', new_macro)
            self.assertIn('LFile_New(NULL, "demo")', new_macro)
            self.assertIn("LFile_SaveAs(file", new_macro)
            self.assertIn(str(tdb_path.resolve().with_suffix("")).replace("\\", "\\\\"), new_macro)
            self.assertIn('LMacro_Register("Codex File Action", "CodexFileAction")', new_macro)
            self.assertIn('LFile_OpenCell(file, "SUB")', open_cell_macro)
            self.assertIn("LWindow_MakeVisible(window)", open_cell_macro)
            self.assertIn("LCell_MoveOrigin", move_origin_macro)
            self.assertIn("LFile_DispUtoIntU(file, 1.5)", move_origin_macro)
            self.assertIn("LFile_DispUtoIntU(file, -2)", move_origin_macro)
            self.assertIn("LCell_ClearContents(cell)", clear_macro)

    def test_write_file_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "file.cpp"
            receipt = write_file_upi_macro("home-view", out_path)

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["action"], "home-view")
            self.assertIn("LCell_HomeView", out_path.read_text(encoding="utf-8"))

    def test_layer_upi_macro_generates_layer_management_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "layer.receipt.txt"
            ensure_macro = build_layer_upi_macro("ensure", receipt_path, layer="Mask 1")
            rename_macro = build_layer_upi_macro("rename", receipt_path, layer="Mask 1", new_name="Mask 2")
            change_macro = build_layer_upi_macro(
                "change-selection-layer",
                receipt_path,
                source_layer="Mask 1",
                target_layer="Mask 2",
            )

            self.assertIn('extern "C" void CodexLayerAction(void)', ensure_macro)
            self.assertIn('LLayer_Find(file, "Mask 1")', ensure_macro)
            self.assertIn('LLayer_New(file, LLayer_GetList(file), "Mask 1")', ensure_macro)
            self.assertIn("LLayer_SetCurrent(file, layer)", ensure_macro)
            self.assertIn('LMacro_Register("Codex Layer Action", "CodexLayerAction")', ensure_macro)
            self.assertIn('LLayer_SetName(layer, "Mask 2")', rename_macro)
            self.assertIn('sourceLayer = LLayer_Find(file, "Mask 1")', change_macro)
            self.assertIn('targetLayer = LLayer_Find(file, "Mask 2")', change_macro)
            self.assertIn('LLayer_New(file, LLayer_GetList(file), "Mask 2")', change_macro)
            self.assertIn("LSelection_ChangeLayer(sourceLayer, targetLayer)", change_macro)

    def test_layer_upi_macro_rejects_missing_or_current_layer(self):
        with self.assertRaises(ValueError):
            build_layer_upi_macro("ensure")
        with self.assertRaises(ValueError):
            build_layer_upi_macro("set-current", layer="CURRENT")
        with self.assertRaises(ValueError):
            build_layer_upi_macro("rename", layer="Mask 1")

    def test_write_layer_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "layer.cpp"
            receipt = write_layer_upi_macro("set-current", out_path, layer="Mask 1")

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["action"], "set-current")
            self.assertIn("CodexLayerAction", out_path.read_text(encoding="utf-8"))

    def test_cell_upi_macro_generates_cell_management_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "cell.receipt.txt"
            ensure_macro = build_cell_upi_macro("ensure", receipt_path, cell="TOP")
            copy_macro = build_cell_upi_macro("copy", receipt_path, source_cell="TOP", target_cell="COPY_TOP")
            rename_macro = build_cell_upi_macro("rename", receipt_path, cell="TOP", new_name="MAIN")
            flatten_macro = build_cell_upi_macro("flatten", receipt_path, cell="TOP")

            self.assertIn('extern "C" void CodexCellAction(void)', ensure_macro)
            self.assertIn('LCell_Find(file, "TOP")', ensure_macro)
            self.assertIn('LCell_New(file, "TOP")', ensure_macro)
            self.assertIn("LCell_MakeVisible(cell)", ensure_macro)
            self.assertIn('LMacro_Register("Codex Cell Action", "CodexCellAction")', ensure_macro)
            self.assertIn('sourceCell = LCell_Find(file, "TOP")', copy_macro)
            self.assertIn('LCell_Copy(file, sourceCell, file, "COPY_TOP")', copy_macro)
            self.assertIn('LCell_SetName(file, cell, "MAIN")', rename_macro)
            self.assertIn("LCell_Flatten(cell)", flatten_macro)

    def test_cell_upi_macro_rejects_missing_names(self):
        with self.assertRaises(ValueError):
            build_cell_upi_macro("ensure")
        with self.assertRaises(ValueError):
            build_cell_upi_macro("rename", cell="TOP")
        with self.assertRaises(ValueError):
            build_cell_upi_macro("copy", source_cell="TOP")

    def test_write_cell_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "cell.cpp"
            receipt = write_cell_upi_macro("clear", out_path, cell="TOP")

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["action"], "clear")
            self.assertIn("LCell_ClearContents(cell)", out_path.read_text(encoding="utf-8"))

    def test_window_upi_macro_generates_window_and_view_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "window.receipt.txt"
            image_path = Path(tmp) / "visible.png"
            text_path = Path(tmp) / "notes.txt"
            home_macro = build_window_upi_macro("home-visible-cell", receipt_path)
            layout_macro = build_window_upi_macro("make-first-layout-visible", receipt_path)
            image_macro = build_window_upi_macro("save-visible-image", receipt_path, path=str(image_path))
            text_macro = build_window_upi_macro("new-text-window", receipt_path, text="hello")
            load_macro = build_window_upi_macro("load-text-window", receipt_path, path=str(text_path))

            self.assertIn('extern "C" void CodexWindowAction(void)', home_macro)
            self.assertIn("LCell_GetVisible()", home_macro)
            self.assertIn("LCell_HomeView(cell)", home_macro)
            self.assertIn("LWindow_GetList()", layout_macro)
            self.assertIn("LWindow_GetNext(window)", layout_macro)
            self.assertIn("LWindow_MakeVisible(window)", layout_macro)
            self.assertIn("LWindow_SaveImageToFile(window", image_macro)
            self.assertIn(str(image_path.resolve()).replace("\\", "\\\\"), image_macro)
            self.assertIn("LWindow_NewTextWindow(NULL, TEXT)", text_macro)
            self.assertIn('LWindow_SetText(window, "hello")', text_macro)
            self.assertIn("LWindow_LoadTextFile", load_macro)
            self.assertIn(str(text_path.resolve()).replace("\\", "\\\\"), load_macro)

    def test_window_upi_macro_rejects_missing_paths(self):
        with self.assertRaises(ValueError):
            build_window_upi_macro("save-visible-image")
        with self.assertRaises(ValueError):
            build_window_upi_macro("load-text-window")

    def test_write_window_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "window.cpp"
            receipt = write_window_upi_macro("close-visible-window", out_path)

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["action"], "close-visible-window")
            self.assertIn("LWindow_Close(window)", out_path.read_text(encoding="utf-8"))

    def test_io_upi_macro_generates_import_export_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "io.receipt.txt"
            gds_path = Path(tmp) / "layout.gds"
            cif_path = Path(tmp) / "layout.cif"
            log_path = Path(tmp) / "io.log"
            import_gds_macro = build_io_upi_macro(
                "import-gds",
                receipt_path,
                path=str(gds_path),
                log_path=str(log_path),
                overwrite="none",
            )
            import_cif_macro = build_io_upi_macro(
                "import-cif",
                receipt_path,
                path=str(cif_path),
                polygon_as_rect=True,
                overwrite="all",
            )
            export_macro = build_io_upi_macro(
                "export-gds",
                receipt_path,
                path=str(gds_path),
                cell="TOP",
                include_hierarchy=False,
                hidden_objects=True,
                log_path=str(log_path),
            )

            self.assertIn('extern "C" void CodexIOAction(void)', import_gds_macro)
            self.assertIn("LFile_ImportGDSII", import_gds_macro)
            self.assertIn(str(gds_path.resolve()).replace("\\", "\\\\"), import_gds_macro)
            self.assertIn("cDontOverwriteCells", import_gds_macro)
            self.assertIn("LFile_ImportCIF", import_cif_macro)
            self.assertIn("LTRUE,", import_cif_macro)
            self.assertIn("cOverwriteAllCells", import_cif_macro)
            self.assertIn("LGDSParamEx gdsParam = {0};", export_macro)
            self.assertIn("LFile_ExportGDSII(file, &gdsParam, &logParam)", export_macro)
            self.assertIn("gdsParam.ExportScope = gdsExportSpecifiedCell", export_macro)
            self.assertIn('gdsParam.cszSpecifiedCell = "TOP"', export_macro)
            self.assertIn("gdsParam.bIncludeHierarchy = LFALSE", export_macro)
            self.assertIn("gdsParam.bDoNotExportHiddenObjects = LFALSE", export_macro)

    def test_io_upi_macro_rejects_missing_path(self):
        with self.assertRaises(ValueError):
            build_io_upi_macro("import-gds")
        with self.assertRaises(ValueError):
            build_io_upi_macro("export-gds", overwrite="bogus", path="out.gds")

    def test_write_io_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "io.cpp"
            gds_path = Path(tmp) / "layout.gds"
            receipt = write_io_upi_macro("export-gds", out_path, path=str(gds_path))

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["action"], "export-gds")
            self.assertIn("CodexIOAction", out_path.read_text(encoding="utf-8"))

    def test_grid_upi_macro_generates_grid_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "grid.receipt.txt"
            manufacturing_macro = build_grid_upi_macro("set-manufacturing-grid", receipt_path, value=0.1)
            display_macro = build_grid_upi_macro("set-display-grid", receipt_path, value=1.0)
            snap_macro = build_grid_upi_macro("set-snap-grid", receipt_path, value=0.5, x=0.25, y=0.75)
            major_macro = build_grid_upi_macro("set-major-grid", receipt_path, value=10)

            self.assertIn('extern "C" void CodexGridAction(void)', manufacturing_macro)
            self.assertIn("LFile_GetGrid_v16_30(file, &grid)", manufacturing_macro)
            self.assertIn("grid.manufacturing_grid_size = LFile_DispUtoIntU(file, 0.1)", manufacturing_macro)
            self.assertIn("grid.display_curves_using_manufacturing_grid = LTRUE", manufacturing_macro)
            self.assertIn("grid.displayed_grid_size = LFile_DispUtoIntU(file, 1)", display_macro)
            self.assertIn("grid.mouse_snap_grid_size_x = LFile_DispUtoIntU(file, 0.25)", snap_macro)
            self.assertIn("grid.mouse_snap_grid_size_y = LFile_DispUtoIntU(file, 0.75)", snap_macro)
            self.assertIn("grid.displayed_majorgrid_size = LFile_DispUtoIntU(file, 10)", major_macro)
            self.assertIn("LFile_SetGrid_v16_30(file, &grid)", major_macro)

    def test_grid_upi_macro_rejects_non_positive_values(self):
        with self.assertRaises(ValueError):
            build_grid_upi_macro("set-display-grid", value=0)
        with self.assertRaises(ValueError):
            build_grid_upi_macro("set-snap-grid", value=1, x=-1)

    def test_write_grid_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "grid.cpp"
            receipt = write_grid_upi_macro("set-major-grid", out_path, value=5)

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["action"], "set-major-grid")
            self.assertIn("CodexGridAction", out_path.read_text(encoding="utf-8"))

    def test_drc_upi_macro_generates_drc_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "drc.receipt.txt"
            rule_path = Path(tmp) / "rules.cal"
            result_path = Path(tmp) / "results.db"
            run_macro = build_drc_upi_macro("run", receipt_path, x1=0, y1=0, x2=10, y2=20)
            command_macro = build_drc_upi_macro("run-command-file", receipt_path, path=str(rule_path))
            flags_macro = build_drc_upi_macro(
                "set-flags",
                receipt_path,
                flag_acute=True,
                flag_all_angle=True,
                flag_off_grid=True,
            )
            status_macro = build_drc_upi_macro("status", receipt_path)
            load_macro = build_drc_upi_macro("load-results", receipt_path, path=str(result_path), show_browser=True)
            clear_macro = build_drc_upi_macro("clear-markers", receipt_path)

            self.assertIn('extern "C" void CodexDRCAction(void)', run_macro)
            self.assertIn("LRect drcArea = LRect_Set", run_macro)
            self.assertIn("LCell_RunDRC(cell, drcAreaPtr, &numErrors)", run_macro)
            self.assertIn("LCell_RunDRCCommandFile", command_macro)
            self.assertIn(str(rule_path.resolve()).replace("\\", "\\\\"), command_macro)
            self.assertIn("flags.bFlagAcuteAngles = LTRUE", flags_macro)
            self.assertIn("flags.bFlagAllAngleEdges = LTRUE", flags_macro)
            self.assertIn("flags.bFlagOffGridObjects = LTRUE", flags_macro)
            self.assertIn("LFile_SetDrcFlags(file, &flags)", flags_macro)
            self.assertIn("LCell_GetDRCNumErrors(cell)", status_macro)
            self.assertIn("LCell_GetDRCStatus(cell)", status_macro)
            self.assertIn("LCell_LoadResultsIntoDRCErrorNavigator", load_macro)
            self.assertIn(str(result_path.resolve()).replace("\\", "\\\\"), load_macro)
            self.assertIn("LCell_RemoveAllMarkers(cell)", clear_macro)
            self.assertIn("LCell_RemoveGlobalMarkers(cell)", clear_macro)

    def test_drc_upi_macro_rejects_missing_inputs(self):
        with self.assertRaises(ValueError):
            build_drc_upi_macro("run-command-file")
        with self.assertRaises(ValueError):
            build_drc_upi_macro("set-rule-set")
        with self.assertRaises(ValueError):
            build_drc_upi_macro("run", x1=0, y1=0)
        with self.assertRaises(ValueError):
            build_drc_upi_macro("set-tolerance", tolerance=-1)

    def test_write_drc_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "drc.cpp"
            receipt = write_drc_upi_macro("open-summary", out_path)

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["action"], "open-summary")
            self.assertIn("CodexDRCAction", out_path.read_text(encoding="utf-8"))

    def test_object_property_upi_macro_generates_selection_object_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "object_property.receipt.txt"
            gds_macro = build_object_property_upi_macro("set-gds-datatype", receipt_path, gds_datatype=12)
            net_macro = build_object_property_upi_macro("set-net-name", receipt_path, net_name="NET_A")
            layer_macro = build_object_property_upi_macro("change-layer", receipt_path, layer="Mask2")
            snap_macro = build_object_property_upi_macro("snap-to-grid", receipt_path, grid=0.25)
            copy_macro = build_object_property_upi_macro("copy-to-layer", receipt_path, layer="CopyLayer")
            convert_macro = build_object_property_upi_macro("convert-to-polygon", receipt_path)

            self.assertIn('extern "C" void CodexObjectPropertyAction(void)', gds_macro)
            self.assertIn("LSelection_GetList()", gds_macro)
            self.assertIn("LSelection_GetObject(selection)", gds_macro)
            self.assertIn("LObject_SetGDSIIDataTypeEx(object, 12)", gds_macro)
            self.assertIn('LObject_SetNetName(object, "NET_A")', net_macro)
            self.assertIn('LLayer_Find(file, "Mask2")', layer_macro)
            self.assertIn("LObject_ChangeLayer(cell, object, targetLayer)", layer_macro)
            self.assertIn("LObject_SnapToGrid(object, LFile_DispUtoIntU(file, 0.25))", snap_macro)
            self.assertIn('LLayer_Find(file, "CopyLayer")', copy_macro)
            self.assertIn("LObject_Copy(cell, targetLayer, object)", copy_macro)
            self.assertIn("LObject_ConvertToPolygon(cell, objects, objectCount)", convert_macro)

    def test_object_property_upi_macro_rejects_missing_inputs(self):
        with self.assertRaises(ValueError):
            build_object_property_upi_macro("set-net-name")
        with self.assertRaises(ValueError):
            build_object_property_upi_macro("change-layer")
        with self.assertRaises(ValueError):
            build_object_property_upi_macro("copy-to-layer", layer="CURRENT")
        with self.assertRaises(ValueError):
            build_object_property_upi_macro("set-gds-datatype", gds_datatype=40000)
        with self.assertRaises(ValueError):
            build_object_property_upi_macro("snap-to-grid", grid=0)

    def test_write_object_property_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "object_property.cpp"
            receipt = write_object_property_upi_macro("clear-net-name", out_path)

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["action"], "clear-net-name")
            self.assertIn("CodexObjectPropertyAction", out_path.read_text(encoding="utf-8"))



    def test_extract_upi_macro_generates_extract_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "extract.receipt.txt"
            def_path = Path(tmp) / "extract.def"
            spice_path = Path(tmp) / "out.sp"
            run_macro = build_extract_upi_macro("run", receipt_path, def_file=str(def_path), spice_out=str(spice_path), write_node_names=True)
            cmd_macro = build_extract_upi_macro("run-command-file", receipt_path, def_file=str(Path(tmp) / "lvs.cal"), spice_out=str(spice_path))
            hiper_macro = build_extract_upi_macro("run-hiper", receipt_path)
            opts_macro = build_extract_upi_macro("set-options", receipt_path, def_file=str(def_path), spice_out=str(spice_path), write_node_names=True, write_parasitic_cap=True)
            summary_macro = build_extract_upi_macro("open-summary", receipt_path)
            stats_macro = build_extract_upi_macro("open-statistics", receipt_path)

            self.assertIn('extern "C" void CodexExtractAction(void)', run_macro)
            self.assertIn("LExtract_Run(cell,", run_macro)
            self.assertIn(", 1, 0)", run_macro)
            self.assertIn("LExtract_RunCommandFile", cmd_macro)
            self.assertIn(str((Path(tmp) / "lvs.cal").resolve()).replace("\\", "\\\\"), cmd_macro)
            self.assertIn("LExtract_RunHiPer(cell)", hiper_macro)
            self.assertIn("LExtract_GetOptionsEx840(cell, &options)", opts_macro)
            self.assertIn("LExtract_SetOptionsEx840(cell, &options)", opts_macro)
            self.assertIn("options.bWriteNodeNames = LTRUE", opts_macro)
            self.assertIn("options.bWriteParasiticCap = LTRUE", opts_macro)
            self.assertIn("LCell_OpenExtractSummary(cell)", summary_macro)
            self.assertIn("LCell_OpenExtractStatistics(cell)", stats_macro)

    def test_extract_upi_macro_rejects_missing_inputs(self):
        with self.assertRaises(ValueError):
            build_extract_upi_macro("run")
        with self.assertRaises(ValueError):
            build_extract_upi_macro("run", def_file="x.def")
        with self.assertRaises(ValueError):
            build_extract_upi_macro("run-command-file")
        with self.assertRaises(ValueError):
            build_extract_upi_macro("run-command-file", def_file="lvs.cal")

    def test_write_extract_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "extract.cpp"
            receipt = write_extract_upi_macro("open-summary", out_path)

            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertEqual(receipt["action"], "open-summary")
            self.assertIn("CodexExtractAction", out_path.read_text(encoding="utf-8"))

    def test_via_upi_macro_generates_via_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "via.receipt.txt"
            add_macro = build_via_upi_macro("add", receipt_path, lower_layer="Metal1", upper_layer="Metal2", via_cell="VIA1", pitch_x=0.5, pitch_y=0.5)
            count_macro = build_via_upi_macro("count", receipt_path)
            find_macro = build_via_upi_macro("find", receipt_path, via_def_name="VIA1")
            find_bl_macro = build_via_upi_macro("find-by-layer", receipt_path, lower_layer="Metal1", upper_layer="Metal2")
            del_macro = build_via_upi_macro("delete-all", receipt_path)

            self.assertIn('extern "C" void CodexViaAction(void)', add_macro)
            self.assertIn("LFile_AddVia(file,", add_macro)
            self.assertIn("LFile_GetViaCount(file)", count_macro)
            self.assertIn("LVia_Find(file,", find_macro)
            self.assertIn("LVia_FindByLayer(file,", find_bl_macro)
            self.assertIn("LFile_DeleteAllVias(file)", del_macro)

    def test_via_upi_macro_rejects_missing_inputs(self):
        with self.assertRaises(ValueError):
            build_via_upi_macro("add")
        with self.assertRaises(ValueError):
            build_via_upi_macro("add", lower_layer="Metal1")
        with self.assertRaises(ValueError):
            build_via_upi_macro("find")

    def test_write_via_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "via.cpp"
            receipt = write_via_upi_macro("count", out_path)
            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["action"], "count")
            self.assertIn("CodexViaAction", out_path.read_text(encoding="utf-8"))

    def test_basepoint_upi_macro_generates_basepoint_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "bp.receipt.txt"
            get_mode_macro = build_basepoint_upi_macro("get-mode", receipt_path)
            set_mode_macro = build_basepoint_upi_macro("set-mode", receipt_path, enabled=True)
            set_macro = build_basepoint_upi_macro("set", receipt_path, x=1.5, y=2.5)
            get_macro = build_basepoint_upi_macro("get", receipt_path)

            self.assertIn('extern "C" void CodexBasepointAction(void)', get_mode_macro)
            self.assertIn("LApp_GetBasePointMode()", get_mode_macro)
            self.assertIn("LApp_SetBasePointMode(LTRUE)", set_mode_macro)
            self.assertIn("LCell_SetBasePoint(cell,", set_macro)
            self.assertIn("LCell_GetBasePoint(cell)", get_macro)

    def test_basepoint_upi_macro_rejects_missing_xy(self):
        with self.assertRaises(ValueError):
            build_basepoint_upi_macro("set")
        with self.assertRaises(ValueError):
            build_basepoint_upi_macro("set", x=1.0)

    def test_write_basepoint_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "bp.cpp"
            receipt = write_basepoint_upi_macro("get-mode", out_path)
            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["action"], "get-mode")
            self.assertIn("CodexBasepointAction", out_path.read_text(encoding="utf-8"))

    def test_layer_params_upi_macro_generates_param_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "lp.receipt.txt"
            get_macro = build_layer_params_upi_macro("get", receipt_path, layer="Metal1")
            set_macro = build_layer_params_upi_macro("set", receipt_path, layer="Metal1", gds_number=10, gds_datatype=0, cap=1.5)
            cap_macro = build_layer_params_upi_macro("set-cap", receipt_path, layer="Metal1", cap=2.0)
            rho_macro = build_layer_params_upi_macro("set-rho", receipt_path, layer="Metal1", rho=0.05)

            self.assertIn('extern "C" void CodexLayerParamsAction(void)', get_macro)
            self.assertIn("LLayer_GetParametersEx1512(targetLayer, &params)", get_macro)
            self.assertIn("LLayer_SetParametersEx1512(targetLayer, &params)", set_macro)
            self.assertIn("params.GDSNumber = 10", set_macro)
            self.assertIn("params.AreaCapacitance = 1.5", set_macro)
            self.assertIn("LLayer_SetCap(targetLayer, 2.0)", cap_macro)
            self.assertIn("LLayer_SetRho(targetLayer, 0.05)", rho_macro)

    def test_layer_params_upi_macro_rejects_missing_inputs(self):
        with self.assertRaises(ValueError):
            build_layer_params_upi_macro("get")
        with self.assertRaises(ValueError):
            build_layer_params_upi_macro("set-cap", layer="Metal1")

    def test_write_layer_params_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "lp.cpp"
            receipt = write_layer_params_upi_macro("get", out_path, layer="Metal1")
            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["action"], "get")
            self.assertIn("CodexLayerParamsAction", out_path.read_text(encoding="utf-8"))


    def test_technology_upi_macro_generates_technology_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "tech.receipt.txt"
            get_macro = build_technology_upi_macro("get", receipt_path)
            name_macro = build_technology_upi_macro("set-name", receipt_path, tech_name="MyTech")
            unit_macro = build_technology_upi_macro("set-unit", receipt_path, unit_num=1, unit_denom=1000)
            lambda_macro = build_technology_upi_macro("set-lambda", receipt_path, lambda_num=1, lambda_denom=2)

            self.assertIn('extern "C" void CodexTechnologyAction(void)', get_macro)
            self.assertIn("LFile_GetTechnologyEx840(file, &tech)", get_macro)
            self.assertIn('LFile_SetTechnologyName(file, "MyTech")', name_macro)
            self.assertIn("LFile_SetTechnologyUnitNum(file, 1)", unit_macro)
            self.assertIn("LFile_SetTechnologyUnitDenom(file, 1000)", unit_macro)
            self.assertIn("LFile_SetTechnologyLambdaNum(file, 1)", lambda_macro)
            self.assertIn("LFile_SetTechnologyLambdaDenom(file, 2)", lambda_macro)

    def test_technology_upi_macro_rejects_missing_inputs(self):
        with self.assertRaises(ValueError):
            build_technology_upi_macro("set-name")
        with self.assertRaises(ValueError):
            build_technology_upi_macro("set-unit", unit_num=1)

    def test_write_technology_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "tech.cpp"
            receipt = write_technology_upi_macro("get", out_path)
            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["action"], "get")
            self.assertIn("CodexTechnologyAction", out_path.read_text(encoding="utf-8"))

    def test_cell_info_upi_macro_generates_cell_info_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "cellinfo.receipt.txt"
            list_macro = build_cell_info_upi_macro("list", receipt_path)
            name_macro = build_cell_info_upi_macro("get-name", receipt_path)
            visible_macro = build_cell_info_upi_macro("get-visible", receipt_path)

            self.assertIn('extern "C" void CodexCellInfoAction(void)', list_macro)
            self.assertIn("LCell_GetList(file)", list_macro)
            self.assertIn("LCell_GetNext(c)", list_macro)
            self.assertIn("LCell_GetName(cell, name, sizeof(name))", name_macro)
            self.assertIn("LCell_GetVisible()", visible_macro)

    def test_write_cell_info_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "cellinfo.cpp"
            receipt = write_cell_info_upi_macro("list", out_path)
            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["action"], "list")
            self.assertIn("CodexCellInfoAction", out_path.read_text(encoding="utf-8"))


    def test_object_upi_macro_generates_torus(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "torus.cpp"
            macro = build_object_upi_macro("torus", Path(tmp) / "receipt.txt", x=5.0, y=5.0, inner_radius=1.0, outer_radius=2.0, start_angle=0.0, stop_angle=270.0)
            self.assertIn("LTorus_CreateNew(cell, layer, &torusParams)", macro)
            self.assertIn("torusParams.nInnerRadius = LFile_DispUtoIntU(file, 1)", macro)
            self.assertIn("torusParams.nOuterRadius = LFile_DispUtoIntU(file, 2)", macro)

    def test_object_upi_macro_generates_pie(self):
        with tempfile.TemporaryDirectory() as tmp:
            macro = build_object_upi_macro("pie", Path(tmp) / "receipt.txt", x=3.0, y=4.0, radius=2.5, start_angle=45.0, stop_angle=180.0)
            self.assertIn("LPie_CreateNew(cell, layer, &pieParams)", macro)
            self.assertIn("pieParams.nRadius = LFile_DispUtoIntU(file, 2.5)", macro)

    def test_net_info_upi_macro_generates_net_info_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = Path(tmp) / "netinfo.receipt.txt"
            list_macro = build_net_info_upi_macro("list", receipt_path)
            count_macro = build_net_info_upi_macro("count", receipt_path)

            self.assertIn('extern "C" void CodexNetInfoAction(void)', list_macro)
            self.assertIn("LCell_GetNetList(cell)", list_macro)
            self.assertIn("LNet_GetNext(net)", list_macro)

    def test_write_net_info_upi_macro(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "netinfo.cpp"
            receipt = write_net_info_upi_macro("list", out_path)
            self.assertTrue(Path(receipt["macro"]).exists())
            self.assertEqual(receipt["action"], "list")
            self.assertIn("CodexNetInfoAction", out_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
