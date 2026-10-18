"""Comparación emparejada: mismos pedidos, destinos e instantes de llegada."""

from src.graph import Node

from .alternatives import build_additional_routes
from .engine import generate_orders, simulate, validate_inputs
from .models import Experiment, Repetition
from .routes import VEHICLE_COUNTS, build_routes


def run_experiment(
    nodes: list[Node], algorithm: str, vehicles: int = 8, rate: float = 4,
    hours: float = 8, seed: int = 42, repetitions: int = 5,
) -> Experiment:
    validate_inputs(rate, hours, vehicles, seed)
    if vehicles not in VEHICLE_COUNTS:
        raise ValueError("Selecciona 8, 10 o 12 camiones.")
    if type(repetitions) is not int or repetitions < 5:
        raise ValueError("Cada escenario necesita al menos cinco repeticiones.")
    current, proposed = build_routes(nodes, algorithm)
    additional = build_additional_routes(nodes, current, proposed)
    results = []
    for index in range(repetitions):
        repetition_seed = seed + index
        orders = generate_orders(rate, hours, repetition_seed)
        results.append(Repetition(
            repetition_seed,
            simulate(orders, current, vehicles, hours),
            simulate(orders, proposed, vehicles, hours),
        ))
    return Experiment(algorithm, vehicles, rate, hours, current, proposed, tuple(results), additional)
