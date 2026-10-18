"""Llegadas variables y atención FIFO con disponibilidad hasta el regreso."""

from heapq import heapify, heappop, heappush
from math import isfinite
from random import Random

from .models import Delivery, Metrics, Order, Run, Trip
from .routes import DESTINATIONS
from .statistics import summarize_times


def validate_inputs(rate: float, hours: float, vehicles: int, seed: int) -> None:
    if not isfinite(rate) or rate < 0:
        raise ValueError("La demanda debe ser un número finito mayor o igual a cero.")
    if not isfinite(hours) or hours <= 0:
        raise ValueError("La recepción de pedidos debe durar más de cero horas.")
    if type(vehicles) is not int or vehicles <= 0:
        raise ValueError("La cantidad de camiones debe ser un entero positivo.")
    if type(seed) is not int:
        raise ValueError("La semilla debe ser un número entero.")


def generate_orders(rate: float, hours: float, seed: int) -> tuple[Order, ...]:
    """Intervalos exponenciales; destinos independientes de igual probabilidad."""
    validate_inputs(rate, hours, 1, seed)
    if rate == 0:
        return ()
    arrivals, destinations = Random(seed), Random(f"destinations:{seed}")
    instant = 0.0
    orders = []
    while True:
        instant += arrivals.expovariate(rate / 60)
        if instant >= hours * 60:
            break
        orders.append(Order(len(orders) + 1, instant, destinations.choice(DESTINATIONS)))
    return tuple(orders)


def simulate(orders: tuple[Order, ...], routes: dict[str, Trip], vehicles: int, hours: float) -> Run:
    validate_inputs(0, hours, vehicles, 0)
    closing = hours * 60
    identifiers = set()
    for order in orders:
        if order.identifier in identifiers:
            raise ValueError("Los identificadores de los pedidos no pueden repetirse.")
        identifiers.add(order.identifier)
        if not isfinite(order.arrival) or not 0 <= order.arrival < closing:
            raise ValueError("Los pedidos deben llegar dentro del horario de recepción.")
        if order.destination not in routes:
            raise ValueError(f"Falta el recorrido del destino {order.destination}.")
        trip = routes[order.destination]
        if any(not isfinite(t) or t <= 0 for t in (trip.outboundMinutes, trip.inboundMinutes)):
            raise ValueError("Los tiempos de ida y regreso deben ser positivos y finitos.")
    available = [(0.0, vehicle) for vehicle in range(1, vehicles + 1)]
    heapify(available)
    deliveries = []
    for order in sorted(orders, key=lambda item: (item.arrival, item.identifier)):
        instant, vehicle = heappop(available)
        departure = max(instant, order.arrival)
        trip = routes[order.destination]
        delivered = departure + trip.outboundMinutes
        returned = delivered + trip.inboundMinutes
        deliveries.append(Delivery(order, vehicle, departure, delivered, returned))
        heappush(available, (returned, vehicle))
    timely = sum(item.elapsed <= 75 for item in deliveries)
    # Sólo se cuenta la parte ocupada dentro del horario de recepción.
    busy = sum(max(0.0, min(item.returned, closing) - item.departure) for item in deliveries)
    last_return = max((item.returned for item in deliveries), default=closing)
    metrics = Metrics(
        orders=len(deliveries), timely=timely,
        timelyPercent=100 * timely / len(deliveries) if deliveries else None,
        waitStatistics=summarize_times(item.wait for item in deliveries),
        deliveryStatistics=summarize_times(item.elapsed for item in deliveries),
        utilizationPercent=100 * busy / (vehicles * closing),
        overtime=max(0.0, last_return - closing),
    )
    return Run(tuple(deliveries), metrics)
