"""Pruebas HTTP de la interfaz y sus callbacks, sin iniciar un servidor."""

import unittest

from src.app import create_app


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.server.test_client()
        cls.callback = next(key for key in cls.app.callback_map if "results.children" in key)
        cls.outputs = [
            {"id": "results", "property": "children"},
            {"id": "error", "property": "children"},
            {"id": "network", "property": "elements"},
            {"id": "network-table", "property": "children"},
            {"id": "network-note", "property": "children"},
            {"id": "network-count", "property": "children"},
        ]

    def execute(self, **changes):
        values = {"algorithm": "Dijkstra", "vehicles": 8, "scenario": "Normal", "rate": 4,
                  "hours": 8, "seed": 42, "edge": None, "edge-time": None, "closed": []}
        values.update(changes)
        return self.client.post("/_dash-update-component", json={
            "output": self.callback, "outputs": self.outputs,
            "inputs": [{"id": "simulate", "property": "n_clicks", "value": 1}],
            "state": [{"id": key, "property": "value", "value": value} for key, value in values.items()],
            "changedPropIds": ["simulate.n_clicks"],
        })

    def test_page_layout_and_assets_are_served(self):
        for path in ("/", "/_dash-layout", "/_dash-dependencies", "/assets/styles.css"):
            with self.subTest(path=path):
                with self.client.get(path) as response:
                    self.assertEqual(response.status_code, 200)
        layout = self.client.get("/_dash-layout").get_json()
        content = str(layout)
        for identifier in ("algorithm", "vehicles", "simulate", "scenario"):
            self.assertIn(identifier, content)
        self.assertIn("12 camiones", content)

    def test_complete_run_for_each_fleet_and_algorithm(self):
        for algorithm in ("Dijkstra", "A*", "Hill Climbing"):
            for vehicles in (8, 10, 12):
                response = self.execute(algorithm=algorithm, vehicles=vehicles)
                self.assertEqual(response.status_code, 200)
                content = response.get_json()["response"]
                self.assertEqual(content["error"]["children"], "")
                self.assertIn(f"Normal con {vehicles} camiones", str(content["results"]))
                for label in ("Promedio", "Mediana", "Mínimo", "Máximo"):
                    self.assertIn(label, str(content["results"]))
                self.assertEqual(len(content["network"]["elements"]), 184)

    def test_rate_matches_selected_season(self):
        response = self.client.post("/_dash-update-component", json={
            "output": "rate.value", "outputs": {"id": "rate", "property": "value"},
            "inputs": [{"id": "scenario", "property": "value", "value": "Navidad"}],
            "state": [], "changedPropIds": ["scenario.value"],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["response"]["rate"]["value"], 10)

    def test_closed_connection_updates_graph_count_and_routes(self):
        response = self.execute(edge="N02|N18", closed=["closed"])
        self.assertEqual(response.status_code, 200)
        content = response.get_json()["response"]
        self.assertEqual(content["error"]["children"], "")
        self.assertEqual(len(content["network"]["elements"]), 183)
        self.assertIn("143", content["network-count"]["children"])
        self.assertIn("cerrada", content["network-note"]["children"])
        self.assertFalse(any(item["data"]["id"] == "N02-N18" for item in content["network"]["elements"]))

    def test_invalid_inputs_show_error_instead_of_old_results(self):
        for changes in ({"hours": None}, {"rate": -1}, {"vehicles": 9}, {"seed": 2.5},
                        {"edge-time": 20}, {"edge": "N01|N02", "closed": ["closed"]}):
            response = self.execute(**changes)
            self.assertEqual(response.status_code, 200)
            content = response.get_json()["response"]
            self.assertTrue(content["error"]["children"])
            self.assertIn("No se ejecutó", str(content["results"]))

    def test_no_orders_is_valid_and_displays_empty_metrics(self):
        response = self.execute(rate=0)
        self.assertEqual(response.status_code, 200)
        content = response.get_json()["response"]
        self.assertEqual(content["error"]["children"], "")
        self.assertIn("Sin pedidos", str(content["results"]))

    def test_route_table_includes_current_and_two_alternatives_for_all_destinations(self):
        def components(value):
            if isinstance(value, dict):
                if "type" in value:
                    yield value
                for child in value.values():
                    yield from components(child)
            elif isinstance(value, list):
                for child in value:
                    yield from components(child)

        response = self.execute()
        content = response.get_json()["response"]["results"]["children"]
        route_table = next(component for component in components(content)
                           if component.get("type") == "Table"
                           and component["props"]["children"][0]["props"].get("children")
                           == "Ruta actual y alternativas por destino")
        rows = route_table["props"]["children"][-1]["props"]["children"]
        self.assertEqual(len(rows), 12)
        values = [[cell["props"]["children"] for cell in row["props"]["children"]] for row in rows]
        for destination in ("N08", "N19", "N34", "N40"):
            self.assertEqual(sum(row[0] == destination for row in values), 3)
        self.assertIn(["N40", "Alternativa 2", "51.0", "61.0", "112.0"], values)
        self.assertIn("no como una tercera política simulada", str(content))

    def test_additional_route_is_updated_after_a_closure(self):
        response = self.execute(edge="N31|N39", closed=["closed"])
        self.assertEqual(response.status_code, 200)
        content = response.get_json()["response"]
        self.assertEqual(content["error"]["children"], "")
        self.assertIn("54.0", str(content["results"]))
        self.assertIn("143", content["network-count"]["children"])
