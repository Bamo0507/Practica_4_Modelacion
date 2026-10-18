"""Pruebas del lector de la red de distribución."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.graph import Connection, Node, read_graph


class CsvReaderTests(unittest.TestCase):
    def read_fixture(self, content: str) -> list[Node]:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.csv"
            path.write_text(content, encoding="utf-8-sig")
            return read_graph(path)

    def test_loads_real_network(self):
        path = Path(__file__).resolve().parents[1] / "data" / "matriz_logistica.csv"
        nodes = read_graph(path)
        self.assertEqual([node.identifier for node in nodes], [f"N{i:02}" for i in range(1, 41)])
        self.assertEqual(sum(len(node.achievableDestinations) for node in nodes), 144)
        self.assertEqual(
            nodes[0].achievableDestinations,
            [Connection("N02", 8), Connection("N09", 7), Connection("N17", 9)],
        )
        n17 = next(node for node in nodes if node.identifier == "N17")
        self.assertNotIn("N01", [edge.destinationId for edge in n17.achievableDestinations])

    def test_preserves_direction_and_fractional_times(self):
        nodes = self.read_fixture("Origen/Destino,A,B\r\nA,0,2.5\r\nB,,0\r\n")
        self.assertEqual(nodes[0].achievableDestinations, [Connection("B", 2.5)])
        self.assertEqual(nodes[1].achievableDestinations, [])

    def test_preserves_header_order_when_rows_are_reordered(self):
        nodes = self.read_fixture("Origen/Destino,A,B\nB,9,0\nA,0,3\n")
        self.assertEqual([node.identifier for node in nodes], ["A", "B"])
        self.assertEqual(nodes[0].achievableDestinations, [Connection("B", 3)])
        self.assertEqual(nodes[1].achievableDestinations, [Connection("A", 9)])

    def test_node_lists_are_independent(self):
        first, second = Node("A"), Node("B")
        first.achievableDestinations.append(Connection("B", 5))
        self.assertEqual(second.achievableDestinations, [])

    def test_rejects_invalid_structure(self):
        cases = [
            ("", "cabecera"),
            ("Origen/Destino,A,A\n", "repetidos"),
            ("Origen/Destino,A,\n", "vacíos"),
            ("Origen/Destino,A,B\nA,0\n", "campos"),
            ("Origen/Destino,A,B\nC,0,1\n", "no aparece"),
            ("Origen/Destino,A,B\nA,0,1\nA,0,1\n", "más de una fila"),
            ("Origen/Destino,A,B\nA,0,1\n", "Faltan filas"),
        ]
        for content, message in cases:
            with self.subTest(content=content):
                with self.assertRaisesRegex(ValueError, message):
                    self.read_fixture(content)

    def test_rejects_invalid_travel_times(self):
        for value in ["-2", "0", "nan", "inf", "texto"]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "conexión A -> B"):
                    self.read_fixture(f"Origen/Destino,A,B\nA,0,{value}\nB,,0\n")

    def test_rejects_nonzero_diagonal(self):
        with self.assertRaisesRegex(ValueError, "diagonal"):
            self.read_fixture("Origen/Destino,A\nA,5\n")

    def test_reports_missing_file(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                read_graph(Path(directory) / "missing.csv")
