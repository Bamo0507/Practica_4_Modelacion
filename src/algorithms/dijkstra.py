"""Búsqueda del recorrido con menor tiempo acumulado."""

from heapq import heappop, heappush
import math

from src.graph import Node

from .common import index_graph, reconstruct_path
from .models import RouteResult


def dijkstra(nodes: list[Node], origin: str, destination: str) -> RouteResult:
    """Encuentra una ruta de tiempo mínimo con conexiones positivas."""
    graph = index_graph(nodes, origin, destination)
    distances = {origin: 0.0}
    parents: dict[str, str] = {}
    pending = [(0.0, origin)]
    visited: list[str] = []

    while pending:
        current_time, current = heappop(pending)
        if current_time != distances[current]:
            continue
        visited.append(current)
        if current == destination:
            return RouteResult(
                reconstruct_path(parents, destination), current_time, visited, "found"
            )

        for connection in graph[current].achievableDestinations:
            neighbor = connection.destinationId
            new_time = current_time + connection.travelTimeMinutes
            if new_time < distances.get(neighbor, math.inf):
                distances[neighbor] = new_time
                parents[neighbor] = current
                heappush(pending, (new_time, neighbor))

    return RouteResult([], None, visited, "unreachable")
