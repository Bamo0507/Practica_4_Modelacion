"""Lectura de matrices de tiempos y construcción de sus nodos."""

import csv
import math
from pathlib import Path

from .models import Connection, Node


def read_graph(path: str | Path) -> list[Node]:
    """Carga una matriz CSV como nodos con conexiones directas y dirigidas.

    La primera columna identifica el origen y la cabecera identifica los
    destinos. Las celdas vacías no crean conexiones y la diagonal debe
    contener ceros o estar vacía. Los demás tiempos deben ser positivos.
    El resultado conserva el orden de los destinos de la cabecera.
    """
    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        header = next(reader, None)
        if header is None or len(header) < 2:
            raise ValueError("El CSV debe incluir una cabecera con destinos.")

        identifiers = [value.strip() for value in header[1:]]
        if any(not identifier for identifier in identifiers):
            raise ValueError("Los identificadores de destino no pueden estar vacíos.")
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("La cabecera contiene identificadores repetidos.")

        nodes = {identifier: Node(identifier) for identifier in identifiers}
        seen_origins: set[str] = set()

        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(
                    f"Fila {reader.line_num}: se esperaban {len(header)} campos "
                    f"y se encontraron {len(row)}."
                )

            origin = row[0].strip()
            if origin not in nodes:
                raise ValueError(
                    f"Fila {reader.line_num}: el origen {origin!r} "
                    "no aparece en la cabecera."
                )
            if origin in seen_origins:
                raise ValueError(f"El origen {origin!r} tiene más de una fila.")
            seen_origins.add(origin)

            for destination, raw_time in zip(identifiers, row[1:]):
                value = raw_time.strip()
                if not value:
                    continue

                try:
                    travel_time = float(value)
                except ValueError as error:
                    raise ValueError(
                        f"La conexión {origin} -> {destination} "
                        f"tiene un tiempo no numérico: {value!r}."
                    ) from error

                if not math.isfinite(travel_time):
                    raise ValueError(
                        f"La conexión {origin} -> {destination} "
                        "debe tener un tiempo finito."
                    )

                if origin == destination:
                    if travel_time != 0:
                        raise ValueError(
                            f"La diagonal de {origin} debe tener un tiempo de cero."
                        )
                    continue

                if travel_time <= 0:
                    raise ValueError(
                        f"La conexión {origin} -> {destination} "
                        "debe tener un tiempo mayor que cero."
                    )

                nodes[origin].achievableDestinations.append(
                    Connection(destination, travel_time)
                )

        missing = [identifier for identifier in identifiers if identifier not in seen_origins]
        if missing:
            raise ValueError(f"Faltan filas para los orígenes: {', '.join(missing)}.")

        return list(nodes.values())
