"""Búsqueda de un camino simple que no repita los recorridos indicados."""

from collections.abc import Collection

from src.graph import Node

from .common import index_graph
from .dijkstra import dijkstra


def find_distinct_path(
    nodes: list[Node], origin: str, destination: str,
    excluded: Collection[tuple[str, ...]],
) -> tuple[str, ...] | None:
    """Reutiliza Dijkstra para explorar desvíos, sin modificar la red original."""
    index_graph(nodes, origin, destination)
    weights = {(node.identifier, c.destinationId): c.travelTimeMinutes
               for node in nodes for c in node.achievableDestinations}
    forbidden = {tuple(path) for path in excluded}
    for path in forbidden:
        if (not path or path[0] != origin or path[-1] != destination
                or len(path) != len(set(path))
                or any(arc not in weights for arc in zip(path, path[1:]))):
            raise ValueError("Los recorridos excluidos deben ser caminos simples válidos del mismo origen y destino.")

    shortest = dijkstra(nodes, origin, destination)
    if not shortest.found:
        return None
    if tuple(shortest.path) not in forbidden:
        return tuple(shortest.path)

    prefixes = {path[:length] for path in forbidden for length in range(1, len(path))}
    candidates: set[tuple[str, ...]] = set()
    for prefix in sorted(prefixes):
        blocked_nodes = set(prefix[:-1])
        # Se descartan todas las continuaciones conocidas que comparten este prefijo.
        blocked_edges = {
            (prefix[-1], path[len(prefix)]) for path in forbidden
            if len(path) > len(prefix) and path[:len(prefix)] == prefix
        }
        query_nodes = [
            Node(node.identifier, [
                connection for connection in node.achievableDestinations
                if connection.destinationId not in blocked_nodes
                and (node.identifier, connection.destinationId) not in blocked_edges
            ]) for node in nodes if node.identifier not in blocked_nodes
        ]
        suffix = dijkstra(query_nodes, prefix[-1], destination)
        if suffix.found:
            candidates.add(prefix[:-1] + tuple(suffix.path))

    if not candidates:
        return None
    return min(candidates, key=lambda path: (
        sum(weights[arc] for arc in zip(path, path[1:])), path,
    ))
