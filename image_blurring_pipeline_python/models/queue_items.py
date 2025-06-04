from dataclasses import dataclass, field, fields
from abc import ABC
from typing import Tuple

import numpy as np


@dataclass
class _BaseQueueItem(ABC):
    frame: np.ndarray
    frame_id: int
    timestamp_ms: int
    _terminate: bool = field(default=False, init=False, repr=False, compare=False)

    @classmethod
    def termination(cls):
        instance = cls(**{f.name: None for f in fields(cls) if f.init})
        instance._terminate = True
        return instance

    def set_termination(self):
        self._terminate = True

    @property
    def is_termination(self) -> bool:
        return self._terminate

@dataclass
class InputItem(_BaseQueueItem):
    pass


@dataclass
class OutputItem(_BaseQueueItem):
    contours: Tuple[np.ndarray]
