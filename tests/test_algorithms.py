"""Validación de rutas, optimalidad y cambios de red."""

from copy import deepcopy
import math
from pathlib import Path
import random
import unittest

from src.algorithms import ALGORITHMS, a_star, dijkstra, find_route, hill_climbing
from src.algorithms.heuristics import minimum_hops_heuristic
from src.graph import Connection, Node, read_graph


def reference_distances(nodes: list[Node]) -> dict[tuple[str, str], float]:
    """Referencia independiente de tiempos mínimos mediante Floyd-Warshall."""
    identifiers = [node.identifier for node in nodes]
    distances = {
        (origin, destination): 0.0 if origin == destination else math.inf
        for origin in identifiers
        for destination in identifiers
    }
    for node in nodes:
        for connection in node.achievableDestinations:
            key = (node.identifier, connection.destinationId)
            distances[key] = min(distances[key], connection.travelTimeMinutes)
    for intermediate in identifiers:
        for origin in identifiers:
            for destination in identifiers:
                distances[origin, destination] = min(
                    distances[origin, destination],
                    distances[origin, intermediate] + distances[intermediate, destination],
                )
    return distances


class AlgorithmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "data" / "matriz_logistica.csv"
        cls.network = read_graph(path)
        cls.distances = reference_distances(cls.network)

    def assert_valid_route(self, nodes, result, origin, destination):
        self.assertTrue(result.found)
        self.assertEqual(result.path[0], origin)
        self.assertEqual(result.path[-1], destination)
        self.assertEqual(len(result.path), len(set(result.path)))
        connections = {
            (node.identifier, edge.destinationId): edge.travelTimeMinutes
            for node in nodes
            for edge in node.achievableDestinations
        }
        cost = 0.0
        for edge in zip(result.path, result.path[1:]):
            self.assertIn(edge, connections)
            cost += connections[edge]
        self.assertAlmostEqual(cost, result.totalTimeMinutes)

    def assert_algorithms_match_reference(self, nodes, distances):
        for origin in nodes:
            for destination in nodes:
                key = (origin.identifier, destination.identifier)
                for name, algorithm in ALGORITHMS.items():
                    with self.subTest(algorithm=name, route=key):
                        result = algorithm(nodes, *key)
                        if math.isinf(distances[key]):
                            self.assertFalse(result.found)
                            self.assertEqual(result.status, "unreachable")
                            self.assertEqual(result.path, [])
                            self.assertIsNone(result.totalTimeMinutes)
                        else:
                            self.assert_valid_route(nodes, result, *key)
                            if name != "Hill Climbing":
                                self.assertAlmostEqual(result.totalTimeMinutes, distances[key])
                            else:
                                self.assertGreaterEqual(result.totalTimeMinutes, distances[key])

    def test_all_pairs_of_real_network(self):
        self.assert_algorithms_match_reference(self.network, self.distances)

    def test_small_random_directed_networks(self):
        generator = random.Random(2026)
        for _ in range(5):
            nodes = [Node(str(index)) for index in range(6)]
            for origin in nodes:
                for destination in nodes:
                    if origin != destination and generator.random() < 0.3:
                        origin.achievableDestinations.append(
                            Connection(destination.identifier, generator.randint(1, 30) / 2)
                        )
            self.assert_algorithms_match_reference(nodes, reference_distances(nodes))

    def test_hill_climbing_can_return_a_slower_route(self):
        nodes = [
            Node("S", [Connection("A", 1), Connection("B", 1)]),
            Node("A", [Connection("G", 100)]),
            Node("B", [Connection("C", 1)]),
            Node("C", [Connection("G", 1)]),
            Node("G"),
        ]
        for algorithm in (dijkstra, a_star):
            result = algorithm(nodes, "S", "G")
            self.assertEqual(result.path, ["S", "B", "C", "G"])
            self.assertEqual(result.totalTimeMinutes, 3)
        result = hill_climbing(nodes, "S", "G")
        self.assertEqual(result.path, ["S", "A", "G"])
        self.assertEqual(result.totalTimeMinutes, 101)

    def test_heuristic_is_admissible_and_consistent(self):
        graph = {node.identifier: node for node in self.network}
        for destination in graph:
            estimates = minimum_hops_heuristic(graph, destination)
            self.assertEqual(estimates[destination], 0)
            for origin, node in graph.items():
                self.assertLessEqual(estimates[origin], self.distances[origin, destination])
                for connection in node.achievableDestinations:
                    self.assertLessEqual(
                        estimates[origin],
                        connection.travelTimeMinutes + estimates[connection.destinationId],
                    )

    def test_edits_and_closures_recompute_routes(self):
        nodes = [
            Node("A", [Connection("B", 1), Connection("C", 5)]),
            Node("B", [Connection("C", 1)]),
            Node("C"),
        ]
        for algorithm in (dijkstra, a_star):
            self.assertEqual(algorithm(nodes, "A", "C").totalTimeMinutes, 2)
        nodes[0].achievableDestinations[0].travelTimeMinutes = 10
        for algorithm in ALGORITHMS.values():
            self.assertEqual(algorithm(nodes, "A", "C").path, ["A", "C"])
        nodes[0].achievableDestinations.pop()
        for algorithm in ALGORITHMS.values():
            self.assertEqual(algorithm(nodes, "A", "C").totalTimeMinutes, 11)
        nodes[1].achievableDestinations.clear()
        for algorithm in ALGORITHMS.values():
            self.assertEqual(algorithm(nodes, "A", "C").status, "unreachable")

    def test_search_does_not_mutate_graph(self):
        original = deepcopy(self.network)
        for algorithm in ALGORITHMS.values():
            algorithm(self.network, "N01", "N40")
        self.assertEqual(self.network, original)

    def test_ties_do_not_depend_on_input_order(self):
        nodes = [
            Node("S", [Connection("B", 2), Connection("A", 2)]),
            Node("A", [Connection("G", 2)]),
            Node("B", [Connection("G", 2)]),
            Node("G"),
        ]
        reordered = deepcopy(nodes[::-1])
        for node in reordered:
            node.achievableDestinations.reverse()
        for algorithm in ALGORITHMS.values():
            self.assertEqual(algorithm(nodes, "S", "G"), algorithm(reordered, "S", "G"))

    def test_single_node(self):
        for algorithm in ALGORITHMS.values():
            result = algorithm([Node("A")], "A", "A")
            self.assertEqual(result.path, ["A"])
            self.assertEqual(result.totalTimeMinutes, 0)
            self.assertEqual(result.visitedNodes, ["A"])

    def test_invalid_graphs_are_rejected(self):
        cases = [
            [Node("A"), Node("A")],
            [Node("")],
            [Node("A", [Connection("B", 1)])],
            [Node("A", [Connection("A", 1), Connection("A", 2)])],
        ]
        for value in (-1, 0, math.inf, math.nan):
            cases.append([Node("A", [Connection("A", value)])])
        for nodes in cases:
            for algorithm in ALGORITHMS.values():
                with self.subTest(nodes=nodes, algorithm=algorithm.__name__):
                    with self.assertRaises(ValueError):
                        algorithm(nodes, "A", "A")

    def test_unknown_node_is_not_reported_as_unreachable(self):
        for algorithm in ALGORITHMS.values():
            with self.assertRaises(ValueError):
                algorithm([Node("A")], "A", "B")

    def test_registry_dispatches_and_rejects_unknown_algorithm(self):
        for name, algorithm in ALGORITHMS.items():
            self.assertEqual(
                find_route(name, self.network, "N01", "N08"),
                algorithm(self.network, "N01", "N08"),
            )
        with self.assertRaises(ValueError):
            find_route("Desconocido", self.network, "N01", "N08")
