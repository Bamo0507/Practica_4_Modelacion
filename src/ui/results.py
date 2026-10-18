"""Tablas y gráficas derivadas de los resultados reales del motor."""

from statistics import mean

from dash import dcc, html
import plotly.graph_objects as go

from src.simulation import Experiment, summarize_times

from .network import BLUE, NAVY


def table(headers: list[str], rows: list[list], caption: str | None = None):
    return html.Div(html.Table([
        *([html.Caption(caption)] if caption else []),
        html.Thead(html.Tr([html.Th(value, scope="col") for value in headers])),
        html.Tbody([html.Tr([html.Td(value) for value in row]) for row in rows]),
    ]), className="table-wrap", tabIndex=0)


def formatted(value: float | None, suffix: str = "") -> str:
    return "Sin pedidos" if value is None else f"{value:,.1f}{suffix}"


def aggregate(experiment: Experiment, policy: str) -> dict:
    runs = [getattr(repetition, policy) for repetition in experiment.repetitions]
    deliveries = [delivery for run in runs for delivery in run.deliveries]
    timely = sum(run.metrics.timely for run in runs)
    wait = summarize_times(item.wait for item in deliveries)
    delivery = summarize_times(item.elapsed for item in deliveries)
    return {
        "orders": len(deliveries) / len(runs),
        "timely": timely / len(runs),
        "percent": 100 * timely / len(deliveries) if deliveries else None,
        "wait": wait.average,
        "waitMedian": wait.median,
        "waitMinimum": wait.minimum,
        "waitMaximum": wait.maximum,
        "delivery": delivery.average,
        "deliveryMedian": delivery.median,
        "deliveryMinimum": delivery.minimum,
        "deliveryMaximum": delivery.maximum,
        "utilization": mean(run.metrics.utilizationPercent for run in runs),
        "overtime": mean(run.metrics.overtime for run in runs),
    }


def comparison_chart(current: dict, proposed: dict, key: str, title: str, unit: str):
    values = [current[key], proposed[key]]
    if all(value is None for value in values):
        return html.Article([html.H3(title), html.P("Sin pedidos para calcular este indicador.")],
                            className="empty-state")
    figure = go.Figure(go.Bar(
        y=["Rutas actuales", "Algoritmo seleccionado"], x=values, orientation="h",
        marker_color=[NAVY, BLUE],
        text=[formatted(value, f" {unit}") for value in values], textposition="auto",
        hovertemplate=f"%{{y}}: %{{x:.1f}} {unit}<extra></extra>",
    ))
    figure.update_layout(
        title={"text": title, "font": {"size": 18}}, height=245,
        margin={"l": 12, "r": 32, "t": 55, "b": 40},
        font={"family": "Fira Sans, Arial, sans-serif", "size": 14, "color": NAVY},
        paper_bgcolor="white", plot_bgcolor="white", showlegend=False,
        xaxis={"title": unit, "rangemode": "tozero", "gridcolor": "#e6edf5"},
        yaxis={"autorange": "reversed", "automargin": True},
    )
    if key == "percent":
        figure.update_xaxes(range=[0, 105])
    return dcc.Graph(figure=figure, config={"displaylogo": False, "responsive": True,
                                         "modeBarButtons": [["toImage"]]},
                     className="comparison-chart")


def render_results(experiment: Experiment, scenario: str):
    current = aggregate(experiment, "current")
    proposed = aggregate(experiment, "proposed")
    summaries = [
        ("Entregas puntuales", "percent", "%"),
        ("Espera promedio por camión", "wait", " min"),
        ("Solicitud a entrega (promedio)", "delivery", " min"),
        ("Tiempo extra de operación", "overtime", " min"),
    ]
    cards = html.Div([
        html.Article([
            html.P(label, className="metric-label"),
            html.Strong(formatted(proposed[key], unit), className="metric-value"),
            html.P(f"Actual: {formatted(current[key], unit)}", className="metric-baseline"),
        ], className="metric-card") for label, key, unit in summaries
    ], className="metrics")
    time_rows = [
        [label, policy, formatted(values[key]), formatted(values[f"{key}Median"]),
         formatted(values[f"{key}Minimum"]), formatted(values[f"{key}Maximum"])]
        for label, key in (("Espera por camión", "wait"), ("Solicitud a entrega", "delivery"))
        for policy, values in (("Rutas actuales", current), (experiment.algorithm, proposed))
    ]
    metric_rows = [
        [label, formatted(current[key], unit), formatted(proposed[key], unit)]
        for label, key, unit in [
            ("Pedidos por jornada", "orders", ""),
            ("Pedidos puntuales por jornada", "timely", ""),
            ("Entregas dentro de 75 min", "percent", "%"),
            ("Espera promedio por camión", "wait", " min"),
            ("Tiempo promedio de solicitud a entrega", "delivery", " min"),
            ("Utilización durante la recepción", "utilization", "%"),
            ("Operación después del cierre", "overtime", " min"),
        ]
    ]
    route_rows, paths = [], []
    for destination, trip in experiment.proposedRoutes.items():
        baseline = experiment.currentRoutes[destination]
        extra = experiment.additionalRoutes.get(destination)
        selected_label = (f"{experiment.algorithm} (misma ida actual)" if trip.outbound == baseline.outbound
                          else f"Alternativa 1: {experiment.algorithm}")
        options = [("Actual", baseline, "Hoja de despacho"),
                   (selected_label, trip, experiment.algorithm)]
        if extra is not None:
            options.append(("Alternativa 2", extra.trip, extra.source))
        path_details = [html.H3(destination)]
        if trip.outbound == baseline.outbound:
            path_details.append(html.P("La ida del algoritmo coincide con la ida actual."))
        for label, option, source in options:
            if option is None:
                route_rows.append([destination, label, "Sin otra ida válida", "No aplica", "No aplica"])
                path_details.append(html.P("No existe otra ida simple distinta con las conexiones disponibles."))
                continue
            route_rows.append([
                destination, label, formatted(option.outboundMinutes), formatted(option.inboundMinutes),
                formatted(option.outboundMinutes + option.inboundMinutes),
            ])
            path_details.extend([
                html.H4(label), html.P(f"Origen del recorrido: {source}.", className="muted"),
                html.P([html.Strong("Ida: "), " -> ".join(option.outbound)]),
                html.P([html.Strong("Regreso: "), " -> ".join(option.inbound)]),
            ])
        paths.append(html.Div(path_details, className="route-path"))
    repetition_rows = []
    for index, repetition in enumerate(experiment.repetitions, 1):
        for label, run in (("Actual", repetition.current), (experiment.algorithm, repetition.proposed)):
            metrics = run.metrics
            repetition_rows.append([
                index, repetition.seed, label, metrics.orders, metrics.timely,
                formatted(metrics.averageWait), formatted(metrics.averageDelivery),
                formatted(metrics.utilizationPercent), formatted(metrics.overtime),
            ])
    return [
        html.Div([
            html.Div([html.P("COMPARACIÓN COMPLETADA", className="eyebrow"),
                      html.H2(f"{scenario} con {experiment.vehicles} camiones")]),
            html.Span(f"{experiment.algorithm} / {len(experiment.repetitions)} repeticiones", className="badge"),
        ], className="section-heading"),
        html.P(
            f"Demanda: {experiment.rate:g} pedidos/h. Recepción: {experiment.hours:g} h. "
            "Cada pareja utiliza los mismos pedidos, destinos e instantes de llegada.",
            className="muted",
        ),
        cards,
        table(["Tiempo", "Rutas", "Promedio", "Mediana", "Mínimo", "Máximo"], time_rows,
              "Tiempos de todos los pedidos (min)"),
        html.P(
            f"Se calculan sobre todos los pedidos de las {len(experiment.repetitions)} repeticiones. "
            "La mediana es el valor central al ordenar los tiempos; si hay dos valores centrales, "
            "se promedian. El mínimo y el máximo son los extremos observados. "
            "No se promedian las medianas ni los extremos de cada jornada.",
            className="muted",
        ),
        html.Div([
            comparison_chart(current, proposed, "delivery", "Tiempo promedio de entrega", "min"),
            comparison_chart(current, proposed, "percent", "Puntualidad de los pedidos", "%"),
        ], className="charts"),
        html.Details([
            html.Summary("Ver indicadores y repeticiones"),
            html.P(
                "Los tiempos y la puntualidad se calculan sobre todos los pedidos. "
                "Los conteos, la utilización y el tiempo extra se promedian por jornada. "
                "La utilización incluye ida y regreso, sólo dentro del horario de recepción.",
                className="muted",
            ),
            table(["Indicador", "Rutas actuales", experiment.algorithm], metric_rows),
            table(["Repetición", "Semilla", "Política", "Pedidos", "Puntuales", "Espera promedio (min)",
                   "Entrega promedio (min)", "Utilización (%)", "Extra (min)"], repetition_rows,
                  "Resultados de cada jornada"),
        ], className="details-block"),
        html.H2("Tiempos de las rutas"),
        html.P(
            "La simulación compara las rutas actuales con la alternativa 1. La alternativa 2 se muestra "
            "para validar otro recorrido de ida distinto, no como una tercera política simulada. "
            "Ida y regreso se calculan por separado; el total suma ambos viajes, sin espera por camión.",
            className="muted",
        ),
        table(["Destino", "Opción", "Ida (min)", "Regreso (min)", "Total (min)"], route_rows,
              "Ruta actual y alternativas por destino"),
        html.Details([html.Summary("Ver todos los recorridos de ida y regreso"), *paths], className="details-block"),
    ]
