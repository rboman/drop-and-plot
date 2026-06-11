# PlotDrop Agent Notes

This file is for future Codex sessions. Keep `README.md` user-facing; keep implementation memory and working context here.

## Current State

- PlotDrop is a Python 3.11+ desktop MVP using PySide6, Matplotlib, and numpy.
- The repository started empty and now contains the full app skeleton under `src/plotdrop/`, tests under `tests/`, and sample data under `examples/`.
- The app is installable with `pip install -e ".[dev]"` and exposes the `plotdrop` console entry point.
- The main UI has a left dataset panel and a Matplotlib plot area with `NavigationToolbar2QT`.
- The dataset panel includes `Clear`, `Export`, scale selection, and a `Grid` checkbox.

## Important Implementation Details

- `data_loader.py` owns parsing and raises `DataLoadError`.
- `plot_widget.py` owns plotting, scale changes, grid display, and figure saving.
- `main_window.py` owns Qt UI wiring, drag and drop, file dialogs, and user-facing message boxes.
- `settings.py` centralizes supported data extensions, export formats, scale modes, default PNG DPI, and figure size.
- `Dataset.x` and `Dataset.y` are never mutated for log plotting; invalid log points are masked only at draw time.
- Log scale handling is dataset-by-dataset:
  - invalid points are hidden;
  - datasets with no valid points are skipped;
  - scale changes fail only if no dataset has valid points left.
- `PlotScaleWarning` reports hidden points and skipped datasets.
- `PlotScaleError` preserves the previous scale when a requested scale cannot be applied.
- Grid handling must keep the off path free of style kwargs:
  - use `axes.grid(False, which="both")` when disabled;
  - only pass style kwargs when enabling the grid.

## Verification Commands

Run these from the repo root:

```bash
pytest
python3 -m compileall src tests
.venv/bin/python -c "import plotdrop.main_window; print('gui imports ok')"
```

Last known verification:

- `pytest`: 17 tests passed.
- `compileall`: passed.
- GUI import via `.venv/bin/python`: passed.

Matplotlib may warn that `/home/boman/.config/matplotlib` is not writable and create a temporary cache directory under `/tmp`. This warning has not blocked tests or imports.

## Recent User Feedback And Changes

- User tested the app visually with two datasets and `loglog`; plotting worked.
- The dataset list was improved because filenames were too truncated:
  - side panel min/max width added;
  - table height capped;
  - `Points` and `Status` columns fixed width;
  - filename and error message tooltips added.
- A `Grid` checkbox was added.
- A grid toggle bug was fixed: Matplotlib can treat `grid(False, ...)` with style kwargs as grid activation, so disabled grid now passes no style kwargs.

## Good Next Steps

- Consider adding lightweight tests around `PlotWidget` grid/scale behavior if GUI testing becomes acceptable.
- Consider setting `MPLCONFIGDIR` in local development docs or test commands if the Matplotlib cache warning becomes annoying.
- Consider adding a small status bar message for successful exports and file loads.
