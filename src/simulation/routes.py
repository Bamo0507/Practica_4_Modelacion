"""Recorridos actuales y construcción independiente de ida y regreso."""

from math import isfinite

from src.algorithms import find_route
from src.algorithms.common import index_graph
from src.graph import Connection, Node

from .models import Trip

DEPOT = "N01"
DESTINATIONS = ("N08", "N19", "N34", "N40")
VEHICLE_COUNTS = (8, 10, 12)
SCENARIOS = {"Normal": 4, "Semana Santa": 6, "Navidad": 10}
CURRENT_PATHS = {
    "N08": ("N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08"),
    "N19": ("N01", "N02", "N03", "N11", "N19"),
    "N34": ("N01", "N09", "N17", "N25", "N33", "N34"),
    "N40": ("N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08",
            "N16", "N24", "N32", "N40"),
}


def changed_graph(
    nodes: list[Node], edge: tuple[str, str] | None = None,
    minutes: float | None = None, closed: bool = False,
) -> list[Node]:
    """Devuelve una copia; un cambio afecta únicamente el sentido indicado."""
    if edge is not None and not any(
        node.identifier == edge[0] and connection.destinationId == edge[1]
        for node in nodes for connection in node.achievableDestinations
    ):
        raise ValueError("La conexión seleccionada no existe en la matriz.")
    if minutes is not None and (not isfinite(minutes) or minutes <= 0):
        raise ValueError("El tiempo de la conexión debe ser positivo y finito.")
    result = []
    for node in nodes:
        connections = []
        for connection in node.achievableDestinations:
            selected = edge == (node.identifier, connection.destinationId)
            if selected and closed:
                continue
            travel = minutes if selected and minutes is not None else connection.travelTimeMinutes
            connections.append(Connection(connection.destinationId, travel))
        result.append(Node(node.identifier, connections))
    return result


def build_routes(nodes: list[Node], algorithm: str) -> tuple[dict[str, Trip], dict[str, Trip]]:
    graph = index_graph(nodes, DEPOT, DESTINATIONS[0])

    def cost(path: tuple[str, ...]) -> float:
        total = 0.0
        for source, target in zip(path, path[1:]):
            connection = next((c for c in graph[source].achievableDestinations
                               if c.destinationId == target), None)
            if connection is None:
                raise ValueError(
                    f"La ruta actual necesita {source} -> {target}, pero está cerrado. "
                    "Retira ese cierre para comparar ambas políticas."
                )
            total += connection.travelTimeMinutes
        return total

    current, proposed = {}, {}
    for destination, path in CURRENT_PATHS.items():
        reverse = tuple(reversed(path))
        current[destination] = Trip(path, reverse, cost(path), cost(reverse))
        outward = find_route(algorithm, nodes, DEPOT, destination)
        inward = find_route(algorithm, nodes, destination, DEPOT)
        if not outward.found or not inward.found:
            raise ValueError(f"No existe una ruta completa de ida y regreso para {destination}.")
        proposed[destination] = Trip(
            tuple(outward.path), tuple(inward.path),
            outward.totalTimeMinutes, inward.totalTimeMinutes,
        )
    return current, proposed
