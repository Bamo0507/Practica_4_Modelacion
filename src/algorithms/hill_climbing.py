"""Búsqueda local que disminuye la estimación de tiempo restante."""

import math

from src.graph import Node

from .common import index_graph
from .heuristics import minimum_hops_heuristic
from .models import RouteResult


def hill_climbing(nodes: list[Node], origin: str, destination: str) -> RouteResult:
    """Elige el mejor vecino local sin retroceso ni garantía de tiempo mínimo.

    Se minimiza h(n), equivalente a maximizar -h(n). En empates se elige
    el tramo más rápido y después el identificador del destino. Con la
    heurística por tramos existe un vecino de menor h para cada nodo que
    alcanza la meta; eso evita estancamientos en esta variante concreta.
    La ruta puede ser más lenta que la encontrada por Dijkstra o A*.
    """
    graph = index_graph(nodes, origin, destination)
    estimates = minimum_hops_heuristic(graph, destination)
    if math.isinf(estimates[origin]):
        return RouteResult([], None, [], "unreachable")

    current = origin
    path = [origin]
    total_time = 0.0
    while current != destination:
        connections = graph[current].achievableDestinations
        if not connections:
            return RouteResult([], None, path.copy(), "local_minimum")
        best = min(
            connections,
            key=lambda connection: (
                estimates[connection.destinationId],
                connection.travelTimeMinutes,
                connection.destinationId,
            ),
        )
        if estimates[best.destinationId] >= estimates[current]:
            return RouteResult([], None, path.copy(), "local_minimum")

        total_time += best.travelTimeMinutes
        current = best.destinationId
        path.append(current)

    return RouteResult(path, total_time, path.copy(), "found")
