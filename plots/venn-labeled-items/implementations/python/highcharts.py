""" anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: highcharts unknown | Python 3.14.4
Quality: 85/100 | Created: 2026-04-25
"""

import json
import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical palette: first series is brand green
CIRCLE_COLORS = ["#009E73", "#D55E00", "#0072B2"]
CIRCLE_FILLS = ["rgba(0,158,115,0.22)", "rgba(213,94,0,0.22)", "rgba(0,114,178,0.22)"]

# Editorial Chartgeist-style commentary on tech/culture
circles = [{"name": "Overhyped"}, {"name": "Actually Useful"}, {"name": "Secretly Loved"}]

items = [
    {"label": "NFTs", "zone": "A"},
    {"label": "Crypto Bros", "zone": "A"},
    {"label": "Metaverse", "zone": "A"},
    {"label": "Google Maps", "zone": "B"},
    {"label": "VS Code", "zone": "B"},
    {"label": "Dishwasher", "zone": "B"},
    {"label": "ABBA", "zone": "C"},
    {"label": "Slippers", "zone": "C"},
    {"label": "Crocs", "zone": "C"},
    {"label": "ChatGPT", "zone": "AB"},
    {"label": "Slack", "zone": "AB"},
    {"label": "Vinyl Records", "zone": "AC"},
    {"label": "Dolly Parton", "zone": "BC"},
    {"label": "Sourdough", "zone": "ABC"},
    {"label": "Beige Walls", "zone": "outside"},
]

# Three-circle symmetric Venn layout
radius = 1.0
center_dist = 0.55
angles = [math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3]
cx = [center_dist * math.cos(a) for a in angles]
cy = [center_dist * math.sin(a) for a in angles]

# Polygon vertices for each circle (closed shape with smooth curve approximation)
n_vertices = 240


def circle_polygon(center_x, center_y, r, n=n_vertices):
    return [
        [center_x + r * math.cos(2 * math.pi * i / n), center_y + r * math.sin(2 * math.pi * i / n)] for i in range(n)
    ]


# Per-zone anchor (x, y) — placed using exact circle geometry
zone_anchors = {
    "A": (0.0, 1.10),
    "B": (-0.95, -0.32),
    "C": (0.95, -0.32),
    "AB": (-0.52, 0.30),
    "AC": (0.52, 0.30),
    "BC": (0.0, -0.58),
    "ABC": (0.0, 0.05),
    "outside": (-2.20, 1.65),
}

# Vertical spread for items sharing a zone (data-coordinate offsets)
zone_offsets = {1: [0.0], 2: [0.13, -0.13], 3: [0.30, 0.0, -0.30]}

zones_grouped = {}
for it in items:
    zones_grouped.setdefault(it["zone"], []).append(it["label"])

# Build scatter points with per-point dataLabels
scatter_points = []
for zone, labels in zones_grouped.items():
    ax_, ay_ = zone_anchors[zone]
    offsets = zone_offsets[len(labels)]
    for label, dy in zip(labels, offsets, strict=False):
        scatter_points.append(
            {
                "x": round(ax_, 4),
                "y": round(ay_ + dy, 4),
                "name": label,
                "dataLabels": {
                    "enabled": True,
                    "format": label,
                    "align": "center",
                    "verticalAlign": "middle",
                    "y": -38,
                    "style": {
                        "fontSize": "42px",
                        "fontWeight": "600",
                        "fontFamily": "Georgia, 'Times New Roman', serif",
                        "color": INK,
                        "textOutline": f"4px {PAGE_BG}",
                    },
                },
            }
        )

# Category labels outside each circle, on the outer side
category_label_positions = [
    {
        "x": cx[0],
        "y": cy[0] + radius + 0.30,
        "name": circles[0]["name"].upper(),
        "color": CIRCLE_COLORS[0],
        "align": "center",
    },
    {
        "x": cx[1] - radius * 0.55,
        "y": cy[1] - radius - 0.18,
        "name": circles[1]["name"].upper(),
        "color": CIRCLE_COLORS[1],
        "align": "right",
    },
    {
        "x": cx[2] + radius * 0.55,
        "y": cy[2] - radius - 0.18,
        "name": circles[2]["name"].upper(),
        "color": CIRCLE_COLORS[2],
        "align": "left",
    },
]

# Build Highcharts config as a Python dict (serialized to JSON for the JS embed)
series_config = []

# Three filled circles as polygon series — color sets fill, lineColor sets stroke
for i in range(3):
    series_config.append(
        {
            "type": "polygon",
            "name": circles[i]["name"],
            "data": circle_polygon(cx[i], cy[i], radius),
            "color": CIRCLE_FILLS[i],
            "lineColor": CIRCLE_COLORS[i],
            "lineWidth": 6,
            "enableMouseTracking": False,
            "showInLegend": False,
            "states": {"inactive": {"opacity": 1}, "hover": {"enabled": False}},
        }
    )

# Items as one scatter series with per-point dataLabels
series_config.append(
    {
        "type": "scatter",
        "name": "Items",
        "data": scatter_points,
        "color": INK,
        "marker": {"radius": 9, "fillColor": INK, "lineWidth": 2, "lineColor": PAGE_BG, "symbol": "circle"},
        "showInLegend": False,
        "states": {"inactive": {"opacity": 1}, "hover": {"halo": None}},
    }
)

# Category labels rendered as a separate scatter series with bold dataLabels
for cat in category_label_positions:
    series_config.append(
        {
            "type": "scatter",
            "name": cat["name"],
            "data": [
                {
                    "x": cat["x"],
                    "y": cat["y"],
                    "dataLabels": {
                        "enabled": True,
                        "format": cat["name"],
                        "align": cat["align"],
                        "verticalAlign": "middle",
                        "y": 0,
                        "style": {
                            "fontSize": "68px",
                            "fontWeight": "700",
                            "fontFamily": "Georgia, 'Times New Roman', serif",
                            "color": cat["color"],
                            "textOutline": "none",
                            "letterSpacing": "3px",
                        },
                    },
                }
            ],
            "marker": {"enabled": False},
            "enableMouseTracking": False,
            "showInLegend": False,
        }
    )

# Subtle hint label for the "outside" cluster
series_config.append(
    {
        "type": "scatter",
        "name": "outside-hint",
        "data": [
            {
                "x": -2.20,
                "y": 1.95,
                "dataLabels": {
                    "enabled": True,
                    "format": "<i>Neither here nor there</i>",
                    "useHTML": True,
                    "align": "center",
                    "verticalAlign": "middle",
                    "style": {
                        "fontSize": "32px",
                        "fontFamily": "Georgia, 'Times New Roman', serif",
                        "color": INK_MUTED,
                        "fontStyle": "italic",
                        "textOutline": "none",
                    },
                },
            }
        ],
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

chart_config = {
    "chart": {
        "type": "scatter",
        "width": 3600,
        "height": 3600,
        "backgroundColor": PAGE_BG,
        "plotBackgroundColor": PAGE_BG,
        "plotBorderWidth": 0,
        "spacingTop": 80,
        "spacingRight": 80,
        "spacingBottom": 80,
        "spacingLeft": 80,
        "style": {"fontFamily": "Georgia, 'Times New Roman', serif"},
    },
    "title": {
        "text": "<b>CHARTGEIST</b> &middot; venn-labeled-items &middot; highcharts &middot; anyplot.ai",
        "useHTML": True,
        "style": {
            "fontSize": "62px",
            "fontFamily": "Georgia, 'Times New Roman', serif",
            "color": INK,
            "letterSpacing": "1px",
        },
        "align": "center",
        "margin": 24,
    },
    "subtitle": {
        "text": "<i>An entirely subjective taxonomy of things, ranked by vibe.</i>",
        "useHTML": True,
        "style": {
            "fontSize": "38px",
            "fontFamily": "Georgia, 'Times New Roman', serif",
            "color": INK_SOFT,
            "fontStyle": "italic",
        },
        "align": "center",
        "y": 110,
    },
    "xAxis": {
        "min": -2.9,
        "max": 2.9,
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickLength": 0,
        "labels": {"enabled": False},
        "title": {"text": ""},
        "startOnTick": False,
        "endOnTick": False,
    },
    "yAxis": {
        "min": -2.4,
        "max": 2.4,
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickLength": 0,
        "labels": {"enabled": False},
        "title": {"text": ""},
        "startOnTick": False,
        "endOnTick": False,
    },
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "tooltip": {
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderRadius": 8,
        "borderWidth": 1,
        "shadow": False,
        "style": {"fontSize": "22px", "color": INK, "fontFamily": "Georgia, 'Times New Roman', serif"},
        "headerFormat": "",
        "pointFormat": "<b>{point.name}</b>",
    },
    "plotOptions": {
        "series": {"animation": False, "states": {"inactive": {"opacity": 1}}},
        "polygon": {"trackByArea": False},
    },
    "series": series_config,
}

# Download Highcharts JS (headless Chrome cannot load CDN from file://)
# Polygon series requires highcharts-more.js in addition to the core
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
highcharts_more_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts-more.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

config_json = json.dumps(chart_config)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG}; overflow:hidden;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        Highcharts.chart('container', {config_json});
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3600, "height": 3600, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
