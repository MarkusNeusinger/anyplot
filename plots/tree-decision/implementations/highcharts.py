"""pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: highcharts unknown | Python 3.14.3
Quality: 84/100 | Created: 2026-03-06
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Product Launch Decision Tree
# Stage 1: Launch Product vs Keep Current
# If Launch -> Chance: High Demand (0.6) / Low Demand (0.4)
#   High Demand -> $800K
#   Low Demand -> Stage 2 Decision: Discount vs Withdraw
#     Discount -> $200K
#     Withdraw -> -$100K
# If Keep Current -> Chance: Market Grows (0.5) / Market Stable (0.5)
#   Market Grows -> $400K
#   Market Stable -> $250K
#
# EMV rollback:
#   D2: max(200, -100) = $200K (choose Discount, prune Withdraw)
#   C1: 0.6 * 800 + 0.4 * 200 = $560K
#   C2: 0.5 * 400 + 0.5 * 250 = $325K
#   D1: max(560, 325) = $560K (choose Launch, prune Keep Current)


# --- Build chart using highcharts-core Python API ---

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"},
    "spacingTop": 20,
    "spacingBottom": 40,
    "spacingLeft": 40,
    "spacingRight": 40,
}

chart.options.title = {
    "text": "tree-decision \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "600", "color": "#333333"},
}

chart.options.subtitle = {
    "text": "Product Launch Decision Analysis \u2014 Expected Monetary Value Rollback",
    "style": {"fontSize": "32px", "fontWeight": "400", "color": "#777777"},
}

chart.options.x_axis = {"visible": False, "min": 0, "max": 4400, "gridLineWidth": 0}

chart.options.y_axis = {"visible": False, "min": 0, "max": 2300, "reversed": True, "gridLineWidth": 0}

chart.options.tooltip = {
    "useHTML": True,
    "style": {"fontSize": "24px", "pointerEvents": "none"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 2, "offsetY": 2, "width": 5},
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:28px;font-weight:700;color:{point.color}">'
        "\u25cf {series.name}</span><br/>"
        '<span style="font-size:24px;font-weight:600">{point.name}</span>'
    ),
}

chart.options.legend = {
    "enabled": True,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "x": -60,
    "y": 250,
    "itemStyle": {"fontSize": "28px", "fontWeight": "400", "color": "#444444"},
    "symbolWidth": 24,
    "symbolHeight": 24,
    "symbolRadius": 4,
    "itemMarginBottom": 20,
    "backgroundColor": "rgba(255, 255, 255, 0.9)",
    "borderColor": "#DDDDDD",
    "borderWidth": 1,
    "borderRadius": 8,
    "padding": 24,
    "title": {"text": "Legend", "style": {"fontSize": "30px", "fontWeight": "700", "color": "#333333"}},
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "scatter": {
        "states": {"hover": {"marker": {"radiusPlus": 10, "lineWidthPlus": 3}}, "inactive": {"opacity": 0.4}},
        "cursor": "pointer",
        "stickyTracking": False,
    }
}

# --- Series for each node type (id on each point forces object serialization) ---

# Decision nodes (squares)
decision_series = ScatterSeries()
decision_series.name = "Decision Node"
decision_series.data = [
    {"x": 550, "y": 1100, "id": "D1", "name": "EMV: $560K"},
    {"x": 2650, "y": 750, "id": "D2", "name": "EMV: $200K"},
]
decision_series.marker = {
    "symbol": "square",
    "radius": 36,
    "fillColor": "#306998",
    "lineColor": "#1F4D6E",
    "lineWidth": 4,
}
decision_series.color = "#306998"
decision_series.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "y": 60,
    "style": {"fontSize": "32px", "fontWeight": "700", "color": "#222222", "textOutline": "3px white"},
}
chart.add_series(decision_series)

# Chance nodes (circles)
chance_series = ScatterSeries()
chance_series.name = "Chance Node"
chance_series.data = [
    {"x": 1550, "y": 450, "id": "C1", "name": "EMV: $560K"},
    {
        "x": 1550,
        "y": 1750,
        "id": "C2",
        "name": "EMV: $325K",
        "marker": {"fillColor": "#DDDDDD", "lineColor": "#BBBBBB"},
    },
]
chance_series.marker = {
    "symbol": "circle",
    "radius": 36,
    "fillColor": "#E8833A",
    "lineColor": "#B85E20",
    "lineWidth": 4,
}
chance_series.color = "#E8833A"
chance_series.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "y": 60,
    "style": {"fontSize": "32px", "fontWeight": "700", "color": "#222222", "textOutline": "3px white"},
}
chart.add_series(chance_series)

# Terminal nodes - optimal path (triangles)
optimal_series = ScatterSeries()
optimal_series.name = "Terminal (Optimal)"
optimal_series.data = [
    {"x": 2650, "y": 200, "id": "T1", "name": "$800K"},
    {"x": 3750, "y": 500, "id": "T4", "name": "$200K"},
]
optimal_series.marker = {
    "symbol": "triangle",
    "radius": 30,
    "fillColor": "#2A9D8F",
    "lineColor": "#1E7A6D",
    "lineWidth": 4,
}
optimal_series.color = "#2A9D8F"
optimal_series.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "align": "left",
    "x": 50,
    "y": 5,
    "style": {"fontSize": "34px", "fontWeight": "700", "color": "#222222", "textOutline": "3px white"},
}
chart.add_series(optimal_series)

# Terminal nodes - pruned path (grey triangles)
pruned_series = ScatterSeries()
pruned_series.name = "Terminal (Pruned)"
pruned_series.data = [
    {"x": 3750, "y": 1000, "id": "T5", "name": "-$100K"},
    {"x": 2650, "y": 1450, "id": "T2", "name": "$400K"},
    {"x": 2650, "y": 2050, "id": "T3", "name": "$250K"},
]
pruned_series.marker = {
    "symbol": "triangle",
    "radius": 28,
    "fillColor": "#DDDDDD",
    "lineColor": "#BBBBBB",
    "lineWidth": 3,
}
pruned_series.color = "#BBBBBB"
pruned_series.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "align": "left",
    "x": 45,
    "y": 5,
    "style": {"fontSize": "32px", "fontWeight": "700", "color": "#999999", "textOutline": "3px white"},
}
chart.add_series(pruned_series)

# Optimal path line (invisible series for legend entry)
path_optimal = ScatterSeries()
path_optimal.name = "Optimal Path"
path_optimal.data = []
path_optimal.color = "#306998"
path_optimal.marker = {"symbol": "square", "radius": 0}
path_optimal.line_width = 5
chart.add_series(path_optimal)

# Pruned path line (invisible series for legend entry)
path_pruned = ScatterSeries()
path_pruned.name = "Pruned Branch"
path_pruned.data = []
path_pruned.color = "#CCCCCC"
path_pruned.marker = {"symbol": "square", "radius": 0}
path_pruned.dash_style = "Dash"
path_pruned.line_width = 3
chart.add_series(path_pruned)

# Generate chart JS via highcharts-core API
chart_js = chart.to_js_literal()

# Edge data for bezier curve drawing (renderer for custom graph edges)
edges_data = [
    {"fx": 550, "fy": 1100, "tx": 1550, "ty": 450, "label": "Launch Product", "p": False},
    {"fx": 550, "fy": 1100, "tx": 1550, "ty": 1750, "label": "Keep Current", "p": True},
    {"fx": 1550, "fy": 450, "tx": 2650, "ty": 200, "label": "High Demand (0.6)", "p": False},
    {"fx": 1550, "fy": 450, "tx": 2650, "ty": 750, "label": "Low Demand (0.4)", "p": False},
    {"fx": 2650, "fy": 750, "tx": 3750, "ty": 500, "label": "Discount", "p": False},
    {"fx": 2650, "fy": 750, "tx": 3750, "ty": 1000, "label": "Withdraw", "p": True},
    {"fx": 1550, "fy": 1750, "tx": 2650, "ty": 1450, "label": "Market Grows (0.5)", "p": True},
    {"fx": 1550, "fy": 1750, "tx": 2650, "ty": 2050, "label": "Market Stable (0.5)", "p": True},
]
edges_json = json.dumps(edges_data)

# JS to draw bezier edges using chart renderer + axis coordinate mapping
edge_js = (
    """
(function() {
    var chart = Highcharts.charts[Highcharts.charts.length - 1];
    if (!chart) return;
    var ren = chart.renderer;
    var xAxis = chart.xAxis[0];
    var yAxis = chart.yAxis[0];
    var edges = """
    + edges_json
    + """;

    edges.forEach(function(e) {
        var x1 = xAxis.toPixels(e.fx);
        var y1 = yAxis.toPixels(e.fy);
        var x2 = xAxis.toPixels(e.tx);
        var y2 = yAxis.toPixels(e.ty);
        var midX = (x1 + x2) / 2;

        var edgeColor = e.p ? '#CCCCCC' : '#306998';
        var edgeWidth = e.p ? 3 : 5;

        ren.path([
            'M', x1, y1,
            'C', midX, y1, midX, y2, x2, y2
        ]).attr({
            'stroke': edgeColor,
            'stroke-width': edgeWidth,
            'fill': 'none',
            'stroke-dasharray': e.p ? '16,10' : 'none',
            zIndex: 1
        }).add();

        if (e.p) {
            var pruneX = x1 + (x2 - x1) * 0.35;
            var pruneY = y1 + (y2 - y1) * 0.25;
            ren.path([
                'M', pruneX - 12, pruneY - 18,
                'L', pruneX + 12, pruneY + 18,
                'M', pruneX + 4, pruneY - 18,
                'L', pruneX + 28, pruneY + 18
            ]).attr({
                'stroke': '#CC4444',
                'stroke-width': 4,
                zIndex: 5
            }).add();
        }

        var labelX = x1 + (x2 - x1) * 0.45;
        var labelY = y1 + (y2 - y1) * 0.45 - 20;
        var labelColor = e.p ? '#999999' : '#444444';

        ren.text(e.label, labelX, labelY).attr({
            align: 'center',
            zIndex: 6
        }).css({
            fontSize: '30px',
            fontWeight: '600',
            color: labelColor,
            fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
        }).add();
    });
})();
"""
)

# Download Highcharts JS
highcharts_paths = [
    Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js",
    Path("node_modules/highcharts/highcharts.js"),
]
highcharts_js = None
for p in highcharts_paths:
    if p.exists():
        highcharts_js = p.read_text(encoding="utf-8")
        break
if highcharts_js is None:
    highcharts_url = "https://code.highcharts.com/highcharts.js"
    req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        highcharts_js = response.read().decode("utf-8")

# Build HTML with chart JS from highcharts-core + edge drawing
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>
    {chart_js}
    </script>
    <script>
    setTimeout(function() {{
    {edge_js}
    }}, 200);
    </script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
