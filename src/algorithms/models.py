"""Resultado compartido por los algoritmos de búsqueda de rutas."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class RouteResult:
    path: list[str]
    totalTimeMinutes: float | None
    visitedNodes: list[str]
    status: Literal["found", "unreachable", "local_minimum"]

    @property
    def found(self) -> bool:
        return self.status == "found"
