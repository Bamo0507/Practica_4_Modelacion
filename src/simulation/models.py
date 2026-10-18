"""Datos de entrada y resultados de la jornada, con tiempos en minutos."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Order:
    identifier: int
    arrival: float
    destination: str


@dataclass(frozen=True)
class Trip:
    outbound: tuple[str, ...]
    inbound: tuple[str, ...]
    outboundMinutes: float
    inboundMinutes: float


@dataclass(frozen=True)
class AlternativeRoute:
    source: str
    trip: Trip | None


@dataclass(frozen=True)
class Delivery:
    order: Order
    vehicle: int
    departure: float
    delivered: float
    returned: float

    @property
    def wait(self) -> float:
        return self.departure - self.order.arrival

    @property
    def elapsed(self) -> float:
        return self.delivered - self.order.arrival


@dataclass(frozen=True)
class TimeStatistics:
    average: float | None
    median: float | None
    minimum: float | None
    maximum: float | None


@dataclass(frozen=True)
class Metrics:
    orders: int
    timely: int
    timelyPercent: float | None
    waitStatistics: TimeStatistics
    deliveryStatistics: TimeStatistics
    utilizationPercent: float
    overtime: float

    @property
    def averageWait(self) -> float | None:
        return self.waitStatistics.average

    @property
    def averageDelivery(self) -> float | None:
        return self.deliveryStatistics.average


@dataclass(frozen=True)
class Run:
    deliveries: tuple[Delivery, ...]
    metrics: Metrics


@dataclass(frozen=True)
class Repetition:
    seed: int
    current: Run
    proposed: Run


@dataclass(frozen=True)
class Experiment:
    algorithm: str
    vehicles: int
    rate: float
    hours: float
    currentRoutes: dict[str, Trip]
    proposedRoutes: dict[str, Trip]
    repetitions: tuple[Repetition, ...]
    additionalRoutes: dict[str, AlternativeRoute] = field(default_factory=dict)
