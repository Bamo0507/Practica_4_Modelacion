"""Alternativas distintas, costos contrastados y ausencia de cambios a la red."""

from copy import deepcopy
from pathlib import Path
from random import Random
import unittest

from src.algorithms import ALGORITHMS, find_distinct_path
from src.graph import Connection, Node, read_graph
from src.simulation import (
    Experiment, Repetition, Trip, build_additional_routes, build_routes,
    changed_graph, run_experiment, simulate,
)

MATRIX = Path(__file__).resolve().parents[1] / "data" / "matriz_logistica.csv"


def all_simple_paths(nodes, origin, destination):
    graph = {node.identifier: node.achievableDestinations for node in nodes}
    pending = [(0, (origin,))]
    paths = {}
    while pending:
        cost, path = pending.pop()
        if path[-1] == destination:
            paths[path] = cost
            continue
        for connection in graph[path[-1]]:
            if connection.destinationId not in path:
                pending.append((cost + connection.travelTimeMinutes, path + (connection.destinationId,)))
    return paths


class RouteAlternativesTests(unittest.TestCase):
    def test_approved_routes_are_reproduced_from_the_matrix(self):
        result = run_experiment(read_graph(MATRIX), "Dijkstra")
        expected = {
            "N08": (("N01", "N02", "N03", "N12", "N05", "N06", "N07", "N08"), 57, 59),
            "N19": (("N01", "N17", "N18", "N19"), 20, 24),
            "N34": (("N01", "N02", "N18", "N26", "N34"), 24, 34),
            "N40": (("N01", "N17", "N25", "N27", "N29", "N31", "N39", "N40"), 51, 61),
        }
        for destination, (path, out, back) in expected.items():
            trip = result.additionalRoutes[destination].trip
            self.assertEqual(trip.outbound, path)
            self.assertEqual((trip.outboundMinutes, trip.inboundMinutes), (out, back))
        self.assertEqual(result.additionalRoutes["N08"].source, "Hill Climbing")
        self.assertEqual(result.additionalRoutes["N34"].trip.outboundMinutes,
                         result.proposedRoutes["N34"].outboundMinutes)

    def test_three_options_have_distinct_outbound_paths_for_every_selected_algorithm(self):
        nodes = read_graph(MATRIX)
        weights = {(node.identifier, c.destinationId): c.travelTimeMinutes
                   for node in nodes for c in node.achievableDestinations}
        for algorithm in ALGORITHMS:
            result = run_experiment(nodes, algorithm)
            for destination, option in result.additionalRoutes.items():
                with self.subTest(algorithm=algorithm, destination=destination):
                    trips = (result.currentRoutes[destination], result.proposedRoutes[destination], option.trip)
                    self.assertEqual(len({trip.outbound for trip in trips}), 3)
                    for trip in trips:
                        for path, cost in ((trip.outbound, trip.outboundMinutes),
                                           (trip.inbound, trip.inboundMinutes)):
                            self.assertEqual(len(path), len(set(path)))
                            self.assertEqual(sum(weights[arc] for arc in zip(path, path[1:])), cost)

    def test_closed_or_changed_connections_recompute_the_additional_route(self):
        nodes = read_graph(MATRIX)
        before = deepcopy(nodes)
        original = run_experiment(nodes, "Dijkstra")
        closed = run_experiment(changed_graph(nodes, ("N31", "N39"), closed=True), "Dijkstra")
        modified = run_experiment(changed_graph(nodes, ("N31", "N39"), 50), "Dijkstra")
        for result in (closed, modified):
            trip = result.additionalRoutes["N40"].trip
            self.assertNotEqual(trip.outbound, original.additionalRoutes["N40"].trip.outbound)
            self.assertNotIn(("N31", "N39"), set(zip(trip.outbound, trip.outbound[1:])))
            self.assertEqual(trip.outboundMinutes, 54)
        self.assertEqual(nodes, before)

    def test_fallback_matches_exhaustive_simple_paths_on_small_directed_graphs(self):
        random = Random(23)
        for case in range(40):
            identifiers = [str(index) for index in range(6)]
            nodes = [Node(source, [Connection(target, random.randint(1, 9))
                                  for target in identifiers if source != target and random.random() < 0.4])
                     for source in identifiers]
            paths = all_simple_paths(nodes, "0", "5")
            ranked = sorted(paths, key=lambda path: (paths[path], path))
            excluded_sets = [(), tuple(ranked[:1]), tuple(ranked[:2]), tuple(ranked[::2])]
            before = deepcopy(nodes)
            for excluded in excluded_sets:
                with self.subTest(case=case, excluded=len(excluded)):
                    found = find_distinct_path(nodes, "0", "5", excluded)
                    allowed = {path: cost for path, cost in paths.items() if path not in excluded}
                    if not allowed:
                        self.assertIsNone(found)
                    else:
                        self.assertIn(found, allowed)
                        self.assertEqual(allowed[found], min(allowed.values()))
            self.assertEqual(nodes, before)

    def test_cycles_do_not_fabricate_an_alternative(self):
        nodes = [Node("A", [Connection("B", 1)]),
                 Node("B", [Connection("A", 1), Connection("C", 1)]), Node("C")]
        self.assertIsNone(find_distinct_path(nodes, "A", "C", [("A", "B", "C")]))
        self.assertEqual(find_distinct_path(nodes, "A", "A", []), ("A",))
        self.assertIsNone(find_distinct_path(nodes, "A", "A", [("A",)]))

    def test_unreachable_target_returns_none(self):
        self.assertIsNone(find_distinct_path([Node("A"), Node("B")], "A", "B", []))

    def test_invalid_excluded_paths_are_rejected(self):
        nodes = [Node("A", [Connection("B", 1)]), Node("B", [Connection("A", 1)])]
        for path in ((), ("B", "A"), ("A", "C", "B"), ("A", "B", "A", "B")):
            with self.subTest(path=path), self.assertRaises(ValueError):
                find_distinct_path(nodes, "A", "B", [path])

    def test_search_is_independent_of_node_order(self):
        nodes = read_graph(MATRIX)
        current, proposed = build_routes(nodes, "Dijkstra")
        expected = build_additional_routes(nodes, current, proposed)
        reversed_nodes = [Node(node.identifier, list(reversed(node.achievableDestinations)))
                          for node in reversed(nodes)]
        self.assertEqual(build_additional_routes(reversed_nodes, current, proposed), expected)

    def test_missing_second_path_is_explicit_not_a_duplicate(self):
        destinations = ("N08", "N19", "N34", "N40")
        nodes = [Node("N01", [Connection(destination, 5) for destination in destinations])]
        nodes.extend(Node(destination, [Connection("N01", 5)]) for destination in destinations)
        only_routes = {destination: Trip(("N01", destination), (destination, "N01"), 5, 5)
                       for destination in destinations}
        options = build_additional_routes(nodes, only_routes, only_routes)
        self.assertTrue(all(option.trip is None for option in options.values()))
        from src.ui.results import render_results

        empty = simulate((), only_routes, 8, 8)
        result = Experiment("Dijkstra", 8, 0, 8, only_routes, only_routes,
                            (Repetition(42, empty, empty),), options)
        view = str(render_results(result, "Normal"))
        self.assertIn("Sin otra ida válida", view)
        self.assertIn("misma ida actual", view)
