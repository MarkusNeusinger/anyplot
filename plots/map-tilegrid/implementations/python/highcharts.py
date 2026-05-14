"""anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-14
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data
np.random.seed(42)

# US state tile grid layout: state -> (row, col), row 0 = north, col 0 = west
state_grid = {
    "ME": (0, 11),
    "WA": (1, 1),
    "ID": (1, 2),
    "MT": (1, 3),
    "ND": (1, 4),
    "MN": (1, 5),
    "WI": (1, 6),
    "MI": (1, 7),
    "NY": (1, 9),
    "VT": (1, 10),
    "NH": (1, 11),
    "OR": (2, 1),
    "NV": (2, 2),
    "WY": (2, 3),
    "SD": (2, 4),
    "IA": (2, 5),
    "IL": (2, 6),
    "IN": (2, 7),
    "OH": (2, 8),
    "PA": (2, 9),
    "NJ": (2, 10),
    "CT": (2, 11),
    "MA": (2, 12),
    "AK": (3, 0),
    "CA": (3, 1),
    "UT": (3, 2),
    "CO": (3, 3),
    "NE": (3, 4),
    "MO": (3, 5),
    "KY": (3, 6),
    "WV": (3, 7),
    "VA": (3, 8),
    "MD": (3, 9),
    "DE": (3, 10),
    "RI": (3, 11),
    "HI": (4, 0),
    "AZ": (4, 2),
    "NM": (4, 3),
    "KS": (4, 4),
    "AR": (4, 5),
    "TN": (4, 6),
    "NC": (4, 7),
    "SC": (4, 8),
    "DC": (4, 9),
    "TX": (5, 3),
    "OK": (5, 4),
    "LA": (5, 5),
    "MS": (5, 6),
    "AL": (5, 7),
    "GA": (5, 8),
    "FL": (5, 9),
}

# Renewable energy share (%) — synthetic but regionally plausible
renewable_pct = {state: round(np.random.uniform(18, 62), 1) for state in state_grid}
regional_overrides = [
    ("WA", 75, 90),
    ("OR", 65, 80),
    ("ID", 55, 70),
    ("MT", 45, 65),
    ("VT", 52, 70),
    ("ME", 48, 62),
    ("NH", 32, 48),
    ("CA", 52, 68),
    ("WV", 5, 15),
    ("KY", 8, 18),
    ("WY", 10, 22),
    ("MS", 8, 18),
    ("AL", 10, 22),
    ("LA", 12, 22),
    ("GA", 15, 28),
    ("FL", 18, 30),
    ("TX", 25, 40),
]
for state, lo, hi in regional_overrides:
    renewable_pct[state] = round(np.random.uniform(lo, hi), 1)

max_row = max(r for r, _ in state_grid.values())

# Flip rows so that row 0 (north) appears at top (high y in Highcharts)
# Use simple [x, y, value] arrays — name is injected via JS formatter lookup
heatmap_data = [[col, max_row - row, renewable_pct[state]] for state, (row, col) in state_grid.items()]

# Build JS lookup: "col_flippedrow" -> state abbreviation
label_lookup = {f"{col}_{max_row - row}": state for state, (row, col) in state_grid.items()}
lookup_entries = ", ".join(f'"{k}": "{v}"' for k, v in label_lookup.items())
label_lookup_js = "{" + lookup_entries + "}"

# Plot
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginTop": 220,
    "marginBottom": 80,
    "marginLeft": 60,
    "marginRight": 340,
    "style": {"color": INK},
}

chart.options.title = {
    "text": "map-tilegrid · highcharts · anyplot.ai",
    "style": {"fontSize": "56px", "fontWeight": "500", "color": INK},
    "margin": 20,
}

chart.options.subtitle = {
    "text": "Renewable Energy Share by U.S. State — equal-area tile grid",
    "style": {"fontSize": "34px", "color": INK_SOFT},
}

chart.options.x_axis = {"visible": False, "min": -0.5, "max": 12.5}

chart.options.y_axis = {"visible": False, "min": -0.5, "max": max_row + 0.5}

chart.options.color_axis = {
    "min": 0,
    "max": 100,
    "stops": [[0, "#440154"], [0.25, "#3B528B"], [0.5, "#21908C"], [0.75, "#5DC863"], [1.0, "#FDE725"]],
    "labels": {"format": "{value}%", "style": {"fontSize": "22px", "color": INK_SOFT}},
}

chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "margin": 40,
    "symbolHeight": 500,
    "title": {"text": "Renewable %", "style": {"fontSize": "26px", "color": INK, "fontWeight": "bold"}},
    "itemStyle": {"color": INK_SOFT, "fontSize": "22px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 16,
}

label_formatter = f"""function() {{
    var lookup = {label_lookup_js};
    return lookup[this.point.x + '_' + this.point.y] || '';
}}"""

chart.options.series = [
    {
        "type": "heatmap",
        "name": "Renewable Energy %",
        "data": heatmap_data,
        "borderWidth": 5,
        "borderColor": PAGE_BG,
        "dataLabels": {
            "enabled": True,
            "formatter": label_formatter,
            "style": {
                "fontSize": "40px",
                "fontWeight": "bold",
                "color": "#FFFFFF",
                "textOutline": "3px rgba(0,0,0,0.7)",
            },
        },
    }
]

chart.options.tooltip = {
    "formatter": """function() {
        return '<b>' + this.point.name + '</b><br>Renewable: <b>' +
            Highcharts.numberFormat(this.point.value, 1) + '%</b>';
    }"""
}

chart.options.credits = {"enabled": False}

# Download Highcharts + heatmap module (User-Agent required; fallback CDN)
_HC_URLS = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
_HM_URLS = [
    "https://code.highcharts.com/modules/heatmap.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js",
]

highcharts_js = None
for url in _HC_URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS")

heatmap_js = None
for url in _HM_URLS:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            heatmap_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if heatmap_js is None:
    raise RuntimeError("Failed to download Highcharts heatmap module")

# Save
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>{html_str}</script>
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
