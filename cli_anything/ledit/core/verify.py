from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .script_writer import CURRENT_LAYER, SquareArraySpec, format_number


BOX_RE = re.compile(
    r"^box -! "
    r"(?P<x1>-?\d+(?:\.\d+)?) (?P<y1>-?\d+(?:\.\d+)?) "
    r"(?P<x2>-?\d+(?:\.\d+)?) (?P<y2>-?\d+(?:\.\d+)?)$"
)
TOLERANCE = 1e-9


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    script: str
    box_count: int
    expected_box_count: int
    bounds: tuple[float, float, float, float]
    first_box: tuple[float, float, float, float] | None
    last_box: tuple[float, float, float, float] | None
    errors: list[str]
    spec: dict[str, object] | None = None


@dataclass(frozen=True)
class LayoutScriptVerificationResult:
    ok: bool
    script: str
    line_count: int
    command_count: int
    counts: dict[str, int]
    raw_count: int
    errors: list[str]
    warnings: list[str]


def parse_box_line(line: str) -> tuple[float, float, float, float] | None:
    match = BOX_RE.match(line.strip())
    if not match:
        return None
    return tuple(float(match.group(name)) for name in ("x1", "y1", "x2", "y2"))


def verify_square_array_script(script_path: Path, spec: SquareArraySpec | None = None) -> VerificationResult:
    script_path = script_path.resolve()
    lines = script_path.read_text(encoding="utf-8").splitlines()
    boxes = [box for box in (parse_box_line(line) for line in lines) if box is not None]
    errors: list[str] = []

    if not boxes:
        errors.append("No box -! commands were found.")

    if spec is None:
        spec = _infer_spec_from_script(lines, boxes)
    expected_box_count = spec.count

    if len(boxes) != expected_box_count:
        errors.append(f"Expected {expected_box_count} boxes but found {len(boxes)}.")

    expected_boxes = spec.boxes()
    if boxes and expected_boxes and not _boxes_close(boxes[0], expected_boxes[0]):
        errors.append(
            "First box mismatch: expected "
            f"{_fmt_box(expected_boxes[0])} but found {_fmt_box(boxes[0])}."
        )
    if boxes and expected_boxes and not _boxes_close(boxes[-1], expected_boxes[-1]):
        errors.append(
            "Last box mismatch: expected "
            f"{_fmt_box(expected_boxes[-1])} but found {_fmt_box(boxes[-1])}."
        )

    actual_bounds = _bounds_from_boxes(boxes) if boxes else (0.0, 0.0, 0.0, 0.0)
    expected_bounds = spec.bounds
    if boxes and not _boxes_close(actual_bounds, expected_bounds):
        errors.append(
            "Bounds mismatch: expected "
            f"{_fmt_box(expected_bounds)} but found {_fmt_box(actual_bounds)}."
        )

    return VerificationResult(
        ok=not errors,
        script=str(script_path),
        box_count=len(boxes),
        expected_box_count=expected_box_count,
        bounds=actual_bounds,
        first_box=boxes[0] if boxes else None,
        last_box=boxes[-1] if boxes else None,
        errors=errors,
        spec=spec.to_dict(),
    )


def verify_layout_script(script_path: Path) -> LayoutScriptVerificationResult:
    script_path = script_path.resolve()
    lines = script_path.read_text(encoding="utf-8").splitlines()
    known_commands = {
        "array",
        "box",
        "cell",
        "copy",
        "goto",
        "instance",
        "layer",
        "move",
        "paste",
        "path",
        "polygon",
        "rotate",
        "save",
        "saveas",
        "text",
        "width",
    }
    counts = {command: 0 for command in sorted(known_commands)}
    errors: list[str] = []
    warnings: list[str] = []
    raw_count = 0
    command_count = 0

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        command_count += 1
        command = stripped.split(maxsplit=1)[0].lower()
        if command == "run":
            errors.append(f"Nested run command is not allowed at line {line_number}.")
            continue
        if command in counts:
            counts[command] += 1
        else:
            raw_count += 1
            warnings.append(f"Line {line_number} uses unclassified raw command: {command}.")

    if command_count == 0:
        errors.append("No executable L-Edit commands were found.")

    return LayoutScriptVerificationResult(
        ok=not errors,
        script=str(script_path),
        line_count=len(lines),
        command_count=command_count,
        counts=counts,
        raw_count=raw_count,
        errors=errors,
        warnings=warnings,
    )


def _infer_spec_from_script(lines: list[str], boxes: list[tuple[float, float, float, float]]) -> SquareArraySpec:
    cell = "TOP"
    layer = CURRENT_LAYER
    for line in lines:
        if line.startswith("cell "):
            cell = line.split(" ", 1)[1].strip().strip('"')
        if line.startswith("layer "):
            layer = line.split(" ", 1)[1].strip().strip('"')
    if not boxes:
        return SquareArraySpec(rows=0, cols=0, size=0.0, pitch_x=1.0, pitch_y=1.0, layer=layer, cell=cell)
    first = boxes[0]
    if len(boxes) > 1:
        second = boxes[1]
        pitch_x = second[0] - first[0]
    else:
        pitch_x = first[2] - first[0]
    row_starts = [box[1] for box in boxes]
    rows = 1
    for idx in range(1, len(row_starts)):
        if row_starts[idx] != row_starts[0]:
            rows = idx
            break
    if rows == 1:
        pitch_y = first[3] - first[1]
    else:
        pitch_y = boxes[rows][1] - boxes[0][1]
    size = first[2] - first[0]
    origin_x = first[0]
    origin_y = first[1]
    cols = max(1, len(boxes) // rows)
    return SquareArraySpec(
        rows=rows,
        cols=cols,
        size=size,
        pitch_x=pitch_x,
        pitch_y=pitch_y,
        layer=layer,
        cell=cell,
        origin_x=origin_x,
        origin_y=origin_y,
    )


def _bounds_from_boxes(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    x1 = min(box[0] for box in boxes)
    y1 = min(box[1] for box in boxes)
    x2 = max(box[2] for box in boxes)
    y2 = max(box[3] for box in boxes)
    return (x1, y1, x2, y2)


def _fmt_box(box: tuple[float, float, float, float]) -> str:
    return "(" + ", ".join(format_number(value) for value in box) + ")"


def _boxes_close(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> bool:
    return all(abs(a - b) <= TOLERANCE for a, b in zip(left, right))
