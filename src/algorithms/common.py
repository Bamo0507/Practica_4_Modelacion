"""Validación del grafo y reconstrucción de los recorridos."""

import math

from src.graph import Node


def index_graph(nodes: list[Node], origin: str, destination: str) -> dict[str, Node]:
    graph = {node.identifier: node for node in nodes}
    if len(graph) != len(nodes):
        raise ValueError("El grafo contiene identificadores repetidos.")
    if any(not identifier for identifier in graph):
        raise ValueError("Los identificadores no pueden estar vacíos.")
    for identifier in (origin, destination):
        if identifier not in graph:
            raise ValueError(f"El nodo {identifier!r} no existe en el grafo.")

    for node in nodes:
        destinations: set[str] = set()
        for connection in node.achievableDestinations:
            if connection.destinationId not in graph:
                raise ValueError(
                    f"La conexión desde {node.identifier} apunta a un nodo inexistente."
                )
            if connection.destinationId in destinations:
                raise ValueError(f"El nodo {node.identifier} tiene conexiones repetidas.")
            destinations.add(connection.destinationId)
            if not math.isfinite(connection.travelTimeMinutes) or connection.travelTimeMinutes <= 0:
                raise ValueError("Los tiempos de viaje deben ser positivos y finitos.")
    return graph


def reconstruct_path(parents: dict[str, str], destination: str) -> list[str]:
    path = [destination]
    while path[-1] in parents:
        path.append(parents[path[-1]])
    return path[::-1]
