""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
"""

import json
import tempfile
import time
import urllib.request
from collections import OrderedDict
from pathlib import Path

from highcharts_core.chart import Chart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Synthetic sedimentary section (Colorado Plateau stratigraphy)
layers = [
    {"top": 0, "bottom": 18, "lithology": "sandstone", "formation": "Dakota Sandstone", "age": "Cretaceous"},
    {"top": 18, "bottom": 42, "lithology": "shale", "formation": "Morrison Formation", "age": "Jurassic"},
    {"top": 42, "bottom": 58, "lithology": "limestone", "formation": "Sundance Formation", "age": "Jurassic"},
    {"top": 58, "bottom": 68, "lithology": "siltstone", "formation": "Carmel Formation", "age": "Jurassic"},
    {"top": 68, "bottom": 100, "lithology": "sandstone", "formation": "Navajo Sandstone", "age": "Jurassic"},
    {"top": 100, "bottom": 118, "lithology": "conglomerate", "formation": "Kayenta Formation", "age": "Triassic"},
    {"top": 118, "bottom": 142, "lithology": "shale", "formation": "Chinle Formation", "age": "Triassic"},
    {"top": 142, "bottom": 162, "lithology": "limestone", "formation": "Kaibab Limestone", "age": "Permian"},
    {"top": 162, "bottom": 185, "lithology": "sandstone", "formation": "Coconino Sandstone", "age": "Permian"},
    {"top": 185, "bottom": 200, "lithology": "shale", "formation": "Hermit Formation", "age": "Permian"},
]

# Lithology pattern definitions (for Highcharts pattern-fill module)
lithology_config = {
    "sandstone": {
        "name": "Sandstone",
        "color": {
            "pattern": {
                "path": {
                    "d": "M 3 3 a 1.5 1.5 0 1 0 0.01 0 M 9 8 a 1.5 1.5 0 1 0 0.01 0 "
                    "M 6 1 a 1 1 0 1 0 0.01 0 M 1 10 a 1 1 0 1 0 0.01 0 "
                    "M 11 4 a 1.2 1.2 0 1 0 0.01 0",
                    "stroke": "#8B7355",
                    "strokeWidth": 2.5,
                    "fill": "#8B7355",
                },
                "width": 14,
                "height": 14,
                "backgroundColor": "#F5DEB3",
            }
        },
    },
    "shale": {
        "name": "Shale",
        "color": {
            "pattern": {
                "path": {
                    "d": "M 0 4 L 18 4 M 2 9 L 11 9 M 13 9 L 18 9 M 0 14 L 7 14 M 9 14 L 16 14",
                    "stroke": "#555555",
                    "strokeWidth": 1.8,
                },
                "width": 18,
                "height": 18,
                "backgroundColor": "#B8B8B8",
            }
        },
    },
    "limestone": {
        "name": "Limestone",
        "color": {
            "pattern": {
                "path": {
                    "d": "M 0 0 L 20 0 M 0 10 L 20 10 M 10 0 L 10 10 M 0 10 L 0 20 M 20 10 L 20 20",
                    "stroke": "#4A7A8C",
                    "strokeWidth": 2,
                },
                "width": 20,
                "height": 20,
                "backgroundColor": "#B8D4E3",
            }
        },
    },
    "siltstone": {
        "name": "Siltstone",
        "color": {
            "pattern": {
                "path": {
                    "d": "M 1 4 L 6 4 M 9 4 L 13 4 M 3 9 L 8 9 M 10 9 L 15 9 M 0 14 L 5 14 M 7 14 L 11 14",
                    "stroke": "#7A6B54",
                    "strokeWidth": 1.8,
                },
                "width": 16,
                "height": 18,
                "backgroundColor": "#D2C4A5",
            }
        },
    },
    "conglomerate": {
        "name": "Conglomerate",
        "color": {
            "pattern": {
                "path": {
                    "d": "M 8 8 m -5 0 a 5 5 0 1 0 10 0 a 5 5 0 1 0 -10 0 "
                    "M 20 18 m -3.5 0 a 3.5 3.5 0 1 0 7 0 a 3.5 3.5 0 1 0 -7 0 "
                    "M 19 5 m -2.5 0 a 2.5 2.5 0 1 0 5 0 a 2.5 2.5 0 1 0 -5 0",
                    "stroke": "#5C3A6E",
                    "strokeWidth": 2,
                    "fill": "none",
                },
                "width": 26,
                "height": 26,
                "backgroundColor": "#C4A0D4",
            }
        },
    },
}

# Group layers by lithology for legend
lithology_groups = OrderedDict()
for layer in layers:
    lith = layer["lithology"]
    if lith not in lithology_groups:
        lithology_groups[lith] = []
    lithology_groups[lith].append(layer)

# Age boundaries for geological period labels
age_bands = [
    {"from": 0, "to": 18, "label": "Cretaceous", "color": "rgba(76, 175, 80, 0.06)"},
    {"from": 18, "to": 100, "label": "Jurassic", "color": "rgba(33, 150, 243, 0.06)"},
    {"from": 100, "to": 142, "label": "Triassic", "color": "rgba(255, 152, 0, 0.06)"},
    {"from": 142, "to": 200, "label": "Permian", "color": "rgba(156, 39, 176, 0.06)"},
]

# Build chart configuration
chart_config = {
    "chart": {
        "type": "columnrange",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#FAFAF8",
        "marginLeft": 340,
        "marginRight": 480,
        "marginTop": 200,
        "marginBottom": 130,
        "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    },
    "title": {
        "text": "column-stratigraphic \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "bold", "color": "#2C3E50"},
    },
    "subtitle": {
        "text": "Synthetic Sedimentary Section \u2014 Colorado Plateau Stratigraphy",
        "style": {"fontSize": "34px", "color": "#7F8C8D"},
    },
    "xAxis": {"visible": False, "min": -0.25, "max": 1.3},
    "yAxis": {
        "reversed": True,
        "title": {
            "text": "Depth (m)",
            "style": {"fontSize": "42px", "color": "#2C3E50", "fontWeight": "600"},
            "margin": 30,
        },
        "labels": {"style": {"fontSize": "32px", "color": "#444444"}, "format": "{value}"},
        "min": 0,
        "max": 204,
        "tickInterval": 20,
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0, 0, 0, 0.06)",
        "lineWidth": 2,
        "lineColor": "#CCCCCC",
        "plotBands": [
            {
                "from": band["from"],
                "to": band["to"],
                "color": band["color"],
                "label": {
                    "text": band["label"],
                    "align": "left",
                    "x": -160,
                    "verticalAlign": "middle",
                    "rotation": 270,
                    "style": {"fontSize": "30px", "fontWeight": "bold", "color": "#555555"},
                },
            }
            for band in age_bands
        ],
        "plotLines": [
            {"value": boundary, "color": "rgba(0, 0, 0, 0.35)", "width": 3, "dashStyle": "Dash", "zIndex": 5}
            for boundary in [18, 100, 142]
        ],
    },
    "legend": {
        "enabled": True,
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "x": -30,
        "y": 0,
        "itemStyle": {"fontSize": "30px", "color": "#333333"},
        "symbolHeight": 28,
        "symbolWidth": 28,
        "itemMarginBottom": 18,
        "title": {"text": "Lithology", "style": {"fontSize": "34px", "fontWeight": "bold", "color": "#2C3E50"}},
        "backgroundColor": "rgba(255, 255, 255, 0.7)",
        "borderRadius": 8,
        "padding": 20,
    },
    "tooltip": {
        "style": {"fontSize": "26px"},
        "headerFormat": "",
        "pointFormat": (
            "<b>{point.custom.formation}</b><br/>"
            "{series.name}<br/>"
            "Depth: {point.low} \u2013 {point.high} m<br/>"
            "Thickness: {point.custom.thickness} m"
        ),
    },
    "credits": {"enabled": False},
    "plotOptions": {"columnrange": {"grouping": False, "borderRadius": 0}},
    "series": [],
}

# Build series - one per lithology type
for lith, layer_list in lithology_groups.items():
    config = lithology_config[lith]
    data_points = []
    for layer in layer_list:
        thickness = layer["bottom"] - layer["top"]
        data_points.append(
            {
                "x": 0,
                "low": layer["top"],
                "high": layer["bottom"],
                "custom": {"formation": layer["formation"], "thickness": thickness},
            }
        )

    chart_config["series"].append(
        {
            "type": "columnrange",
            "name": config["name"],
            "data": data_points,
            "color": config["color"],
            "borderColor": "#2C3E50",
            "borderWidth": 2.5,
            "pointWidth": 2200,
        }
    )

# Add formation name labels as a scatter series positioned to the right of the column
formation_labels = []
for layer in layers:
    mid_depth = (layer["top"] + layer["bottom"]) / 2
    formation_labels.append({"x": 0.68, "y": mid_depth, "name": layer["formation"]})

chart_config["series"].append(
    {
        "type": "scatter",
        "name": "Formations",
        "data": formation_labels,
        "showInLegend": False,
        "enableMouseTracking": False,
        "marker": {"enabled": False},
        "dataLabels": {
            "enabled": True,
            "format": "{point.name}",
            "align": "left",
            "x": 10,
            "y": 4,
            "style": {"fontSize": "30px", "fontWeight": "600", "color": "#2C3E50", "textOutline": "3px #FAFAF8"},
            "overflow": "allow",
            "crop": False,
        },
    }
)

# Generate JavaScript - using raw JSON config because highcharts-core cannot
# serialize SVG pattern path objects needed for lithology fills
chart = Chart(container="container")
js_config = json.dumps(chart_config, ensure_ascii=False)
js_code = f"Highcharts.chart('{chart.container}', {js_config});"

# Load Highcharts JS modules
highcharts_base = Path(__file__).resolve().parents[3] / "node_modules" / "highcharts"
modules = {}
for name, filename in [
    ("highcharts", "highcharts.js"),
    ("more", "highcharts-more.js"),
    ("pattern", "modules/pattern-fill.js"),
]:
    local_path = highcharts_base / filename
    if local_path.exists():
        modules[name] = local_path.read_text(encoding="utf-8")
    else:
        url = f"https://code.highcharts.com/{filename}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            modules[name] = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{modules["highcharts"]}</script>
    <script>{modules["more"]}</script>
    <script>{modules["pattern"]}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_code}</script>
</body>
</html>"""

# Screenshot with headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <script src="https://code.highcharts.com/modules/pattern-fill.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{js_code}</script>
</body>
</html>"""
    f.write(interactive_html)
