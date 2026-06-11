from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np

from plotdrop.dataset import Dataset
from plotdrop.settings import SUPPORTED_DATA_EXTENSIONS


class DataLoadError(ValueError):
    """Raised when a data file cannot be parsed into a Dataset."""


_SEPARATOR_RE = re.compile(r"[,\s;]+")


def load_dataset(path: str | Path) -> Dataset:
    data_path = Path(path)
    extension = data_path.suffix.lower()
    if extension not in SUPPORTED_DATA_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_DATA_EXTENSIONS))
        raise DataLoadError(
            f"Unsupported file extension '{extension or '<none>'}'. "
            f"Supported extensions: {supported}."
        )

    if not data_path.exists():
        raise DataLoadError(f"File does not exist: {data_path}")
    if not data_path.is_file():
        raise DataLoadError(f"Path is not a file: {data_path}")

    rows: list[list[float]] = []
    header_skipped = False
    data_started = False

    try:
        lines = data_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise DataLoadError(f"Could not read '{data_path.name}' as UTF-8 text.") from exc
    except OSError as exc:
        raise DataLoadError(f"Could not read '{data_path.name}': {exc}") from exc

    for line_number, raw_line in enumerate(lines, start=1):
        content = _strip_comment(raw_line).strip()
        if not content:
            continue

        parts = [part for part in _SEPARATOR_RE.split(content) if part]
        parsed = _parse_numeric_parts(parts)
        if parsed is None:
            if not data_started and not header_skipped:
                header_skipped = True
                continue
            raise DataLoadError(
                f"Line {line_number} in '{data_path.name}' is not numeric data."
            )

        data_started = True
        rows.append(parsed)

    if not rows:
        raise DataLoadError(f"'{data_path.name}' does not contain usable numeric data.")

    column_counts = {len(row) for row in rows}
    if len(column_counts) != 1:
        raise DataLoadError(f"'{data_path.name}' has inconsistent column counts.")

    values = np.asarray(rows, dtype=np.float64)
    if values.shape[1] == 1:
        y = values[:, 0]
        x = np.arange(y.size, dtype=np.float64)
    else:
        x = values[:, 0]
        y = values[:, 1]

    return Dataset(path=data_path, name=data_path.name, x=x, y=y)


def _strip_comment(line: str) -> str:
    return line.split("#", 1)[0]


def _parse_numeric_parts(parts: list[str]) -> list[float] | None:
    if not parts:
        return None

    values: list[float] = []
    for part in parts:
        try:
            value = float(part)
        except ValueError:
            return None
        if not math.isfinite(value):
            raise DataLoadError(f"Non-finite value '{part}' is not supported.")
        values.append(value)

    return values
