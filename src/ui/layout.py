"""Vista única: selección, ejecución completa y resultados."""

from dash import dcc, html
import dash_cytoscape as cyto

from src.algorithms import ALGORITHMS
from src.graph import Node
from src.simulation import SCENARIOS, VEHICLE_COUNTS

from .network import elements, stylesheet
from .results import table


def field(label: str, identifier: str, component, hint: str | None = None):
    return html.Div([
        html.Label(label, htmlFor=identifier), component,
        *([html.Small(hint)] if hint else []),
    ], className="field")


def layout(nodes: list[Node]):
    edges = [(node.identifier, connection) for node in nodes for connection in node.achievableDestinations]
    dropdown = {"clearable": False, "searchable": False}
    return html.Main([
        html.A("Ir a resultados", href="#results", className="skip-link"),
        html.Header([
            html.P("LOGÍSTICA DEL VALLE", className="eyebrow"),
            html.H1("Simulador de distribución"),
            html.P("Compara las rutas actuales con los algoritmos y revisa cómo cambia el servicio.", className="intro"),
        ]),
        html.Section([
            html.Div([
                field("Algoritmo", "algorithm", dcc.Dropdown(
                    list(ALGORITHMS), "Dijkstra", id="algorithm", **dropdown)),
                field("Camiones", "vehicles", dcc.Dropdown(
                    [{"label": f"{count} camiones", "value": count} for count in VEHICLE_COUNTS],
                    8, id="vehicles", **dropdown)),
                field("Época", "scenario", dcc.Dropdown(
                    list(SCENARIOS), "Normal", id="scenario", **dropdown)),
                html.Button("Simular", id="simulate", n_clicks=0, className="primary"),
            ], className="main-controls"),
            html.Details([
                html.Summary("Configuración de la jornada y conexiones"),
                html.Div([
                    field("Pedidos por hora", "rate", dcc.Input(id="rate", type="number", value=4,
                          min=0, max=100, step=0.5), "Promedio esperado; no es una cantidad fija."),
                    field("Recepción (horas)", "hours", dcc.Input(id="hours", type="number", value=8,
                          min=0.5, max=24, step=0.5)),
                    field("Semilla", "seed", dcc.Input(id="seed", type="number", value=42, step=1),
                          "Permite repetir la misma secuencia de pedidos."),
                ], className="settings-grid"),
                html.H3("Cambio opcional de una conexión"),
                html.P("Se aplica sólo al sentido seleccionado y no modifica el CSV. Vacío conserva el tiempo original.",
                       className="muted"),
                html.Div([
                    field("Conexión", "edge", dcc.Dropdown(
                        [{"label": f"{source} -> {c.destinationId} ({c.travelTimeMinutes:g} min)",
                          "value": f"{source}|{c.destinationId}"} for source, c in edges],
                        id="edge", placeholder="Sin cambios", clearable=True)),
                    field("Nuevo tiempo (min)", "edge-time", dcc.Input(
                        id="edge-time", type="number", min=0.1, step=0.5, placeholder="Original")),
                    dcc.Checklist([{"label": " Cerrar esta conexión", "value": "closed"}], [], id="closed"),
                ], className="settings-grid"),
            ], className="configuration"),
            html.P("5 repeticiones por ejecución. La atención continúa hasta que regresa el último camión.",
                   className="run-hint"),
        ], className="panel controls-panel", **{"aria-label": "Configurar simulación"}),
        html.Div(id="error", role="alert", **{"aria-live": "assertive"}),
        dcc.Loading(html.Section([
            html.Div([html.H2("Todo listo para simular"),
                      html.P("Elige el algoritmo, la cantidad de camiones y la época. Luego presiona Simular.")],
                     className="empty-state"),
        ], id="results", className="results", **{"aria-live": "polite"}), type="circle", color="#2563eb"),
        html.Section([
            html.Div([
                html.Div([html.H2("Red de distribución"), html.P(
                    f"{len(nodes)} ubicaciones / {len(edges)} conexiones dirigidas",
                    id="network-count", className="muted")]),
                dcc.Checklist([{"label": " Mostrar minutos", "value": "times"}], [], id="show-times"),
            ], className="section-heading"),
            html.P("N01 es la bodega. N08, N19, N34 y N40 son destinos. Arrastra los nodos o amplía la vista.",
                   className="muted"),
            cyto.Cytoscape(
                id="network", elements=elements(nodes), stylesheet=stylesheet(),
                layout={"name": "preset", "fit": True, "padding": 28},
                style={"width": "100%", "height": "520px"}, minZoom=0.2, maxZoom=3,
                responsive=True, autoRefreshLayout=False,
            ),
            html.P("Esquema de conexiones, no mapa geográfico. Las flechas indican el sentido de circulación.",
                   className="muted graph-note"),
            html.Div(id="network-note", className="muted"),
            html.Details([
                html.Summary("Ver conexiones en tabla"),
                html.Div(table(["Origen", "Destino", "Tiempo (min)"], [
                    [source, c.destinationId, f"{c.travelTimeMinutes:g}"] for source, c in edges
                ]), id="network-table"),
            ], className="details-block"),
        ], className="panel network-panel"),
        html.Footer("Modelación y simulación / Logística del Valle"),
    ], className="workspace")
