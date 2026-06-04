"""Centralized configuration for cli-anything-ledit.

All paths that were previously hardcoded are now configurable via environment
variables.  Each variable has a sensible default so the tool still works out of
the box on a typical Tanner Tools v16.3 installation on Windows.

Environment variables
---------------------
LEDIT_EXE
    Full path to ledit64.exe.  Falls back to scanning well-known install dirs.
LEDIT_DOC
    Full path to the L-Edit PDF documentation.
LEDIT_GCC
    Full path to the g++.exe shipped with Tanner (MinGW).
LEDIT_UPI_INCLUDE
    Directory containing ldata.h and the UPI link library.
LEDIT_UPI_LINK_LIB
    Full path to libupilink-gcc4.6.3-x64.a (or equivalent).
LEDIT_DEFAULT_OUTPUT_DIR
    Default directory for generated output files.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# L-Edit executable
# ---------------------------------------------------------------------------

LEDIT_CANDIDATES: list[Path] = [
    Path(r"C:\Program Files\Tanner EDA\Tanner Tools v16.3\ledit64.exe"),
    Path(r"C:\L-edit\Tanner-Tools-v16.30\patched\ledit64.exe"),
    Path(r"C:\Program Files (x86)\Tanner EDA\Tanner Tools v16.3\ledit64.exe"),
]

DEFAULT_LEDIT_DOC = Path(r"C:\Program Files\Tanner EDA\Tanner Tools v16.3\Docs\ledit.pdf")

# ---------------------------------------------------------------------------
# UPI compiler toolchain
# ---------------------------------------------------------------------------

DEFAULT_GCC = Path(r"C:\Program Files\Tanner EDA\Tanner Tools v16.3\mingw64\bin\g++.exe")
DEFAULT_UPI_INCLUDE = Path(r"C:\Program Files\Tanner EDA\Tanner Tools v16.3\upi\Include")
DEFAULT_UPI_LINK_LIB = DEFAULT_UPI_INCLUDE / "libupilink-gcc4.6.3-x64.a"

# ---------------------------------------------------------------------------
# Derived / resolved values
# ---------------------------------------------------------------------------


def _env_path(name: str, default: Path | None = None) -> Path | None:
    """Read a Path from an environment variable, returning *default* when unset."""
    raw = os.environ.get(name, "").strip()
    return Path(raw) if raw else default


def resolve_ledit_exe() -> Path | None:
    """Return the first existing L-Edit executable, respecting LEDIT_EXE."""
    explicit = _env_path("LEDIT_EXE")
    if explicit and explicit.exists():
        return explicit
    for candidate in LEDIT_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def resolve_ledit_doc() -> Path:
    return _env_path("LEDIT_DOC", DEFAULT_LEDIT_DOC)  # type: ignore[return-value]


def resolve_gcc() -> Path:
    return _env_path("LEDIT_GCC", DEFAULT_GCC)  # type: ignore[return-value]


def resolve_upi_include() -> Path:
    return _env_path("LEDIT_UPI_INCLUDE", DEFAULT_UPI_INCLUDE)  # type: ignore[return-value]


def resolve_upi_link_lib() -> Path:
    return _env_path("LEDIT_UPI_LINK_LIB", DEFAULT_UPI_LINK_LIB)  # type: ignore[return-value]


def resolve_default_output_dir() -> Path:
    return _env_path("LEDIT_DEFAULT_OUTPUT_DIR", Path("outputs"))  # type: ignore[return-value]