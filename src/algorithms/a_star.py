"""Búsqueda guiada por tiempo acumulado y estimación de tiempo restante."""

from heapq import heappop, heappush
import math

from src.graph import Node

from .common import index_graph, reconstruct_path
from .heuristics import minimum_hops_heuristic
from .models import RouteResult


def a_star(nodes: list[Node], origin: str, destination: str) -> RouteResult:
    """Encuentra una ruta óptima usando una estimación consistente en minutos."""
    graph = index_graph(nodes, origin, destination)
    estimates = minimum_hops_heuristic(graph, destination)
    if math.isinf(estimates[origin]):
        return RouteResult([], None, [], "unreachable")

    distances = {origin: 0.0}
    parents: dict[str, str] = {}
    pending = [(estimates[origin], 0.0, origin)]
    visited: list[str] = []

    while pending:
        _, current_time, current = heappop(pending)
        if current_time != distances[current]:
            continue
        visited.append(current)
        if current == destination:
            return RouteResult(
                reconstruct_path(parents, destination), current_time, visited, "found"
            )

        for connection in graph[current].achievableDestinations:
            neighbor = connection.destinationId
            if math.isinf(estimates[neighbor]):
                continue
            new_time = current_time + connection.travelTimeMinutes
            if new_time < distances.get(neighbor, math.inf):
                distances[neighbor] = new_time
                parents[neighbor] = current
                heappush(pending, (new_time + estimates[neighbor], new_time, neighbor))

    return RouteResult([], None, visited, "unreachable")
