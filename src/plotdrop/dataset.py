from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Dataset:
    path: Path
    name: str
    x: NDArray[np.float64]
    y: NDArray[np.float64]

    @property
    def point_count(self) -> int:
        return int(self.y.size)
