import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from cli_anything.ledit.core.script_writer import build_run_command
from cli_anything.ledit.ledit_cli import main


class LEditCliE2ETest(unittest.TestCase):
    def test_square_array_json_writes_script_and_preview(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "array.tco"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "square-array",
                    "--rows",
                    "3",
                    "--cols",
                    "4",
                    "--size",
                    "2",
                    "--pitch",
                    "5",
                    "--layer",
                    "Metal1",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["box_count"], 12)
            self.assertTrue(out_path.exists())
            self.assertTrue(out_path.with_suffix(".svg").exists())
            self.assertTrue(out_path.with_suffix(".run.txt").exists())
            self.assertTrue(out_path.with_suffix(".open.ps1").exists())
            self.assertEqual(receipt["run_file"], str(out_path.with_suffix(".run.txt").resolve()))
            self.assertEqual(receipt["powershell_open_file"], str(out_path.with_suffix(".open.ps1").resolve()))
            self.assertEqual(
                out_path.with_suffix(".run.txt").read_text(encoding="utf-8"),
                build_run_command(out_path.resolve()) + "\n",
            )
            self.assertEqual(out_path.read_text(encoding="utf-8").count("box -!"), 12)

            verify_result = runner.invoke(
                main,
                [
                    "--json",
                    "verify-script",
                    str(out_path),
                    "--rows",
                    "3",
                    "--cols",
                    "4",
                    "--size",
                    "2",
                    "--pitch",
                    "5",
                    "--layer",
                    "Metal1",
                ],
            )

            self.assertEqual(verify_result.exit_code, 0, verify_result.output)
            verify_receipt = json.loads(verify_result.output)
            self.assertTrue(verify_receipt["ok"], verify_receipt["errors"])
            self.assertEqual(verify_receipt["box_count"], 12)
            self.assertEqual(verify_receipt["bounds"], [0.0, 0.0, 17.0, 12.0])

    def test_draw_square_array_generates_and_verifies_in_one_command(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "draw_array.tco"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "draw-square-array",
                    "--rows",
                    "4",
                    "--cols",
                    "6",
                    "--size",
                    "1.1",
                    "--pitch-x",
                    "2.2",
                    "--pitch-y",
                    "2.6",
                    "--origin-x",
                    "3",
                    "--origin-y",
                    "4",
                    "--layer",
                    "Metal1",
                    "--cell",
                    "TOP",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertTrue(receipt["verified"])
            self.assertEqual(receipt["box_count"], 24)
            self.assertEqual(receipt["bounds"], [3.0, 4.0, 15.1, 12.9])
            self.assertEqual(receipt["verify"]["first_box"], [3.0, 4.0, 4.1, 5.1])
            self.assertEqual(receipt["verify"]["last_box"], [14.0, 11.8, 15.1, 12.9])
            self.assertEqual(receipt["run_command"], build_run_command(out_path.resolve()))
            self.assertEqual(receipt["run_file"], str(out_path.with_suffix(".run.txt").resolve()))
            self.assertEqual(receipt["powershell_open_file"], str(out_path.with_suffix(".open.ps1").resolve()))
            self.assertTrue(out_path.exists())
            self.assertTrue(out_path.with_suffix(".svg").exists())
            self.assertTrue(out_path.with_suffix(".run.txt").exists())
            self.assertTrue(out_path.with_suffix(".open.ps1").exists())

    def test_layer_probe_json_writes_probe_script(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "probe_metal1.tco"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "layer-probe",
                    "--layer",
                    "Metal1",
                    "--cell",
                    "TOP",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["run_command"], build_run_command(out_path.resolve()))
            self.assertTrue(out_path.exists())
            self.assertTrue(out_path.with_suffix(".run.txt").exists())
            self.assertTrue(out_path.with_suffix(".open.ps1").exists())
            script = out_path.read_text(encoding="utf-8")
            self.assertIn("layer Metal1", script)
            self.assertIn("box -! 0 0 0.2 0.2", script)

    def test_layer_probe_rejects_current(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "layer-probe", "--layer", "CURRENT"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires a real layer name", receipt["error"])

    def test_layout_script_json_writes_mixed_script(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = Path(tmp) / "layout.json"
            out_path = Path(tmp) / "mixed.tco"
            spec_path.write_text(
                json.dumps(
                    {
                        "title": "mixed test",
                        "cell": "TOP",
                        "layer": "CURRENT",
                        "operations": [
                            {"op": "box", "x1": 0, "y1": 0, "x2": 2, "y2": 1},
                            {"op": "path", "points": [[0, 0], [2, 2]], "width": 0.2},
                            {"op": "polygon", "points": [[4, 0], [5, 0], [4.5, 1]]},
                            {"op": "text", "label": "OUT", "x": 1, "y": 1},
                            {"op": "instance", "cell": "SUBCELL", "x": 10, "y": 20},
                            {"op": "rotate", "angle": 45, "x": 0, "y": 0},
                            {"op": "saveas", "path": "C:\\tmp\\mixed_output.tdb"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = runner.invoke(main, ["--json", "layout-script", str(spec_path), "--out", str(out_path)])

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["script"], str(out_path.resolve()))
            self.assertTrue(receipt["verified"], receipt["verify"]["errors"])
            self.assertEqual(receipt["verify"]["counts"]["box"], 1)
            self.assertEqual(receipt["verify"]["counts"]["path"], 1)
            self.assertEqual(receipt["verify"]["counts"]["polygon"], 1)
            self.assertEqual(receipt["verify"]["counts"]["text"], 1)
            self.assertEqual(receipt["verify"]["counts"]["instance"], 1)
            self.assertEqual(receipt["verify"]["counts"]["rotate"], 1)
            self.assertEqual(receipt["verify"]["counts"]["saveas"], 1)
            self.assertFalse(receipt["sent_run_command"])
            script = out_path.read_text(encoding="utf-8")
            self.assertIn("box -! 0 0 2 1", script)
            self.assertIn("path -! 0 0 2 2 -pw 0.2", script)
            self.assertIn("polygon -! 4 0 5 0 4.5 1", script)
            self.assertIn("text OUT -! 1 1", script)
            self.assertIn("instance SUBCELL -! 10 20", script)
            self.assertIn("rotate 45 -! 0 0", script)
            self.assertIn('saveas "C:\\\\tmp\\\\mixed_output.tdb"', script)
            self.assertTrue(out_path.with_suffix(".run.txt").exists())
            self.assertTrue(out_path.with_suffix(".open.ps1").exists())

            verify_result = runner.invoke(main, ["--json", "verify-layout-script", str(out_path)])

            self.assertEqual(verify_result.exit_code, 0, verify_result.output)
            verify_receipt = json.loads(verify_result.output)
            self.assertTrue(verify_receipt["ok"], verify_receipt["errors"])
            self.assertEqual(verify_receipt["counts"]["box"], 1)
            self.assertEqual(verify_receipt["counts"]["save"], 1)

    def test_direct_geometry_commands_write_verified_scripts(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cases = [
                (
                    ["box", "--x1", "1", "--y1", "2", "--x2", "3", "--y2", "4", "--out", str(tmp_path / "box.tco")],
                    "box",
                    "box -! 1 2 3 4",
                ),
                (
                    [
                        "path",
                        "--point",
                        "0",
                        "0",
                        "--point",
                        "1",
                        "1",
                        "--width",
                        "0.2",
                        "--out",
                        str(tmp_path / "path.tco"),
                    ],
                    "path",
                    "path -! 0 0 1 1 -pw 0.2",
                ),
                (
                    [
                        "polygon",
                        "--point",
                        "0",
                        "0",
                        "--point",
                        "2",
                        "0",
                        "--point",
                        "1",
                        "1",
                        "--out",
                        str(tmp_path / "polygon.tco"),
                    ],
                    "polygon",
                    "polygon -! 0 0 2 0 1 1",
                ),
                (
                    ["text", "--label", "NET A", "--x", "5", "--y", "6", "--out", str(tmp_path / "text.tco")],
                    "text",
                    'text "NET A" -! 5 6',
                ),
                (
                    ["instance", "--cell-name", "SUB CELL", "--x", "7", "--y", "8", "--out", str(tmp_path / "instance.tco")],
                    "instance",
                    'instance "SUB CELL" -! 7 8',
                ),
            ]

            for args, command_name, expected_line in cases:
                with self.subTest(command=command_name):
                    result = runner.invoke(main, ["--json", *args])

                    self.assertEqual(result.exit_code, 0, result.output)
                    receipt = json.loads(result.output)
                    self.assertTrue(receipt["ok"], receipt.get("error"))
                    self.assertTrue(receipt["verified"], receipt["verify"]["errors"])
                    self.assertEqual(receipt["verify"]["counts"][command_name], 1)
                    self.assertEqual(receipt["verify"]["counts"]["save"], 1)
                    script = Path(receipt["script"]).read_text(encoding="utf-8")
                    self.assertIn(expected_line, script)

    def test_direct_editing_commands_write_verified_scripts(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cases = [
                (["width", "--value", "0.35", "--out", str(tmp_path / "width.tco")], "width", "width 0.35"),
                (["goto", "--x", "10", "--y", "20", "--out", str(tmp_path / "goto.tco")], "goto", "goto -! 10 20"),
                (
                    [
                        "array",
                        "--cols",
                        "3",
                        "--rows",
                        "2",
                        "--pitch-x",
                        "5",
                        "--pitch-y",
                        "-4",
                        "--out",
                        str(tmp_path / "array.tco"),
                    ],
                    "array",
                    "array 3 2 5 -4",
                ),
                (["copy", "--x", "1", "--y", "2", "--out", str(tmp_path / "copy.tco")], "copy", "copy -! 1 2"),
                (["move", "--x", "-2", "--y", "3", "--mode", "relative", "--out", str(tmp_path / "move.tco")], "move", "move -2 3"),
                (["paste", "--x", "4", "--y", "5", "--out", str(tmp_path / "paste.tco")], "paste", "paste -! 4 5"),
                (["rotate", "--angle", "90", "--x", "0", "--y", "0", "--out", str(tmp_path / "rotate.tco")], "rotate", "rotate 90 -! 0 0"),
                (
                    ["saveas", "--path", r"C:\tmp\direct_save.tdb", "--out", str(tmp_path / "saveas.tco")],
                    "saveas",
                    'saveas "C:\\\\tmp\\\\direct_save.tdb"',
                ),
            ]

            for args, command_name, expected_line in cases:
                with self.subTest(command=command_name):
                    result = runner.invoke(main, ["--json", *args])

                    self.assertEqual(result.exit_code, 0, result.output)
                    receipt = json.loads(result.output)
                    self.assertTrue(receipt["ok"], receipt.get("error"))
                    self.assertTrue(receipt["verified"], receipt["verify"]["errors"])
                    self.assertEqual(receipt["verify"]["counts"][command_name], 1)
                    script = Path(receipt["script"]).read_text(encoding="utf-8")
                    self.assertIn(expected_line, script)

    def test_copy_rejects_partial_position(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "copy", "--x", "1"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("--x and --y", receipt["error"])

    def test_macro_square_array_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "array_macro.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-square-array",
                    "--rows",
                    "2",
                    "--cols",
                    "3",
                    "--size",
                    "1",
                    "--pitch",
                    "2",
                    "--layer",
                    "CURRENT",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["box_count"], 6)
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("LLayer_GetCurrent(file)", macro)
            self.assertEqual(macro.count("LBox_New"), 6)

    def test_macro_selection_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "selection.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-selection-action",
                    "--action",
                    "move",
                    "--dx",
                    "1.25",
                    "--dy",
                    "-0.5",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "move")
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexSelectionAction", macro)
            self.assertIn("LSelection_Move", macro)
            self.assertIn("LFile_DispUtoIntU(file, 1.25)", macro)
            self.assertIn("LFile_DispUtoIntU(file, -0.5)", macro)

    def test_macro_object_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            circle_path = Path(tmp) / "circle.cpp"
            circle_result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-object-action",
                    "--kind",
                    "circle",
                    "--x",
                    "1.5",
                    "--y",
                    "2.5",
                    "--radius",
                    "0.75",
                    "--out",
                    str(circle_path),
                ],
            )

            self.assertEqual(circle_result.exit_code, 0, circle_result.output)
            circle_receipt = json.loads(circle_result.output)
            self.assertTrue(circle_receipt["ok"], circle_receipt.get("error"))
            self.assertEqual(circle_receipt["macro"], str(circle_path.resolve()))
            self.assertEqual(circle_receipt["kind"], "circle")
            self.assertIsNone(circle_receipt["execute_command"])
            self.assertIsNone(circle_receipt["compile"])
            circle_macro = circle_path.read_text(encoding="utf-8")
            self.assertIn("CodexObjectAction", circle_macro)
            self.assertIn("LCircle_New", circle_macro)
            self.assertIn("LFile_DispUtoIntU(file, 0.75)", circle_macro)

            port_path = Path(tmp) / "port.cpp"
            port_result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-object-action",
                    "--kind",
                    "port",
                    "--label",
                    "IN",
                    "--x1",
                    "0",
                    "--y1",
                    "0",
                    "--x2",
                    "2",
                    "--y2",
                    "1",
                    "--layer",
                    "Metal1",
                    "--out",
                    str(port_path),
                ],
            )

            self.assertEqual(port_result.exit_code, 0, port_result.output)
            port_receipt = json.loads(port_result.output)
            self.assertTrue(port_receipt["ok"], port_receipt.get("error"))
            self.assertEqual(port_receipt["kind"], "port")
            port_macro = port_path.read_text(encoding="utf-8")
            self.assertIn('LPort_New(cell, layer, "IN"', port_macro)
            self.assertIn('LLayer_Find(file, "Metal1")', port_macro)

    def test_macro_file_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "file.cpp"
            tdb_path = Path(tmp) / "new_layout.tdb"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-file-action",
                    "--action",
                    "new",
                    "--path",
                    str(tdb_path),
                    "--cell",
                    "TOP",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "new")
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexFileAction", macro)
            self.assertIn('LFile_New(NULL, "new_layout")', macro)
            self.assertIn("LFile_SaveAs(file", macro)

            home_path = Path(tmp) / "home.cpp"
            home_result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-file-action",
                    "--action",
                    "home-view",
                    "--out",
                    str(home_path),
                ],
            )

            self.assertEqual(home_result.exit_code, 0, home_result.output)
            home_receipt = json.loads(home_result.output)
            self.assertTrue(home_receipt["ok"], home_receipt.get("error"))
            home_macro = home_path.read_text(encoding="utf-8")
            self.assertIn("LCell_HomeView", home_macro)

    def test_macro_file_action_requires_path_for_new(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-file-action", "--action", "new"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --path", receipt["error"])

    def test_macro_layer_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "layer.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-layer-action",
                    "--action",
                    "ensure",
                    "--layer",
                    "Mask1",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "ensure")
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexLayerAction", macro)
            self.assertIn('LLayer_Find(file, "Mask1")', macro)
            self.assertIn('LLayer_New(file, LLayer_GetList(file), "Mask1")', macro)

            change_path = Path(tmp) / "change.cpp"
            change_result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-layer-action",
                    "--action",
                    "change-selection-layer",
                    "--source-layer",
                    "Mask1",
                    "--target-layer",
                    "Mask2",
                    "--out",
                    str(change_path),
                ],
            )

            self.assertEqual(change_result.exit_code, 0, change_result.output)
            change_receipt = json.loads(change_result.output)
            self.assertTrue(change_receipt["ok"], change_receipt.get("error"))
            change_macro = change_path.read_text(encoding="utf-8")
            self.assertIn("LSelection_ChangeLayer(sourceLayer, targetLayer)", change_macro)

    def test_macro_layer_action_requires_real_layer_name(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-layer-action", "--action", "ensure"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --layer", receipt["error"])

    def test_macro_cell_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "cell.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-cell-action",
                    "--action",
                    "ensure",
                    "--cell",
                    "TOP",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "ensure")
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexCellAction", macro)
            self.assertIn('LCell_Find(file, "TOP")', macro)
            self.assertIn('LCell_New(file, "TOP")', macro)

            copy_path = Path(tmp) / "copy_cell.cpp"
            copy_result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-cell-action",
                    "--action",
                    "copy",
                    "--source-cell",
                    "TOP",
                    "--target-cell",
                    "TOP_COPY",
                    "--out",
                    str(copy_path),
                ],
            )

            self.assertEqual(copy_result.exit_code, 0, copy_result.output)
            copy_receipt = json.loads(copy_result.output)
            self.assertTrue(copy_receipt["ok"], copy_receipt.get("error"))
            copy_macro = copy_path.read_text(encoding="utf-8")
            self.assertIn('LCell_Copy(file, sourceCell, file, "TOP_COPY")', copy_macro)

    def test_macro_cell_action_requires_cell_name(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-cell-action", "--action", "ensure"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --cell", receipt["error"])

    def test_macro_window_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "window.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-window-action",
                    "--action",
                    "home-visible-cell",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "home-visible-cell")
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexWindowAction", macro)
            self.assertIn("LCell_GetVisible()", macro)
            self.assertIn("LCell_HomeView(cell)", macro)

            image_path = Path(tmp) / "visible.png"
            image_macro_path = Path(tmp) / "save_image.cpp"
            image_result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-window-action",
                    "--action",
                    "save-visible-image",
                    "--path",
                    str(image_path),
                    "--out",
                    str(image_macro_path),
                ],
            )

            self.assertEqual(image_result.exit_code, 0, image_result.output)
            image_receipt = json.loads(image_result.output)
            self.assertTrue(image_receipt["ok"], image_receipt.get("error"))
            image_macro = image_macro_path.read_text(encoding="utf-8")
            self.assertIn("LWindow_SaveImageToFile(window", image_macro)
            self.assertIn(str(image_path.resolve()).replace("\\", "\\\\"), image_macro)

    def test_macro_window_action_requires_path_for_file_actions(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-window-action", "--action", "save-visible-image"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --path", receipt["error"])

    def test_macro_object_property_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "object_property.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-object-property-action",
                    "--action",
                    "set-net-name",
                    "--net-name",
                    "NET_A",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "set-net-name")
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexObjectPropertyAction", macro)
            self.assertIn("LSelection_GetList()", macro)
            self.assertIn('LObject_SetNetName(object, "NET_A")', macro)

    def test_macro_object_property_action_requires_net_name(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-object-property-action", "--action", "set-net-name"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --net-name", receipt["error"])

    def test_macro_io_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "io.cpp"
            gds_path = Path(tmp) / "layout.gds"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-io-action",
                    "--action",
                    "export-gds",
                    "--path",
                    str(gds_path),
                    "--cell",
                    "TOP",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "export-gds")
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexIOAction", macro)
            self.assertIn("LFile_ExportGDSII", macro)
            self.assertIn('gdsParam.cszSpecifiedCell = "TOP"', macro)

    def test_macro_io_action_requires_path(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-io-action", "--action", "import-gds"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --path", receipt["error"])

    def test_macro_grid_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "grid.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-grid-action",
                    "--action",
                    "set-snap-grid",
                    "--value",
                    "1",
                    "--x",
                    "0.25",
                    "--y",
                    "0.5",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "set-snap-grid")
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexGridAction", macro)
            self.assertIn("LFile_GetGrid_v16_30(file, &grid)", macro)
            self.assertIn("grid.mouse_snap_grid_size_x = LFile_DispUtoIntU(file, 0.25)", macro)

    def test_macro_grid_action_rejects_non_positive_value(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-grid-action", "--action", "set-display-grid", "--value", "0"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("greater than zero", receipt["error"])

    def test_macro_drc_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "drc.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-drc-action",
                    "--action",
                    "run",
                    "--x1",
                    "0",
                    "--y1",
                    "0",
                    "--x2",
                    "10",
                    "--y2",
                    "20",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "run")
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexDRCAction", macro)
            self.assertIn("LCell_RunDRC(cell, drcAreaPtr, &numErrors)", macro)

    def test_macro_drc_action_requires_command_file_path(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-drc-action", "--action", "run-command-file"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --path", receipt["error"])

    def test_macro_smoke_writes_minimal_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "smoke.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-smoke",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["receipt_file"], str(out_path.with_suffix(".receipt.txt").resolve()))
            self.assertIsNone(receipt["execute_command"])
            self.assertIsNone(receipt["compile"])
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexSmokeMacro", macro)
            self.assertNotIn("LBox_New", macro)

    def test_macro_smoke_interpreted_does_not_compile_without_execute(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "smoke.cpp"
            result = runner.invoke(main, ["--json", "macro-smoke", "--interpreted", "--out", str(out_path)])

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertIsNone(receipt["compile"])
            self.assertTrue(out_path.exists())
            self.assertFalse(out_path.with_suffix(".upi").exists())

    def test_run_script_reports_missing_script(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "run-script", r"C:\tmp\missing_ledit_script.tco"])

        self.assertNotEqual(result.exit_code, 0)

    @unittest.skipIf(shutil.which("powershell") is None, "PowerShell is not on PATH")
    def test_run_script_reports_no_visible_ledit_window(self):
        visible_check = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-Process -Name ledit64 -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Measure-Object).Count",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(visible_check.returncode, 0, visible_check.stderr + visible_check.stdout)
        if int(visible_check.stdout.strip() or "0") > 0:
            self.skipTest("A visible L-Edit window is present; not sending keys during tests")

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "array.tco"
            out_path.write_text("// empty test script\n", encoding="utf-8")
            result = runner.invoke(main, ["--json", "run-script", str(out_path)])

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertFalse(receipt["ok"])
            self.assertFalse(receipt["sent"])
            self.assertEqual(receipt["run_command"], build_run_command(out_path.resolve()))
            self.assertIn("No visible L-Edit window", receipt["error"])

    def test_inspect_reports_ledit_path(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "inspect"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertTrue(receipt["ok"])
        self.assertIn("ledit64.exe", receipt["ledit_exe"])
        self.assertGreaterEqual(len(receipt["ledit_candidates"]), 2)
        self.assertTrue(any(candidate["exists"] for candidate in receipt["ledit_candidates"]))
        self.assertIn("processes", receipt)
        self.assertIn("process_count", receipt)
        self.assertIn("visible_window_count", receipt)
        self.assertIn("can_send_run_command", receipt)
        self.assertIsInstance(receipt["processes"], list)

    def test_upi_preflight_reports_launch_plan_and_process_boundary(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            macro_path = Path(tmp) / "smoke.upi"
            macro_path.write_text("placeholder", encoding="utf-8")

            result = runner.invoke(main, ["--json", "upi-preflight", "--macro", str(macro_path)])

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertIn("ready", receipt)
            self.assertEqual(receipt["macro"], str(macro_path.resolve()))
            self.assertTrue(receipt["macro_exists"])
            self.assertIn("process_count", receipt)
            self.assertIn("blockers", receipt)
            self.assertIn("warnings", receipt)
            self.assertIn("launch_plan", receipt)
            self.assertIn("-U", receipt["launch_plan"]["args"])
            if receipt["process_count"] > 0:
                self.assertFalse(receipt["ready"])
                self.assertTrue(any("Existing L-Edit process" in blocker for blocker in receipt["blockers"]))

            allowed_result = runner.invoke(
                main,
                ["--json", "upi-preflight", "--macro", str(macro_path), "--allow-existing-process"],
            )

            self.assertEqual(allowed_result.exit_code, 0, allowed_result.output)
            allowed_receipt = json.loads(allowed_result.output)
            self.assertTrue(allowed_receipt["macro_exists"])
            self.assertFalse(any("Existing L-Edit process" in blocker for blocker in allowed_receipt["blockers"]))
            if allowed_receipt["process_count"] > 0:
                self.assertTrue(any("single-instance" in warning for warning in allowed_receipt["warnings"]))

    def test_capabilities_reports_layered_coverage(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "capabilities"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertTrue(receipt["ok"])
        layer_names = [layer["name"] for layer in receipt["layers"]]
        self.assertIn("command-window-script", layer_names)
        self.assertIn("upi-macro", layer_names)
        self.assertIn("interactive-window-sendkeys", layer_names)
        self.assertIn("window-ui", layer_names)
        command_layer = next(layer for layer in receipt["layers"] if layer["name"] == "command-window-script")
        self.assertIn("box", command_layer["commands"])
        self.assertIn("array", command_layer["commands"])
        self.assertNotIn("array-selected", command_layer["commands"])
        self.assertIn("rotate", command_layer["commands"])
        self.assertIn("layout-script", command_layer["entrypoints"])
        self.assertIn("box", command_layer["entrypoints"])
        self.assertIn("rotate", command_layer["entrypoints"])
        upi_layer = next(layer for layer in receipt["layers"] if layer["name"] == "upi-macro")
        self.assertIn("macro-selection-action", upi_layer["commands"])
        self.assertIn("macro-object-action", upi_layer["commands"])
        self.assertIn("macro-object-property-action", upi_layer["commands"])
        self.assertIn("macro-file-action", upi_layer["commands"])
        self.assertIn("macro-layer-action", upi_layer["commands"])
        self.assertIn("macro-cell-action", upi_layer["commands"])
        self.assertIn("macro-window-action", upi_layer["commands"])
        self.assertIn("macro-io-action", upi_layer["commands"])
        self.assertIn("macro-grid-action", upi_layer["commands"])
        self.assertIn("macro-drc-action", upi_layer["commands"])
        self.assertIn("upi-preflight", upi_layer["commands"])
        sendkeys_layer = next(layer for layer in receipt["layers"] if layer["name"] == "interactive-window-sendkeys")
        self.assertIn("foreground control", sendkeys_layer["notes"])

    def test_module_subprocess_writes_script_and_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "subprocess_array.tco"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cli_anything.ledit",
                    "--json",
                    "square-array",
                    "--rows",
                    "2",
                    "--cols",
                    "3",
                    "--size",
                    "1",
                    "--pitch",
                    "2",
                    "--layer",
                    "Metal1",
                    "--out",
                    str(out_path),
                ],
                cwd=Path(__file__).resolve().parents[4],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            receipt = json.loads(result.stdout)
            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["box_count"], 6)
            self.assertEqual(Path(receipt["script"]), out_path.resolve())
            self.assertTrue(out_path.exists())
            self.assertTrue(out_path.with_suffix(".svg").exists())
            self.assertTrue(out_path.with_suffix(".run.txt").exists())
            self.assertTrue(out_path.with_suffix(".open.ps1").exists())

    @unittest.skipIf(shutil.which("cli-anything-ledit") is None, "installed cli-anything-ledit command is not on PATH")
    def test_installed_command_writes_script_and_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "installed_array.tco"
            result = subprocess.run(
                [
                    "cli-anything-ledit",
                    "--json",
                    "square-array",
                    "--rows",
                    "2",
                    "--cols",
                    "2",
                    "--size",
                    "1",
                    "--pitch",
                    "2",
                    "--layer",
                    "Metal1",
                    "--out",
                    str(out_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            receipt = json.loads(result.stdout)
            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["box_count"], 4)
            self.assertEqual(Path(receipt["script"]), out_path.resolve())
            self.assertTrue(out_path.exists())
            self.assertTrue(out_path.with_suffix(".svg").exists())
            self.assertTrue(out_path.with_suffix(".run.txt").exists())
            self.assertTrue(out_path.with_suffix(".open.ps1").exists())

    @unittest.skipIf(shutil.which("powershell") is None, "PowerShell is not on PATH")
    def test_powershell_helper_writes_script_and_prints_run_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            result = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(Path(__file__).resolve().parents[3] / "scripts" / "New-LEditSquareArray.ps1"),
                    "-Rows",
                    "3",
                    "-Cols",
                    "5",
                    "-Size",
                    "1.25",
                    "-PitchX",
                    "2.5",
                    "-PitchY",
                    "3",
                    "-OriginX",
                    "10",
                    "-OriginY",
                    "20",
                    "-Layer",
                    "Metal1",
                    "-Cell",
                    "TOP",
                    "-Name",
                    "helper_test_3x5",
                    "-OutDir",
                    str(out_dir),
                    "-NoClipboard",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            json_text = result.stdout.split("Paste this into the L-Edit Command Window:", 1)[0]
            receipt = json.loads(json_text)
            out_path = out_dir / "helper_test_3x5.tco"
            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["box_count"], 15)
            self.assertEqual(Path(receipt["script"]), out_path.resolve())
            self.assertEqual(receipt["run_command"], build_run_command(out_path.resolve()))
            self.assertEqual(receipt["run_file"], str(out_path.with_suffix(".run.txt").resolve()))
            self.assertEqual(receipt["powershell_open_file"], str(out_path.with_suffix(".open.ps1").resolve()))
            self.assertFalse(receipt["clipboard_copied"])
            self.assertEqual(receipt["bounds"], [10.0, 20.0, 21.25, 27.25])
            self.assertTrue(receipt["verified"])
            self.assertEqual(receipt["verify"]["box_count"], 15)
            self.assertEqual(receipt["verify"]["first_box"], [10.0, 20.0, 11.25, 21.25])
            self.assertEqual(receipt["verify"]["last_box"], [20.0, 26.0, 21.25, 27.25])
            self.assertFalse(receipt["sent_run_command"])
            self.assertIsNone(receipt["send"])
            self.assertTrue(out_path.exists())
            self.assertTrue(out_path.with_suffix(".svg").exists())
            self.assertTrue(out_path.with_suffix(".run.txt").exists())
            self.assertTrue(out_path.with_suffix(".open.ps1").exists())
            script_text = out_path.read_text(encoding="utf-8")
            self.assertIn("box -! 10 20 11.25 21.25", script_text)
            self.assertIn("box -! 20 26 21.25 27.25", script_text)
            self.assertIn(build_run_command(out_path.resolve()), result.stdout)

            verify_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cli_anything.ledit",
                    "--json",
                    "verify-script",
                    str(out_path),
                    "--rows",
                    "3",
                    "--cols",
                    "5",
                    "--size",
                    "1.25",
                    "--pitch-x",
                    "2.5",
                    "--pitch-y",
                    "3",
                    "--origin-x",
                    "10",
                    "--origin-y",
                    "20",
                    "--layer",
                    "Metal1",
                    "--cell",
                    "TOP",
                ],
                cwd=Path(__file__).resolve().parents[4],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(verify_result.returncode, 0, verify_result.stderr + verify_result.stdout)
            verify_receipt = json.loads(verify_result.stdout)
            self.assertTrue(verify_receipt["ok"], verify_receipt["errors"])
            self.assertEqual(verify_receipt["first_box"], [10.0, 20.0, 11.25, 21.25])
            self.assertEqual(verify_receipt["last_box"], [20.0, 26.0, 21.25, 27.25])

    @unittest.skipIf(shutil.which("powershell") is None, "PowerShell is not on PATH")
    def test_send_run_command_reports_no_visible_ledit_window(self):
        visible_check = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-Process -Name ledit64 -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Measure-Object).Count",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(visible_check.returncode, 0, visible_check.stderr + visible_check.stdout)
        if int(visible_check.stdout.strip() or "0") > 0:
            self.skipTest("A visible L-Edit window is present; not sending keys during tests")

        result = subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(Path(__file__).resolve().parents[3] / "scripts" / "Send-LEditRunCommand.ps1"),
                "-RunCommand",
                r"run C:\tmp\dummy.tco",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
        receipt = json.loads(result.stdout)
        self.assertFalse(receipt["ok"])
        self.assertFalse(receipt["sent"])
        self.assertIn("No visible L-Edit window", receipt["error"])


    def test_macro_extract_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "extract.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-extract-action",
                    "--action",
                    "run",
                    "--def-file",
                    str(Path(tmp) / "extract.def"),
                    "--spice-out",
                    str(Path(tmp) / "out.sp"),
                    "--write-node-names",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["macro"], str(out_path.resolve()))
            self.assertEqual(receipt["action"], "run")
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexExtractAction", macro)
            self.assertIn("LExtract_Run(cell,", macro)

    def test_macro_extract_action_requires_def_file_for_run(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-extract-action", "--action", "run"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --def-file", receipt["error"])

    def test_macro_extract_action_writes_set_options_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "extract_opts.cpp"
            result = runner.invoke(
                main,
                [
                    "--json",
                    "macro-extract-action",
                    "--action",
                    "set-options",
                    "--def-file",
                    str(Path(tmp) / "extract.def"),
                    "--spice-out",
                    str(Path(tmp) / "out.sp"),
                    "--write-node-names",
                    "--write-parasitic-cap",
                    "--out",
                    str(out_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("LExtract_GetOptionsEx840", macro)
            self.assertIn("options.bWriteNodeNames = LTRUE", macro)

    def test_capabilities_reports_macro_extract_action(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "capabilities"])

        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        upi_layer = next(layer for layer in receipt["layers"] if layer["name"] == "upi-macro")
        self.assertIn("macro-extract-action", upi_layer["commands"])


    def test_macro_via_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "via.cpp"
            result = runner.invoke(
                main,
                [
                    "--json", "macro-via-action", "--action", "add",
                    "--lower-layer", "Metal1", "--upper-layer", "Metal2",
                    "--via-cell", "VIA1", "--pitch-x", "0.5", "--pitch-y", "0.5",
                    "--out", str(out_path),
                ],
            )
            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["action"], "add")
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexViaAction", macro)
            self.assertIn("LFile_AddVia(file,", macro)

    def test_macro_via_action_rejects_missing_layers(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-via-action", "--action", "add"])
        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --lower-layer", receipt["error"])

    def test_macro_basepoint_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "bp.cpp"
            result = runner.invoke(
                main,
                ["--json", "macro-basepoint-action", "--action", "set", "--x", "1.5", "--y", "2.5", "--out", str(out_path)],
            )
            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["action"], "set")
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexBasepointAction", macro)
            self.assertIn("LCell_SetBasePoint(cell,", macro)

    def test_macro_layer_params_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "lp.cpp"
            result = runner.invoke(
                main,
                [
                    "--json", "macro-layer-params-action", "--action", "set",
                    "--layer", "Metal1", "--gds-number", "10", "--cap", "1.5",
                    "--out", str(out_path),
                ],
            )
            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["action"], "set")
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexLayerParamsAction", macro)
            self.assertIn("LLayer_SetParametersEx1512", macro)
            self.assertIn("params.GDSNumber = 10", macro)

    def test_macro_layer_params_action_requires_layer(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-layer-params-action", "--action", "get"])
        self.assertNotEqual(result.exit_code, 0)

    def test_capabilities_reports_three_new_layers(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "capabilities"])
        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        upi_layer = next(layer for layer in receipt["layers"] if layer["name"] == "upi-macro")
        self.assertIn("macro-via-action", upi_layer["commands"])
        self.assertIn("macro-basepoint-action", upi_layer["commands"])
        self.assertIn("macro-layer-params-action", upi_layer["commands"])


    def test_macro_technology_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "tech.cpp"
            result = runner.invoke(
                main,
                ["--json", "macro-technology-action", "--action", "set-name", "--tech-name", "MyTech", "--out", str(out_path)],
            )
            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["action"], "set-name")
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexTechnologyAction", macro)
            self.assertIn('LFile_SetTechnologyName(file, "MyTech")', macro)

    def test_macro_technology_action_requires_name_for_set_name(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "macro-technology-action", "--action", "set-name"])
        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        self.assertFalse(receipt["ok"])
        self.assertIn("requires --tech-name", receipt["error"])

    def test_macro_cell_info_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "cellinfo.cpp"
            result = runner.invoke(
                main,
                ["--json", "macro-cell-info-action", "--action", "list", "--out", str(out_path)],
            )
            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["action"], "list")
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexCellInfoAction", macro)
            self.assertIn("LCell_GetList(file)", macro)

    def test_capabilities_reports_technology_and_cell_info(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "capabilities"])
        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        upi_layer = next(layer for layer in receipt["layers"] if layer["name"] == "upi-macro")
        self.assertIn("macro-technology-action", upi_layer["commands"])
        self.assertIn("macro-cell-info-action", upi_layer["commands"])


    def test_macro_object_action_writes_torus_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "torus.cpp"
            result = runner.invoke(
                main,
                [
                    "--json", "macro-object-action", "--kind", "torus",
                    "--x", "5", "--y", "5", "--inner-radius", "1", "--outer-radius", "2",
                    "--out", str(out_path),
                ],
            )
            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["kind"], "torus")
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("LTorus_CreateNew", macro)

    def test_macro_net_info_action_writes_upi_macro(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "netinfo.cpp"
            result = runner.invoke(
                main,
                ["--json", "macro-net-info-action", "--action", "list", "--out", str(out_path)],
            )
            self.assertEqual(result.exit_code, 0, result.output)
            receipt = json.loads(result.output)
            self.assertTrue(receipt["ok"], receipt.get("error"))
            self.assertEqual(receipt["action"], "list")
            macro = out_path.read_text(encoding="utf-8")
            self.assertIn("CodexNetInfoAction", macro)
            self.assertIn("LCell_GetNetList(cell)", macro)

    def test_capabilities_reports_net_info(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "capabilities"])
        self.assertEqual(result.exit_code, 0, result.output)
        receipt = json.loads(result.output)
        upi_layer = next(layer for layer in receipt["layers"] if layer["name"] == "upi-macro")
        self.assertIn("macro-net-info-action", upi_layer["commands"])


if __name__ == "__main__":
    unittest.main()
