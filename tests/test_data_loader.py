from __future__ import annotations

import numpy as np
import pytest

from plotdrop.data_loader import DataLoadError, load_dataset


def write_data(tmp_path, name: str, content: str):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_two_space_separated_columns(tmp_path):
    path = write_data(tmp_path, "data.dat", "0 1\n1 2\n2 3\n")

    dataset = load_dataset(path)

    np.testing.assert_allclose(dataset.x, [0, 1, 2])
    np.testing.assert_allclose(dataset.y, [1, 2, 3])
    assert dataset.name == "data.dat"
    assert dataset.point_count == 3


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("data.csv", "0,1\n1,2\n"),
        ("data.dat", "0;1\n1;2\n"),
        ("data.tsv", "0\t1\n1\t2\n"),
    ],
)
def test_loads_supported_separators(tmp_path, name, content):
    path = write_data(tmp_path, name, content)

    dataset = load_dataset(path)

    np.testing.assert_allclose(dataset.x, [0, 1])
    np.testing.assert_allclose(dataset.y, [1, 2])


def test_ignores_empty_lines_and_comments(tmp_path):
    path = write_data(
        tmp_path,
        "data.txt",
        "\n# header comment\n\n0 1\n# middle comment\n1 2\n",
    )

    dataset = load_dataset(path)

    np.testing.assert_allclose(dataset.x, [0, 1])
    np.testing.assert_allclose(dataset.y, [1, 2])


def test_ignores_inline_comments_after_numeric_values(tmp_path):
    path = write_data(tmp_path, "data.txt", "0 1 # first point\n1 2 # second point\n")

    dataset = load_dataset(path)

    np.testing.assert_allclose(dataset.x, [0, 1])
    np.testing.assert_allclose(dataset.y, [1, 2])


def test_one_column_uses_index_as_x(tmp_path):
    path = write_data(tmp_path, "data.txt", "10\n20\n30\n")

    dataset = load_dataset(path)

    np.testing.assert_allclose(dataset.x, [0, 1, 2])
    np.testing.assert_allclose(dataset.y, [10, 20, 30])


def test_more_than_two_columns_uses_first_two(tmp_path):
    path = write_data(tmp_path, "data.txt", "0 1 100\n1 2 200\n")

    dataset = load_dataset(path)

    np.testing.assert_allclose(dataset.x, [0, 1])
    np.testing.assert_allclose(dataset.y, [1, 2])


def test_tolerates_one_header_line_before_data(tmp_path):
    path = write_data(tmp_path, "data.csv", "time,value\n0,1\n1,2\n")

    dataset = load_dataset(path)

    np.testing.assert_allclose(dataset.x, [0, 1])
    np.testing.assert_allclose(dataset.y, [1, 2])


def test_non_numeric_line_after_data_fails(tmp_path):
    path = write_data(tmp_path, "data.txt", "0 1\nbad line\n1 2\n")

    with pytest.raises(DataLoadError, match="Line 2"):
        load_dataset(path)


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_rejects_non_finite_values(tmp_path, value):
    path = write_data(tmp_path, "data.txt", f"0 1\n1 {value}\n")

    with pytest.raises(DataLoadError, match="Non-finite"):
        load_dataset(path)


def test_rejects_unsupported_extension(tmp_path):
    path = write_data(tmp_path, "data.json", "0 1\n")

    with pytest.raises(DataLoadError, match="Unsupported file extension"):
        load_dataset(path)


def test_rejects_empty_or_comment_only_file(tmp_path):
    path = write_data(tmp_path, "data.txt", "\n# only comments\n")

    with pytest.raises(DataLoadError, match="does not contain usable numeric data"):
        load_dataset(path)


def test_rejects_valid_extension_with_invalid_content(tmp_path):
    path = write_data(tmp_path, "data.csv", "not,data\nstill,bad\n")

    with pytest.raises(DataLoadError, match="Line 2"):
        load_dataset(path)


def test_rejects_inconsistent_column_counts(tmp_path):
    path = write_data(tmp_path, "data.txt", "0 1\n2\n")

    with pytest.raises(DataLoadError, match="inconsistent column counts"):
        load_dataset(path)
