"""Estadísticas de pedidos y cálculo conjunto con jornadas de distinto tamaño."""

from statistics import mean
import unittest

from src.simulation import Experiment, Order, Repetition, TimeStatistics, Trip, simulate, summarize_times
from src.ui.results import aggregate


class TimeStatisticsTests(unittest.TestCase):
    def test_empty_samples_have_no_fabricated_values(self):
        self.assertEqual(summarize_times([]), TimeStatistics(None, None, None, None))

    def test_zero_is_an_observation_not_missing_data(self):
        self.assertEqual(summarize_times([0, 0]), TimeStatistics(0, 0, 0, 0))

    def test_single_observation(self):
        self.assertEqual(summarize_times([12.5]), TimeStatistics(12.5, 12.5, 12.5, 12.5))

    def test_odd_median_is_the_sorted_middle_observation(self):
        samples = [100, 1, 20]
        result = summarize_times(samples)
        self.assertAlmostEqual(result.average, 121 / 3)
        self.assertEqual((result.median, result.minimum, result.maximum), (20, 1, 100))
        self.assertEqual(samples, [100, 1, 20])

    def test_even_median_averages_both_middle_observations(self):
        self.assertEqual(summarize_times(iter([90, 10, 20, 40])), TimeStatistics(40, 30, 10, 90))

    def test_non_finite_and_negative_times_are_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf"), -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                summarize_times([0, value])

    def test_engine_reports_all_statistics_for_each_day(self):
        routes = {"N08": Trip((), (), 40, 60)}
        run = simulate((Order(1, 0, "N08"), Order(2, 10, "N08")), routes, 1, 1)
        self.assertEqual(run.metrics.waitStatistics, TimeStatistics(45, 45, 0, 90))
        self.assertEqual(run.metrics.deliveryStatistics, TimeStatistics(85, 85, 40, 130))
        self.assertEqual(run.metrics.averageWait, 45)
        self.assertEqual(run.metrics.averageDelivery, 85)

    def test_engine_empty_day_has_empty_time_statistics(self):
        run = simulate((), {}, 1, 1)
        self.assertEqual(run.metrics.waitStatistics, summarize_times([]))
        self.assertEqual(run.metrics.deliveryStatistics, summarize_times([]))

    def test_aggregate_uses_pooled_orders_not_average_of_day_statistics(self):
        routes = {"N08": Trip((), (), 10, 10)}
        first = simulate(tuple(Order(index + 1, index * 20, "N08") for index in range(3)), routes, 1, 1)
        second = simulate((Order(1, 0, "N08"), Order(2, 0, "N08")), routes, 1, 1)
        experiment = Experiment("Dijkstra", 1, 4, 1, routes, routes, (
            Repetition(1, first, first), Repetition(2, second, second),
        ))
        result = aggregate(experiment, "current")
        self.assertEqual(result["wait"], 4)
        self.assertEqual(result["waitMedian"], 0)
        self.assertEqual(result["waitMinimum"], 0)
        self.assertEqual(result["waitMaximum"], 20)
        self.assertEqual(result["delivery"], 14)
        self.assertEqual(result["deliveryMedian"], 10)
        self.assertEqual(result["deliveryMinimum"], 10)
        self.assertEqual(result["deliveryMaximum"], 30)
        self.assertNotEqual(result["waitMedian"], mean([
            first.metrics.waitStatistics.median, second.metrics.waitStatistics.median,
        ]))
        self.assertNotEqual(result["waitMaximum"], mean([
            first.metrics.waitStatistics.maximum, second.metrics.waitStatistics.maximum,
        ]))

    def test_empty_day_is_not_counted_as_a_zero_time_order(self):
        routes = {"N08": Trip((), (), 10, 10)}
        empty = simulate((), routes, 1, 1)
        one = simulate((Order(1, 0, "N08"),), routes, 1, 1)
        experiment = Experiment("Dijkstra", 1, 4, 1, routes, routes, (
            Repetition(1, empty, empty), Repetition(2, one, one),
        ))
        for key in ("delivery", "deliveryMedian", "deliveryMinimum", "deliveryMaximum"):
            self.assertEqual(aggregate(experiment, "current")[key], 10)
        all_empty = Experiment("Dijkstra", 1, 0, 1, routes, routes, (Repetition(1, empty, empty),))
        for key in ("wait", "delivery", "waitMedian", "deliveryMedian", "waitMinimum",
                    "deliveryMinimum", "waitMaximum", "deliveryMaximum"):
            self.assertIsNone(aggregate(all_empty, "current")[key])
