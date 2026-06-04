"""Backend utilities for interacting with a local Tanner L-Edit installation.

This module handles:
  - Discovering the ledit64.exe binary
  - Compiling UPI C++ macros with the bundled MinGW g++
  - Launching L-Edit with macro arguments
  - Sending keystroke ``run`` commands to the L-Edit command window
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from ..config import (
    LEDIT_CANDIDATES,
    resolve_gcc,
    resolve_ledit_doc,
    resolve_ledit_exe,
    resolve_upi_include,
    resolve_upi_link_lib,
)
from ..core.script_writer import build_run_command


# ---------------------------------------------------------------------------
# Installation inspection
# ---------------------------------------------------------------------------


def inspect_install() -> dict[str, object]:
    """Return a JSON-serialisable snapshot of the detected L-Edit installation."""
    resolved = resolve_ledit_exe()
    processes = inspect_ledit_processes()
    doc = resolve_ledit_doc()
    return {
        "ledit_exe": str(resolved) if resolved else None,
        "ledit_exe_exists": resolved is not None,
        "ledit_doc": str(doc),
        "ledit_candidates": [{"path": str(c), "exists": c.exists()} for c in LEDIT_CANDIDATES],
        "ledit_doc_exists": doc.exists(),
        "processes": processes,
        "process_count": len(processes),
        "visible_window_count": sum(1 for p in processes if p["main_window_handle"] != 0),
        "can_send_run_command": any(p["main_window_handle"] != 0 for p in processes),
        "script_execution": "Open L-Edit command window and run: run <path-to-tco>",
    }


# ---------------------------------------------------------------------------
# Process helpers
# ---------------------------------------------------------------------------


def inspect_ledit_processes() -> list[dict[str, object]]:
    """Enumerate running ledit64.exe processes via PowerShell."""
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        return []
    command = (
        "Get-Process -Name ledit64 -ErrorAction SilentlyContinue | "
        "Select-Object Id,Responding,"
        "@{Name='MainWindowHandleValue';Expression={[int64]$_.MainWindowHandle}},"
        "MainWindowTitle,StartTime | ConvertTo-Json -Depth 4"
    )
    result = subprocess.run(
        [shell, "-NoProfile", "-Command", command],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    data = json.loads(result.stdout)
    if isinstance(data, dict):
        data = [data]
    processes: list[dict[str, object]] = []
    for item in data:
        handle = int(item.get("MainWindowHandleValue") or 0)
        processes.append(
            {
                "id": int(item["Id"]),
                "responding": bool(item.get("Responding")),
                "main_window_handle": handle,
                "main_window_title": item.get("MainWindowTitle") or "",
                "start_time": item.get("StartTime"),
                "visible": handle != 0,
            }
        )
    return processes


# ---------------------------------------------------------------------------
# Launch helpers
# ---------------------------------------------------------------------------


def launch_ledit(
    extra_args: list[str] | None = None,
    default_args: bool = True,
) -> dict[str, object]:
    """Start a new L-Edit process and return a launch receipt."""
    exe = resolve_ledit_exe()
    if exe is None:
        return {
            "ok": False,
            "error": "No existing L-Edit executable was found. Set LEDIT_EXE or install Tanner Tools.",
        }
    args = [str(exe)]
    if default_args:
        args.extend(["-s", "-n"])
    if extra_args:
        args.extend(extra_args)
    subprocess.Popen(args, cwd=str(exe.parent))
    return {"ok": True, "ledit_exe": str(exe), "args": args[1:]}


def build_upi_launch_plan(
    macro_path: Path,
    extra_args: list[str] | None = None,
    default_args: bool = True,
    macro_first: bool = False,
) -> dict[str, object]:
    """Build the command-line plan for launching L-Edit with a UPI macro."""
    exe = resolve_ledit_exe()
    macro_args = ["-U", str(macro_path.resolve())]
    if extra_args:
        idx = 0 if macro_first else len(macro_args)
        for a in extra_args:
            macro_args.insert(idx, a)
            idx += 1
    args = ["-s", "-n", *macro_args] if default_args else list(macro_args)
    quoted_args = " ".join(f'"{a}"' if " " in str(a) else str(a) for a in args)
    return {
        "ok": exe is not None,
        "ledit_exe": str(exe) if exe else None,
        "macro": str(macro_path.resolve()),
        "args": args,
        "extra_args": macro_args,
        "command": (f'"{exe}" {quoted_args}'.strip() if exe else None),
    }


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------


def preflight_upi_execution(
    macro_path: Path | None = None,
    *,
    default_args: bool = True,
    macro_first: bool = False,
    require_clean_instance: bool = True,
) -> dict[str, object]:
    """Check whether it is safe to launch L-Edit with a UPI macro."""
    processes = inspect_ledit_processes()
    visible = [p for p in processes if p["main_window_handle"] != 0]
    macro_exists = None
    launch_plan = None
    if macro_path is not None:
        macro_path = macro_path.resolve()
        macro_exists = macro_path.exists()
        launch_plan = build_upi_launch_plan(
            macro_path, default_args=default_args, macro_first=macro_first
        )
    blockers: list[str] = []
    warnings: list[str] = []
    if resolve_ledit_exe() is None:
        blockers.append("No existing L-Edit executable was found. Set LEDIT_EXE or install Tanner Tools.")
    if require_clean_instance and processes:
        blockers.append(
            f"{len(processes)} ledit64 process(es) already running "
            f"({len(visible)} visible). Close them or use --allow-existing-process."
        )
    if macro_path is not None and not macro_exists:
        blockers.append(f"Macro file does not exist: {macro_path}")
    if not visible:
        warnings.append("No visible L-Edit window found; foreground send commands will fail.")
    return {
        "ok": not blockers,
        "ready": not blockers,
        "ledit_exe": str(resolve_ledit_exe()),
        "process_count": len(processes),
        "visible_count": len(visible),
        "macro": str(macro_path) if macro_path else None,
        "macro_path": str(macro_path) if macro_path else None,
        "macro_exists": macro_exists,
        "launch_plan": launch_plan,
        "blockers": blockers,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# UPI compilation
# ---------------------------------------------------------------------------


def compile_upi_macro(
    cpp_path: Path,
    out_path: Path | None = None,
    def_path: Path | None = None,
    exported_functions: list[str] | None = None,
) -> dict[str, object]:
    """Compile a C++ UPI macro source into a .upi DLL using the Tanner MinGW toolchain."""
    cpp_path = cpp_path.resolve()
    if out_path is None:
        out_path = cpp_path.with_suffix(".upi")
    out_path = out_path.resolve()
    if def_path is None:
        def_path = cpp_path.with_suffix(".def")
    def_path = def_path.resolve()

    gcc = resolve_gcc()
    include_dir = resolve_upi_include()
    link_lib = resolve_upi_link_lib()

    if not gcc.exists():
        return {"ok": False, "error": f"g++.exe was not found: {gcc}. Set LEDIT_GCC.", "compiled": False}
    if not link_lib.exists():
        return {"ok": False, "error": f"UPI link library was not found: {link_lib}. Set LEDIT_UPI_LINK_LIB.", "compiled": False}

    if not def_path.exists():
        exports = exported_functions or ["CodexSquareArray"]
        def_path.write_text(
            "\n".join(
                [
                    f"LIBRARY {out_path.stem}",
                    "EXPORTS",
                    "    UPI_Entry_Point",
                    *[f"    {fn}" for fn in exports],
                    "",
                ]
            ),
            encoding="ascii",
        )

    command = [
        str(gcc),
        "-shared",
        "-DMAKE_DLL",
        "-I",
        str(include_dir),
        "-o",
        str(out_path),
        str(cpp_path),
        str(def_path),
        str(link_lib),
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "ok": result.returncode == 0,
        "compiled": result.returncode == 0,
        "macro": str(cpp_path),
        "upi": str(out_path),
        "def_file": str(def_path),
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


# ---------------------------------------------------------------------------
# UPI execution
# ---------------------------------------------------------------------------


def execute_upi_macro(
    macro_path: Path,
    wait_seconds: float = 4.0,
    extra_args: list[str] | None = None,
    default_args: bool = True,
    macro_first: bool = False,
) -> dict[str, object]:
    """Launch L-Edit with a compiled UPI macro and wait for it to finish."""
    plan = build_upi_launch_plan(
        macro_path, extra_args=extra_args, default_args=default_args, macro_first=macro_first
    )
    args = list(plan["extra_args"])
    before = inspect_ledit_processes()
    launch_receipt = launch_ledit(args, default_args=default_args)
    receipt: dict[str, object] = {
        "ok": bool(launch_receipt.get("ok")),
        "launch": launch_receipt,
        "macro": str(macro_path.resolve()),
        "wait_seconds": wait_seconds,
        "processes_before": before,
    }
    if not launch_receipt.get("ok"):
        receipt["error"] = launch_receipt.get("error", "Failed to launch L-Edit with macro.")
        return receipt
    time.sleep(max(wait_seconds, 0.0))
    receipt["processes_after"] = inspect_ledit_processes()
    return receipt


# ---------------------------------------------------------------------------
# Keystroke sender
# ---------------------------------------------------------------------------


def send_run_command(run_command: str, helper_path: Path | None = None) -> dict[str, object]:
    """Send a ``run`` command to the focused L-Edit command window via SendKeys."""
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        return {
            "ok": False,
            "sent": False,
            "error": "PowerShell was not found; cannot send keys to L-Edit.",
            "run_command": run_command,
        }
    if helper_path is None:
        helper_path = Path(__file__).resolve().parents[3] / "scripts" / "Send-LEditRunCommand.ps1"
    if not helper_path.exists():
        return {
            "ok": False,
            "sent": False,
            "error": f"Send helper was not found: {helper_path}",
            "run_command": run_command,
        }
    result = subprocess.run(
        [shell, "-ExecutionPolicy", "Bypass", "-File", str(helper_path), "-RunCommand", run_command],
        text=True,
        capture_output=True,
        check=False,
    )
    stdout = result.stdout.strip()
    if stdout:
        try:
            receipt = json.loads(stdout)
        except json.JSONDecodeError:
            receipt = {"ok": result.returncode == 0, "sent": result.returncode == 0, "raw_stdout": stdout}
    else:
        receipt = {"ok": result.returncode == 0, "sent": result.returncode == 0}
    receipt.setdefault("run_command", run_command)
    receipt["returncode"] = result.returncode
    if result.stderr.strip():
        receipt["stderr"] = result.stderr.strip()
    return receipt


def send_run_script(script_path: Path, helper_path: Path | None = None) -> dict[str, object]:
    """Send a ``run <script_path>`` command to L-Edit's command window."""
    script_path = script_path.resolve()
    if not script_path.exists():
        return {
            "ok": False,
            "sent": False,
            "error": f"Script does not exist: {script_path}",
            "script": str(script_path),
        }
    run_command = build_run_command(script_path)
    receipt = send_run_command(run_command, helper_path)
    receipt["script"] = str(script_path)
    return receipt
