"""Temporarily quantize Copycat's normalized numeric state to percentages.

This is an ablation experiment: the installed Copycat package is patched only
while the experiment runs.  A value such as ``0.376`` is represented as
``0.38`` (the equivalent of an integer score of 38 on Copycat's 0--100 scale).
The patch quantizes persistent floating-point state, NumPy activation arrays,
and values used as probabilities or weighted-selection weights.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from types import ModuleType
from typing import Any

import numpy as np
from copycat import tools


def quantize(value: object, decimals: int = 2) -> object:
    """Round floats and floating NumPy arrays, leaving discrete values intact."""
    if isinstance(value, float | np.floating):
        return round(float(value), decimals)
    if isinstance(value, np.ndarray) and np.issubdtype(value.dtype, np.floating):
        return np.round(value, decimals)
    if isinstance(value, list):
        return [quantize(item, decimals) for item in value]
    if isinstance(value, tuple):
        return tuple(quantize(item, decimals) for item in value)
    return value


def _quantized_setattr(
    decimals: int, original: Callable[..., None]
) -> Callable[..., None]:
    @wraps(original)
    def patched(self: object, name: str, value: object) -> None:
        original(self, name, quantize(value, decimals))

    return patched


def _quantized_function(
    decimals: int, original: Callable[..., Any]
) -> Callable[..., Any]:
    @wraps(original)
    def patched(*args: object, **kwargs: object) -> Any:
        return quantize(original(*args, **kwargs), decimals)

    return patched


def _quantized_selection(
    decimals: int, original: Callable[..., Any]
) -> Callable[..., Any]:
    """Round sampling weights before Python's random module consumes them."""
    @wraps(original)
    def patched(items: object, weights: object, k: object) -> Any:
        return original(items, quantize(weights, decimals), k)

    return patched


def _copycat_modules() -> Iterator[ModuleType]:
    """Yield loaded Copycat modules, including modules with imported helpers."""
    for name, module in tuple(sys.modules.items()):
        if name == "copycat" or name.startswith("copycat."):
            if module is not None:
                yield module


@contextmanager
def quantized_copycat(decimals: int = 2) -> Iterator[None]:
    """Temporarily quantize Copycat's numeric state and stochastic inputs.

    Copycat imports selection helpers into many modules.  Replacing each loaded
    reference ensures probabilities are rounded immediately before comparisons
    with the random stream, rather than merely when values are logged.
    """
    if decimals < 0:
        raise ValueError("decimals must not be negative")
    changes: list[tuple[object, str, object, bool]] = []

    def replace(owner: object, name: str, replacement: object) -> None:
        owner_dict = vars(owner)
        changes.append((owner, name, getattr(owner, name), name in owner_dict))
        setattr(owner, name, replacement)

    # Quantize every float assigned to a Copycat-domain object.  This includes
    # strengths, salience, temperature, Slipnode fields, and NumPy activations.
    classes: set[type[object]] = set()
    for module in _copycat_modules():
        classes.update(
            value
            for value in vars(module).values()
            if isinstance(value, type) and value.__module__.startswith("copycat")
        )
    for class_ in classes:
        replace(class_, "__setattr__", _quantized_setattr(decimals, class_.__setattr__))

    # Quantize direct probability calculations and all weighted choices.  The
    # replacement is installed at every module-level imported reference.
    probability = tools.temperature_adjust_probability
    adjusted_value = tools.temperature_adjust
    adjusted_values = tools.temperature_adjust_list
    selection = tools.select_items_from_list
    for module in _copycat_modules():
        for name, value in tuple(vars(module).items()):
            if value is probability:
                replace(module, name, _quantized_function(decimals, probability))
            elif value is adjusted_value:
                replace(module, name, _quantized_function(decimals, adjusted_value))
            elif value is adjusted_values:
                replace(module, name, _quantized_function(decimals, adjusted_values))
            elif value is selection:
                replace(module, name, _quantized_selection(decimals, selection))
    try:
        yield
    finally:
        for owner, name, original, was_defined in reversed(changes):
            if was_defined:
                setattr(owner, name, original)
            else:
                delattr(owner, name)


