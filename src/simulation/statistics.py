"""Resumen de tiempos individuales, sin promediar estadísticas de jornadas."""

from collections.abc import Iterable
from math import isfinite
from statistics import mean, median

from .models import TimeStatistics


def summarize_times(values: Iterable[float]) -> TimeStatistics:
    samples = list(values)
    if any(not isfinite(value) or value < 0 for value in samples):
        raise ValueError("Los tiempos deben ser finitos y mayores o iguales a cero.")
    if not samples:
        return TimeStatistics(None, None, None, None)
    return TimeStatistics(mean(samples), median(samples), min(samples), max(samples))
