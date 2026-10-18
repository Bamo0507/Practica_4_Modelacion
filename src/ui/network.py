"""La misma red que utiliza el motor, preparada para Cytoscape."""

from src.graph import Node
from src.simulation import DESTINATIONS

NAVY = "#12335b"
BLUE = "#2563eb"
MUTED = "#526781"


def elements(nodes: list[Node]) -> list[dict]:
    result = []
    for index, node in enumerate(nodes):
        role = "depot" if node.identifier == "N01" else (
            "destination" if node.identifier in DESTINATIONS else "location"
        )
        result.append({
            "data": {"id": node.identifier, "label": node.identifier},
            "position": {"x": (index % 8) * 130, "y": (index // 8) * 110},
            "classes": role,
        })
        result.extend({
            "data": {
                "id": f"{node.identifier}-{connection.destinationId}",
                "source": node.identifier, "target": connection.destinationId,
                "time": f"{connection.travelTimeMinutes:g}",
            }
        } for connection in node.achievableDestinations)
    return result


def stylesheet(show_times: bool = False) -> list[dict]:
    return [
        {"selector": "node", "style": {
            "label": "data(label)", "background-color": "#e4edf9",
            "color": NAVY, "font-size": 14, "font-family": "monospace",
            "font-weight": "bold", "width": 48, "height": 48,
            "text-valign": "center", "text-halign": "center",
            "border-width": 1, "border-color": "#9cb2cd",
        }},
        {"selector": ".depot", "style": {
            "shape": "roundrectangle", "background-color": NAVY, "color": "#ffffff",
            "width": 60, "height": 52, "border-color": NAVY,
        }},
        {"selector": ".destination", "style": {
            "background-color": BLUE, "color": "#ffffff", "border-color": BLUE,
        }},
        {"selector": "edge", "style": {
            "curve-style": "bezier", "line-color": "#8b9fb9", "width": 1.5,
            "target-arrow-shape": "triangle", "target-arrow-color": "#69809e",
            "arrow-scale": 0.9, "label": "data(time)" if show_times else "",
            "font-size": 13, "color": NAVY, "text-background-color": "#ffffff",
            "text-background-opacity": 0.95, "text-background-padding": "2px",
            "text-rotation": "autorotate",
        }},
        {"selector": ":selected", "style": {"border-width": 3, "border-color": BLUE}},
    ]
