from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget

from plotdrop.dataset import Dataset
from plotdrop.export import save_figure
from plotdrop.settings import DEFAULT_FIGURE_SIZE, SCALE_MODES


class PlotScaleError(ValueError):
    """Raised when an axis scale cannot be applied to the current datasets."""


@dataclass(frozen=True)
class PlotScaleWarning:
    masked_points: int = 0
    skipped_datasets: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_warning(self) -> bool:
        return self.masked_points > 0 or bool(self.skipped_datasets)

    def message(self) -> str:
        parts: list[str] = []
        if self.masked_points:
            parts.append(f"{self.masked_points} point(s) hidden because log axes require positive values.")
        if self.skipped_datasets:
            skipped = ", ".join(self.skipped_datasets)
            parts.append(f"Dataset(s) not plotted in this scale: {skipped}.")
        return " ".join(parts)


class PlotWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._datasets: list[Dataset] = []
        self._scale_mode = "linear"

        self.figure = Figure(figsize=DEFAULT_FIGURE_SIZE)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.axes = self.figure.add_subplot(111)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self._redraw()

    @property
    def scale_mode(self) -> str:
        return self._scale_mode

    def set_datasets(self, datasets: list[Dataset]) -> PlotScaleWarning | None:
        self._datasets = list(datasets)
        return self._redraw()

    def clear(self) -> None:
        self._datasets.clear()
        self._scale_mode = "linear"
        self._redraw()

    def set_scale(self, scale_mode: str) -> PlotScaleWarning | None:
        if scale_mode not in SCALE_MODES:
            raise PlotScaleError(f"Unsupported scale mode: {scale_mode}")

        previous_scale = self._scale_mode
        self._scale_mode = scale_mode
        try:
            return self._redraw()
        except PlotScaleError:
            self._scale_mode = previous_scale
            self._redraw()
            raise

    def save(self, path: str | Path) -> Path:
        return save_figure(self.figure, path)

    def _redraw(self) -> PlotScaleWarning | None:
        self.axes.clear()
        warning = self._plot_datasets()
        self._apply_axis_scale()
        self.axes.set_xlabel("x")
        self.axes.set_ylabel("y")
        if self.axes.lines:
            self.axes.legend()
        self.figure.tight_layout()
        self.canvas.draw_idle()
        return warning if warning and warning.has_warning else None

    def _plot_datasets(self) -> PlotScaleWarning | None:
        if not self._datasets:
            return None

        masked_points = 0
        skipped_datasets: list[str] = []
        plotted_count = 0

        for dataset in self._datasets:
            x, y, masked = self._filtered_for_scale(dataset)
            masked_points += masked
            if x.size == 0:
                skipped_datasets.append(dataset.name)
                continue
            self.axes.plot(x, y, label=dataset.name)
            plotted_count += 1

        if plotted_count == 0:
            raise PlotScaleError("No positive data points remain for the selected logarithmic scale.")

        return PlotScaleWarning(masked_points, tuple(skipped_datasets))

    def _filtered_for_scale(self, dataset: Dataset) -> tuple[np.ndarray, np.ndarray, int]:
        if self._scale_mode == "linear":
            return dataset.x, dataset.y, 0

        mask = np.ones(dataset.point_count, dtype=bool)
        if self._scale_mode in {"logx", "loglog"}:
            mask &= dataset.x > 0
        if self._scale_mode in {"logy", "loglog"}:
            mask &= dataset.y > 0

        masked_count = int(dataset.point_count - np.count_nonzero(mask))
        return dataset.x[mask], dataset.y[mask], masked_count

    def _apply_axis_scale(self) -> None:
        if self._scale_mode in {"logx", "loglog"}:
            self.axes.set_xscale("log")
        else:
            self.axes.set_xscale("linear")

        if self._scale_mode in {"logy", "loglog"}:
            self.axes.set_yscale("log")
        else:
            self.axes.set_yscale("linear")
