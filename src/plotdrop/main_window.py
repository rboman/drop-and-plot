from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plotdrop.data_loader import DataLoadError, load_dataset
from plotdrop.dataset import Dataset
from plotdrop.export import ExportError
from plotdrop.plot_widget import PlotScaleError, PlotScaleWarning, PlotWidget
from plotdrop.settings import SCALE_MODES, SUPPORTED_EXPORT_EXTENSIONS


@dataclass
class LoadEntry:
    name: str
    status: str
    point_count: int | None = None
    message: str = ""
    dataset: Dataset | None = None


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PlotDrop")
        self.resize(1000, 700)
        self.setAcceptDrops(True)

        self._entries: list[LoadEntry] = []
        self._datasets: list[Dataset] = []

        self.plot_widget = PlotWidget(self)
        self.dataset_table = self._build_dataset_table()
        self.scale_combo = self._build_scale_combo()
        self.grid_checkbox = self._build_grid_checkbox()

        self._build_layout()
        self._build_menu()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._event_has_local_files(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._local_file_paths(event)
        if not paths:
            event.ignore()
            return

        event.acceptProposedAction()
        self.load_files(paths)

    def load_files(self, paths: list[Path]) -> None:
        for path in paths:
            try:
                dataset = load_dataset(path)
            except DataLoadError as exc:
                self._entries.append(
                    LoadEntry(name=path.name, status="Error", message=str(exc))
                )
                continue

            self._datasets.append(dataset)
            self._entries.append(
                LoadEntry(
                    name=dataset.name,
                    status="Loaded",
                    point_count=dataset.point_count,
                    dataset=dataset,
                )
            )

        self._refresh_dataset_table()
        self._redraw_plot()

    def clear(self) -> None:
        self._entries.clear()
        self._datasets.clear()
        self.scale_combo.setCurrentText("linear")
        self.plot_widget.clear()
        self._refresh_dataset_table()

    def export_current_figure(self) -> None:
        if not self._datasets:
            QMessageBox.information(self, "Export", "No dataset is loaded.")
            return

        filters = ";;".join(
            [
                "PNG image (*.png)",
                "PDF document (*.pdf)",
                "SVG image (*.svg)",
            ]
        )
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export figure",
            "plotdrop.png",
            filters,
        )
        if not path:
            return

        export_path = self._ensure_export_extension(Path(path))
        try:
            self.plot_widget.save(export_path)
        except ExportError as exc:
            QMessageBox.critical(self, "Export error", str(exc))
        except OSError as exc:
            QMessageBox.critical(self, "Export error", f"Could not save figure: {exc}")

    def _build_layout(self) -> None:
        central = QWidget(self)
        outer = QHBoxLayout(central)

        side_panel = QWidget(central)
        side_panel.setMinimumWidth(380)
        side_panel.setMaximumWidth(480)
        side_layout = QVBoxLayout(side_panel)
        side_layout.addWidget(QLabel("Datasets"))
        side_layout.addWidget(self.dataset_table)

        controls = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear)
        export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_current_figure)
        controls.addWidget(clear_button)
        controls.addWidget(export_button)
        side_layout.addLayout(controls)

        side_layout.addWidget(QLabel("Scale"))
        side_layout.addWidget(self.scale_combo)
        side_layout.addWidget(self.grid_checkbox)
        side_layout.addStretch()

        outer.addWidget(side_panel)
        outer.addWidget(self.plot_widget, 1)
        self.setCentralWidget(central)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        open_action = QAction("&Open...", self)
        open_action.triggered.connect(self._open_files)
        file_menu.addAction(open_action)

        export_action = QAction("&Export...", self)
        export_action.triggered.connect(self.export_current_figure)
        file_menu.addAction(export_action)

        clear_action = QAction("&Clear", self)
        clear_action.triggered.connect(self.clear)
        file_menu.addAction(clear_action)

    def _build_dataset_table(self) -> QTableWidget:
        table = QTableWidget(0, 4, self)
        table.setHorizontalHeaderLabels(["File", "Points", "Status", "Message"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setMinimumHeight(150)
        table.setMaximumHeight(280)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(1, 62)
        table.setColumnWidth(2, 72)
        return table

    def _build_scale_combo(self) -> QComboBox:
        combo = QComboBox(self)
        combo.addItems(SCALE_MODES)
        combo.currentTextChanged.connect(self._scale_changed)
        return combo

    def _build_grid_checkbox(self) -> QCheckBox:
        checkbox = QCheckBox("Grid", self)
        checkbox.toggled.connect(self._grid_toggled)
        return checkbox

    def _refresh_dataset_table(self) -> None:
        self.dataset_table.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            values = [
                entry.name,
                "" if entry.point_count is None else str(entry.point_count),
                entry.status,
                entry.message,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setToolTip(entry.name)
                if column == 3 and entry.message:
                    item.setToolTip(entry.message)
                if entry.status == "Error":
                    item.setToolTip(entry.message)
                self.dataset_table.setItem(row, column, item)

    def _scale_changed(self, scale_mode: str) -> None:
        try:
            warning = self.plot_widget.set_scale(scale_mode)
        except PlotScaleError as exc:
            self.scale_combo.blockSignals(True)
            self.scale_combo.setCurrentText(self.plot_widget.scale_mode)
            self.scale_combo.blockSignals(False)
            QMessageBox.warning(self, "Scale not applied", str(exc))
            return

        self._show_scale_warning(warning)

    def _redraw_plot(self) -> None:
        try:
            warning = self.plot_widget.set_datasets(self._datasets)
        except PlotScaleError as exc:
            self.scale_combo.blockSignals(True)
            self.scale_combo.setCurrentText("linear")
            self.scale_combo.blockSignals(False)
            self.plot_widget.set_scale("linear")
            QMessageBox.warning(self, "Scale reset", str(exc))
            return

        self._show_scale_warning(warning)

    def _show_scale_warning(self, warning: PlotScaleWarning | None) -> None:
        if warning and warning.has_warning:
            QMessageBox.warning(self, "Log scale warning", warning.message())

    def _grid_toggled(self, visible: bool) -> None:
        try:
            warning = self.plot_widget.set_grid_visible(visible)
        except PlotScaleError as exc:
            self.grid_checkbox.blockSignals(True)
            self.grid_checkbox.setChecked(not visible)
            self.grid_checkbox.blockSignals(False)
            QMessageBox.warning(self, "Grid not applied", str(exc))
            return

        self._show_scale_warning(warning)

    def _open_files(self) -> None:
        paths, _selected_filter = QFileDialog.getOpenFileNames(
            self,
            "Open data files",
            "",
            "Data files (*.txt *.dat *.csv *.tsv);;All files (*)",
        )
        if paths:
            self.load_files([Path(path) for path in paths])

    def _ensure_export_extension(self, path: Path) -> Path:
        if path.suffix:
            return path
        selected = ".png"
        if selected not in SUPPORTED_EXPORT_EXTENSIONS:
            return path
        return path.with_suffix(selected)

    def _event_has_local_files(self, event: QDragEnterEvent | QDropEvent) -> bool:
        return bool(self._local_file_paths(event))

    def _local_file_paths(self, event: QDragEnterEvent | QDropEvent) -> list[Path]:
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            return []

        paths: list[Path] = []
        for url in mime_data.urls():
            if not url.isLocalFile():
                return []
            path = Path(url.toLocalFile())
            if path.is_file():
                paths.append(path)
        return paths
