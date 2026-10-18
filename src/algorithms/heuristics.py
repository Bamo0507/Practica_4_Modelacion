"""Estimación de tiempo restante sin utilizar coordenadas geográficas."""

from collections import deque
import math

from src.graph import Node


def minimum_hops_heuristic(graph: dict[str, Node], destination: str) -> dict[str, float]:
    """Multiplica el mínimo de tramos restantes por el menor tiempo de la red.

    Un recorrido por niveles desde el destino sobre las conexiones inversas
    obtiene el número mínimo de tramos, respetando la dirección original.
    No calcula tiempos óptimos. La estimación no sobrestima el costo real
    y es consistente para tiempos positivos. El preprocesamiento es O(V+E).
    Se recalcula en cada búsqueda para considerar cambios de la red.
    """
    predecessors: dict[str, list[str]] = {identifier: [] for identifier in graph}
    minimum_time = math.inf
    for origin, node in graph.items():
        for connection in node.achievableDestinations:
            predecessors[connection.destinationId].append(origin)
            minimum_time = min(minimum_time, connection.travelTimeMinutes)

    hops = {destination: 0}
    pending = deque([destination])
    while pending:
        current = pending.popleft()
        for predecessor in predecessors[current]:
            if predecessor not in hops:
                hops[predecessor] = hops[current] + 1
                pending.append(predecessor)

    estimates = {identifier: math.inf for identifier in graph}
    estimates[destination] = 0.0
    for identifier, count in hops.items():
        if count:
            estimates[identifier] = count * minimum_time
    return estimates
