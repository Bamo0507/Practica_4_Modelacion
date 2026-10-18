"""Aplicación Dash. Importar este módulo no inicia el servidor."""

from pathlib import Path

from dash import Dash, Input, Output, State, html, no_update

from src.graph import read_graph
from src.simulation import SCENARIOS, VEHICLE_COUNTS, changed_graph, run_experiment
from src.ui.layout import layout
from src.ui.network import elements, stylesheet
from src.ui.results import render_results, table

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "matriz_logistica.csv"


def create_app() -> Dash:
    app = Dash(__name__, assets_folder=str(ROOT / "assets"), title="Simulador | Logística del Valle",
               update_title="Simulando...", meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
    app.layout = layout(read_graph(MATRIX))

    @app.callback(Output("rate", "value"), Input("scenario", "value"))
    def scenario_rate(scenario):
        return SCENARIOS.get(scenario, 4)

    @app.callback(Output("network", "stylesheet"), Input("show-times", "value"))
    def graph_labels(show_times):
        return stylesheet("times" in (show_times or []))

    @app.callback(
        Output("results", "children"), Output("error", "children"),
        Output("network", "elements"), Output("network-table", "children"),
        Output("network-note", "children"), Output("network-count", "children"),
        Input("simulate", "n_clicks"),
        State("algorithm", "value"), State("vehicles", "value"), State("scenario", "value"),
        State("rate", "value"), State("hours", "value"), State("seed", "value"),
        State("edge", "value"), State("edge-time", "value"), State("closed", "value"),
        prevent_initial_call=True,
        running=[(Output("simulate", "disabled"), True, False),
                 (Output("simulate", "children"), "Simulando...", "Simular")],
    )
    def execute(clicks, algorithm, vehicles, scenario, rate, hours, seed, edge, minutes, closed):
        try:
            if vehicles not in VEHICLE_COUNTS:
                raise ValueError("Selecciona 8, 10 o 12 camiones.")
            if rate is None or not 0 <= rate <= 100:
                raise ValueError("Pedidos por hora: ingresa un promedio entre 0 y 100.")
            if hours is None or not 0.5 <= hours <= 24:
                raise ValueError("Recepción: ingresa una duración entre 0.5 y 24 horas.")
            if seed is None or not float(seed).is_integer():
                raise ValueError("Semilla: ingresa un número entero.")
            if edge is None and (minutes is not None or closed):
                raise ValueError("Selecciona una conexión antes de cambiar su tiempo o cerrarla.")
            nodes = changed_graph(read_graph(MATRIX), tuple(edge.split("|")) if edge else None,
                                  minutes, "closed" in (closed or []))
            result = run_experiment(nodes, algorithm, int(vehicles), rate, hours, int(seed))
        except ValueError as error:
            # Se retiran los resultados anteriores para no atribuirlos a una ejecución fallida.
            return (html.Div("No se ejecutó la simulación. Corrige la configuración e inténtalo de nuevo.",
                             className="empty-state"),
                    html.Div(str(error), className="error-message"),
                    no_update, no_update, no_update, no_update)
        connections = [[node.identifier, c.destinationId, f"{c.travelTimeMinutes:g}"]
                       for node in nodes for c in node.achievableDestinations]
        change = "Red de esta ejecución: matriz original, sin cambios."
        if edge:
            change = f"Red de esta ejecución: {edge.replace('|', ' -> ')} " + (
                "cerrada." if closed else f"con {minutes:g} min." if minutes is not None else "sin cambios.")
        return (render_results(result, scenario), "", elements(nodes),
                table(["Origen", "Destino", "Tiempo (min)"], connections), change,
                f"{len(nodes)} ubicaciones / {len(connections)} conexiones dirigidas")

    return app


app = create_app()
server = app.server
