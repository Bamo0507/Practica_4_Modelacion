"""Alternativas de validación, independientes de las dos políticas simuladas."""

from src.algorithms import find_distinct_path, find_route
from src.graph import Node

from .models import AlternativeRoute, Trip
from .routes import DEPOT


def build_additional_routes(
    nodes: list[Node], current: dict[str, Trip], proposed: dict[str, Trip],
) -> dict[str, AlternativeRoute]:
    weights = {(node.identifier, c.destinationId): c.travelTimeMinutes
               for node in nodes for c in node.achievableDestinations}
    additional = {}
    for destination, selected in proposed.items():
        excluded = {current[destination].outbound, selected.outbound}
        outward, source = None, "Búsqueda por desvíos"
        for algorithm in ("Hill Climbing", "Dijkstra"):
            candidate = find_route(algorithm, nodes, DEPOT, destination)
            if candidate.found and tuple(candidate.path) not in excluded:
                outward, source = tuple(candidate.path), algorithm
                break
        if outward is None:
            outward = find_distinct_path(nodes, DEPOT, destination, excluded)
        inward = find_route("Dijkstra", nodes, destination, DEPOT)
        if outward is None or not inward.found:
            additional[destination] = AlternativeRoute(source, None)
            continue
        back = tuple(inward.path)
        # La valoración final siempre consulta la red recibida, no la copia de búsqueda.
        trip = Trip(
            outward, back,
            sum(weights[arc] for arc in zip(outward, outward[1:])),
            sum(weights[arc] for arc in zip(back, back[1:])),
        )
        additional[destination] = AlternativeRoute(source, trip)
    return additional
