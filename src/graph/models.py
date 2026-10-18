"""Clases de datos para los nodos y sus conexiones de salida."""

from dataclasses import dataclass, field


@dataclass
class Connection:
    destinationId: str
    travelTimeMinutes: float


@dataclass
class Node:
    identifier: str
    achievableDestinations: list[Connection] = field(default_factory=list)
