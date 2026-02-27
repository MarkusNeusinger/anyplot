""" pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: highcharts unknown | Python 3.14.3
Quality: 80/100 | Created: 2026-02-27
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Hydrogen atom energy levels: E_n = -13.6/n² eV
energy_levels = {1: -13.60, 2: -3.40, 3: -1.51, 4: -0.85, 5: -0.54, 6: -0.38}

# Spectral series transitions (emission: n_upper -> n_lower)
lyman_series = [(n, 1) for n in range(2, 7)]
balmer_series = [(n, 2) for n in range(3, 7)]
paschen_series = [(n, 3) for n in range(4, 7)]

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "Arial, Helvetica, sans-serif"},
    "marginRight": 350,
    "marginLeft": 160,
    "marginTop": 200,
    "marginBottom": 200,
}

chart.options.title = {
    "text": "energy-level-atomic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": "#333333"},
}

chart.options.subtitle = {
    "text": "Hydrogen Atom Energy Levels and Spectral Transitions",
    "style": {"fontSize": "40px", "color": "#666666"},
}

chart.options.x_axis = {"visible": False, "min": 0, "max": 11}

chart.options.y_axis = {
    "title": {"text": "Energy (eV)", "style": {"fontSize": "40px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "32px", "color": "#333333"}, "format": "{value}"},
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#cccccc",
    "min": -14.5,
    "max": 0.8,
    "tickInterval": 2,
    "startOnTick": False,
    "endOnTick": False,
}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal", "color": "#333333"},
    "symbolWidth": 50,
    "symbolHeight": 4,
    "itemMarginBottom": 10,
    "y": 10,
}

chart.options.tooltip = {"style": {"fontSize": "32px"}}

chart.options.plot_options = {"line": {"states": {"hover": {"lineWidthPlus": 0}}}, "series": {"animation": False}}

chart.options.credits = {"enabled": False}

# Energy level lines
level_x_start = 1.0
level_x_end = 9.5

# Y-offsets (px) to prevent label overlap for closely-spaced upper levels
label_y_offsets = {1: 0, 2: 0, 3: 0, 4: 20, 5: 0, 6: -20}

for n, energy in energy_levels.items():
    label_text = f"n={n}  ({energy:.2f} eV)"
    chart.add_series(
        {
            "type": "line",
            "name": f"n={n}",
            "data": [
                {"x": level_x_start, "y": energy},
                {
                    "x": level_x_end,
                    "y": energy,
                    "dataLabels": {
                        "enabled": True,
                        "format": label_text,
                        "align": "left",
                        "verticalAlign": "middle",
                        "x": 20,
                        "y": label_y_offsets[n],
                        "crop": False,
                        "overflow": "allow",
                        "style": {"fontSize": "30px", "fontWeight": "bold", "color": "#333333", "textOutline": "none"},
                    },
                },
            ],
            "color": "#2c3e50",
            "lineWidth": 5,
            "marker": {"enabled": False},
            "enableMouseTracking": False,
            "showInLegend": False,
        }
    )

# Ionization limit at 0 eV (dashed red line)
chart.add_series(
    {
        "type": "line",
        "name": "Ionization Limit",
        "data": [
            {"x": level_x_start, "y": 0},
            {
                "x": level_x_end,
                "y": 0,
                "dataLabels": {
                    "enabled": True,
                    "format": "Ionization (0 eV)",
                    "align": "left",
                    "verticalAlign": "middle",
                    "x": 20,
                    "y": -10,
                    "crop": False,
                    "overflow": "allow",
                    "style": {"fontSize": "30px", "fontWeight": "bold", "color": "#e74c3c", "textOutline": "none"},
                },
            },
        ],
        "color": "#e74c3c",
        "lineWidth": 3,
        "dashStyle": "Dash",
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Transition arrows grouped by spectral series
transition_groups = [
    ("Lyman Series (UV)", lyman_series, "#8e44ad", 2.5, "lyman"),
    ("Balmer Series (Visible)", balmer_series, "#306998", 5.0, "balmer"),
    ("Paschen Series (IR)", paschen_series, "#c0392b", 7.5, "paschen"),
]

for group_name, transitions, color, base_x, group_id in transition_groups:
    spacing = 0.55
    offset = -(len(transitions) - 1) * spacing / 2
    for j, (n_upper, n_lower) in enumerate(transitions):
        x_pos = base_x + offset + j * spacing
        upper_e = energy_levels[n_upper]
        lower_e = energy_levels[n_lower]
        is_first = j == 0
        delta_e = abs(upper_e - lower_e)
        entry = {
            "type": "line",
            "name": group_name,
            "data": [
                {
                    "x": x_pos,
                    "y": upper_e,
                    "marker": {
                        "enabled": True,
                        "symbol": "circle",
                        "radius": 8,
                        "fillColor": color,
                        "lineColor": color,
                    },
                },
                {
                    "x": x_pos,
                    "y": lower_e,
                    "marker": {
                        "enabled": True,
                        "symbol": "triangle-down",
                        "radius": 14,
                        "fillColor": color,
                        "lineColor": color,
                    },
                },
            ],
            "color": color,
            "lineWidth": 4,
            "showInLegend": is_first,
            "tooltip": {
                "headerFormat": "",
                "pointFormat": f"n={n_upper} \u2192 n={n_lower}<br/>\u0394E = {delta_e:.2f} eV",
            },
        }
        if is_first:
            entry["id"] = group_id
        else:
            entry["linkedTo"] = group_id
        chart.add_series(entry)

# Download Highcharts JS (try multiple CDNs)
cdn_urls = ["https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js", "https://code.highcharts.com/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except urllib.error.HTTPError:
        time.sleep(2)
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from all CDNs")

# Generate JS literal
js_literal = chart.to_js_literal()

# Inline HTML for rendering
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Standalone HTML for interactive viewing (CDN links)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
</head>
<body style="margin:0; overflow:auto;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
