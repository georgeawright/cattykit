"""Optional numerical precision policies for model-defined quantities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, overload

import numpy as np
from numpy.typing import NDArray


class PrecisionPolicy(Protocol):
    """Quantize a scalar or floating-point array at a model-defined boundary."""

    @overload
    def quantize(self, value: float) -> float:
        ...

    @overload
    def quantize(self, value: NDArray) -> NDArray:
        ...


@dataclass(frozen=True, slots=True)
class FullPrecision:
    """Leave values unchanged."""

    def quantize(self, value):
        return value


@dataclass(frozen=True, slots=True)
class DecimalPlaces:
    """Round to decimal places using NumPy's nearest, ties-to-even rule."""

    places: int

    def __post_init__(self):
        if (
            isinstance(self.places, bool)
            or not isinstance(self.places, int)
            or self.places < 0
        ):
            raise ValueError("places must be a non-negative integer")

    def quantize(self, value):
        result = np.round(value, self.places)
        return result if isinstance(value, np.ndarray) else float(result)
