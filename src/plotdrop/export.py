from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure

from plotdrop.settings import DEFAULT_EXPORT_DPI, SUPPORTED_EXPORT_EXTENSIONS


class ExportError(ValueError):
    """Raised when the current figure cannot be exported."""


def validate_export_path(path: str | Path) -> Path:
    export_path = Path(path)
    extension = export_path.suffix.lower()
    if extension not in SUPPORTED_EXPORT_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXPORT_EXTENSIONS))
        raise ExportError(
            f"Unsupported export format '{extension or '<none>'}'. "
            f"Supported formats: {supported}."
        )
    return export_path


def save_figure(figure: Figure, path: str | Path) -> Path:
    export_path = validate_export_path(path)
    kwargs = {"dpi": DEFAULT_EXPORT_DPI} if export_path.suffix.lower() == ".png" else {}
    figure.savefig(export_path, **kwargs)
    return export_path
