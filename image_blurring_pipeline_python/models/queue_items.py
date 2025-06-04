from dataclasses import dataclass
from abc import ABC
from typing import Tuple

import numpy as np


@dataclass
class _BaseQueueItem(ABC):
    frame: np.ndarray
    frame_id: int
    timestamp_ms: int


@dataclass
class InputItem(_BaseQueueItem):
    pass


@dataclass
class OutputItem(_BaseQueueItem):
    contours: Tuple[np.ndarray]
