"""Algoritmos de rutas disponibles para la aplicación."""

from collections.abc import Callable

from src.graph import Node

from .a_star import a_star
from .alternatives import find_distinct_path
from .dijkstra import dijkstra
from .hill_climbing import hill_climbing
from .models import RouteResult

ALGORITHMS: dict[str, Callable[[list[Node], str, str], RouteResult]] = {
    "Dijkstra": dijkstra,
    "A*": a_star,
    "Hill Climbing": hill_climbing,
}


def find_route(
    algorithm: str, nodes: list[Node], origin: str, destination: str
) -> RouteResult:
    """Ejecuta el algoritmo seleccionado con un resultado común."""
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Algoritmo desconocido: {algorithm!r}.")
    return ALGORITHMS[algorithm](nodes, origin, destination)


__all__ = ["ALGORITHMS", "RouteResult", "a_star", "dijkstra", "find_distinct_path", "find_route", "hill_climbing"]
