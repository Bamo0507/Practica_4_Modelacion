"""Pruebas de tiempos, disponibilidad, repetibilidad y comparación."""

from pathlib import Path
import unittest

from src.algorithms import ALGORITHMS
from src.graph import read_graph
from src.simulation import (
    Order, SCENARIOS, Trip, build_routes, changed_graph,
    generate_orders, run_experiment, simulate,
)

MATRIX = Path(__file__).resolve().parents[1] / "data" / "matriz_logistica.csv"


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.routes = {"N08": Trip(("N01", "N08"), ("N08", "N01"), 40, 60)}

    def test_vehicle_remains_busy_until_return(self):
        orders = (Order(1, 0, "N08"), Order(2, 10, "N08"))
        run = simulate(orders, self.routes, 1, 1)
        self.assertEqual([d.departure for d in run.deliveries], [0, 100])
        self.assertEqual([d.delivered for d in run.deliveries], [40, 140])
        self.assertEqual([d.returned for d in run.deliveries], [100, 200])
        self.assertEqual(run.metrics.timely, 1)
        self.assertEqual(run.metrics.averageWait, 45)
        self.assertEqual(run.metrics.averageDelivery, 85)
        self.assertEqual(run.metrics.overtime, 140)
        self.assertEqual(run.metrics.utilizationPercent, 100)

    def test_parallel_vehicles_and_fifo_ties(self):
        orders = (Order(3, 0, "N08"), Order(2, 0, "N08"), Order(1, 0, "N08"))
        run = simulate(orders, self.routes, 2, 1)
        self.assertEqual([d.order.identifier for d in run.deliveries], [1, 2, 3])
        self.assertEqual([d.vehicle for d in run.deliveries], [1, 2, 1])
        self.assertEqual([d.departure for d in run.deliveries], [0, 0, 100])

    def test_deadline_includes_wait_but_not_return(self):
        routes = {"N08": Trip((), (), 75, 100)}
        run = simulate((Order(1, 0, "N08"), Order(2, 1, "N08")), routes, 1, 8)
        self.assertEqual(run.metrics.timely, 1)
        self.assertEqual(run.metrics.timelyPercent, 50)

    def test_utilization_clips_at_close_and_includes_return(self):
        run = simulate((Order(1, 50, "N08"),), self.routes, 2, 1)
        self.assertAlmostEqual(run.metrics.utilizationPercent, 100 * 10 / 120)
        self.assertEqual(run.metrics.overtime, 90)
        self.assertEqual(run.deliveries[0].returned, 150)

    def test_empty_day_has_no_fabricated_averages(self):
        run = simulate((), self.routes, 8, 8)
        self.assertEqual(run.metrics.orders, 0)
        self.assertIsNone(run.metrics.timelyPercent)
        self.assertIsNone(run.metrics.averageWait)
        self.assertIsNone(run.metrics.averageDelivery)
        self.assertEqual(run.metrics.utilizationPercent, 0)
        self.assertEqual(run.metrics.overtime, 0)

    def test_random_arrivals_reproducible_variable_and_within_hours(self):
        orders = generate_orders(10, 8, 42)
        self.assertEqual(orders, generate_orders(10, 8, 42))
        self.assertNotEqual(orders, generate_orders(10, 8, 43))
        self.assertTrue(all(0 <= order.arrival < 480 for order in orders))
        intervals = [right.arrival - left.arrival for left, right in zip(orders, orders[1:])]
        self.assertGreater(len(set(intervals)), 1)
        self.assertEqual(generate_orders(0, 8, 42), ())
        total = sum(len(generate_orders(10, 8, seed)) for seed in range(200)) / 200
        self.assertLess(abs(total - 80), 3)

    def test_routes_from_actual_matrix(self):
        current, proposed = build_routes(read_graph(MATRIX), "Dijkstra")
        self.assertEqual([(t.outboundMinutes, t.inboundMinutes) for t in current.values()],
                         [(59, 59), (33, 33), (42, 42), (93, 93)])
        self.assertEqual([(t.outboundMinutes, t.inboundMinutes) for t in proposed.values()],
                         [(51, 59), (18, 24), (24, 34), (47, 61)])

    def test_pairs_share_exact_orders_for_every_algorithm_season_and_fleet(self):
        nodes = read_graph(MATRIX)
        for algorithm in ALGORITHMS:
            for rate in SCENARIOS.values():
                for vehicles in (8, 10, 12):
                    result = run_experiment(nodes, algorithm, vehicles, rate)
                    self.assertEqual(len(result.repetitions), 5)
                    for repetition in result.repetitions:
                        self.assertEqual(
                            [d.order for d in repetition.current.deliveries],
                            [d.order for d in repetition.proposed.deliveries],
                        )
                        self.assertLessEqual(repetition.proposed.metrics.utilizationPercent, 100)
                    self.assertEqual([r.seed for r in result.repetitions], [42, 43, 44, 45, 46])

    def test_network_edits_do_not_change_original(self):
        nodes = read_graph(MATRIX)
        edited = changed_graph(nodes, ("N01", "N02"), 20)
        self.assertEqual(nodes[0].achievableDestinations[0].travelTimeMinutes, 8)
        self.assertEqual(edited[0].achievableDestinations[0].travelTimeMinutes, 20)
        self.assertIsNot(edited[1], nodes[1])
        closed = changed_graph(nodes, ("N01", "N02"), closed=True)
        with self.assertRaisesRegex(ValueError, "ruta actual"):
            run_experiment(closed, "Dijkstra")
        # Un cierre fuera de la ruta actual sí permite recalcular y comparar.
        result = run_experiment(changed_graph(nodes, ("N02", "N18"), closed=True), "A*")
        self.assertNotEqual(result.proposedRoutes["N19"].outbound, ("N01", "N02", "N18", "N19"))

    def test_invalid_inputs(self):
        for rate, hours, seed in ((-1, 8, 0), (float("nan"), 8, 0), (4, 0, 0), (4, 8, 1.5)):
            with self.subTest(rate=rate, hours=hours, seed=seed), self.assertRaises(ValueError):
                generate_orders(rate, hours, seed)
        for vehicles in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                simulate((), self.routes, vehicles, 8)
        for orders in (
            (Order(1, -1, "N08"),), (Order(1, 60, "N08"),),
            (Order(1, 0, "N19"),), (Order(1, 0, "N08"), Order(1, 1, "N08")),
        ):
            with self.assertRaises(ValueError):
                simulate(orders, self.routes, 1, 1)
        for kwargs in ({"vehicles": 9}, {"repetitions": 4}):
            with self.assertRaises(ValueError):
                run_experiment(read_graph(MATRIX), "Dijkstra", **kwargs)
        with self.assertRaises(ValueError):
            changed_graph(read_graph(MATRIX), ("N01", "N40"), 10)
