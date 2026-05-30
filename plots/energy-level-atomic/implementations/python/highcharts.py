""" anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-30
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette (hybrid-v3 sort order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data - Hydrogen atom energy levels: E_n = -13.6/n² eV
energy_levels = {1: -13.60, 2: -3.40, 3: -1.51, 4: -0.85, 5: -0.54, 6: -0.38}

# Spectral series transitions (emission: n_upper → n_lower)
lyman_series = [(n, 1) for n in range(2, 7)]
balmer_series = [(n, 2) for n in range(3, 7)]
paschen_series = [(n, 3) for n in range(4, 7)]

# Wavelength labels for alpha transitions: λ = 1240 / ΔE (nm)
alpha_wavelengths = {}
for series in [lyman_series, balmer_series, paschen_series]:
    n_u, n_l = series[0]
    delta_e = abs(energy_levels[n_u] - energy_levels[n_l])
    alpha_wavelengths[(n_u, n_l)] = f"{1240 / delta_e:.0f} nm"

# Title: "energy-level-atomic · python · highcharts · anyplot.ai" = 54 chars < 67, use default 66px
title = "energy-level-atomic · python · highcharts · anyplot.ai"

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Segoe UI', Arial, Helvetica, sans-serif", "color": INK},
    "marginRight": 380,
    "marginLeft": 160,
    "marginTop": 160,
    "marginBottom": 160,
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "700", "color": INK}, "margin": 20}

chart.options.subtitle = {
    "text": "Hydrogen Atom Energy Levels and Spectral Transitions",
    "style": {"fontSize": "44px", "fontWeight": "400", "color": INK_SOFT},
}

chart.options.x_axis = {"visible": False, "min": 0, "max": 11}

BAND_BG_GROUND = "rgba(26,26,23,0.04)" if THEME == "light" else "rgba(240,239,232,0.04)"
BAND_BG_EXCITED = "rgba(68,103,163,0.05)" if THEME == "light" else "rgba(68,103,163,0.08)"

chart.options.y_axis = {
    "title": {"text": "Energy (eV)", "style": {"fontSize": "56px", "fontWeight": "600", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "format": "{value}"},
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": INK_SOFT,
    "min": -14.2,
    "max": 0.6,
    "tickPositions": [-14, -13, -3, -2, -1, 0],
    "tickWidth": 2,
    "tickLength": 10,
    "tickColor": INK_SOFT,
    "startOnTick": False,
    "endOnTick": False,
    "breaks": [{"from": -12.5, "to": -3.6, "breakSize": 0.10}],
    "plotBands": [
        {
            "from": -14.2,
            "to": -12.5,
            "color": BAND_BG_GROUND,
            "label": {
                "text": "Ground state",
                "align": "left",
                "x": 10,
                "style": {"fontSize": "34px", "color": INK_SOFT, "fontStyle": "italic"},
            },
        },
        {
            "from": -3.6,
            "to": 0.6,
            "color": BAND_BG_EXCITED,
            "label": {
                "text": "Excited states → Continuum",
                "align": "right",
                "verticalAlign": "top",
                "x": -10,
                "y": 10,
                "style": {"fontSize": "34px", "color": INK_SOFT, "fontStyle": "italic"},
            },
        },
    ],
}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "itemStyle": {"fontSize": "44px", "fontWeight": "500", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 0,
    "symbolWidth": 60,
    "symbolHeight": 6,
    "itemMarginBottom": 10,
    "itemDistance": 80,
    "y": 10,
}

chart.options.tooltip = {
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "style": {"fontSize": "36px", "color": INK},
}

chart.options.plot_options = {"line": {"states": {"hover": {"lineWidthPlus": 0}}}, "series": {"animation": False}}

chart.options.credits = {"enabled": False}

# Energy level lines — span partial width as per spec
level_x_start = 1.0
level_x_end = 9.5

# Y-offsets (px) to stagger labels for closely-spaced upper levels (n=4-6)
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
                        "style": {"fontSize": "36px", "fontWeight": "600", "color": INK, "textOutline": "none"},
                    },
                },
            ],
            "color": INK,
            "lineWidth": 6,
            "marker": {"enabled": False},
            "enableMouseTracking": False,
            "showInLegend": False,
        }
    )

# Ionization limit at 0 eV (dashed reference line)
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
                    "y": -12,
                    "crop": False,
                    "overflow": "allow",
                    "style": {"fontSize": "34px", "fontWeight": "bold", "color": INK_SOFT, "textOutline": "none"},
                },
            },
        ],
        "color": INK_SOFT,
        "lineWidth": 3,
        "dashStyle": "Dash",
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Transition arrows grouped by spectral series — Imprint palette positions 1-3
transition_groups = [
    ("Lyman Series (UV)", lyman_series, IMPRINT_PALETTE[0], 2.5, "lyman"),
    ("Balmer Series (Visible)", balmer_series, IMPRINT_PALETTE[1], 5.0, "balmer"),
    ("Paschen Series (IR)", paschen_series, IMPRINT_PALETTE[2], 7.5, "paschen"),
]

for group_name, transitions, color, base_x, group_id in transition_groups:
    spacing = 0.55
    offset = -(len(transitions) - 1) * spacing / 2
    for j, (n_upper, n_lower) in enumerate(transitions):
        x_pos = base_x + offset + j * spacing
        upper_e = energy_levels[n_upper]
        lower_e = energy_levels[n_lower]
        is_first = j == 0
        is_alpha = (n_upper, n_lower) in alpha_wavelengths
        delta_e = abs(upper_e - lower_e)

        upper_point = {
            "x": x_pos,
            "y": upper_e,
            "marker": {
                "enabled": True,
                "symbol": "circle",
                "radius": 13 if is_alpha else 10,
                "fillColor": color,
                "lineColor": color,
            },
        }

        if is_alpha:
            upper_point["dataLabels"] = {
                "enabled": True,
                "format": f"λ = {alpha_wavelengths[(n_upper, n_lower)]}",
                "align": "left",
                "verticalAlign": "middle",
                "x": 18,
                "y": -16,
                "crop": False,
                "overflow": "allow",
                "style": {
                    "fontSize": "32px",
                    "fontStyle": "italic",
                    "fontWeight": "bold",
                    "color": color,
                    "textOutline": f"3px {PAGE_BG}",
                },
            }

        lower_point = {
            "x": x_pos,
            "y": lower_e,
            "marker": {
                "enabled": True,
                "symbol": "triangle-down",
                "radius": 18 if is_alpha else 14,
                "fillColor": color,
                "lineColor": color,
            },
        }

        entry = {
            "type": "line",
            "name": group_name,
            "data": [upper_point, lower_point],
            "color": color,
            "lineWidth": 6 if is_alpha else 4,
            "showInLegend": is_first,
            "tooltip": {"headerFormat": "", "pointFormat": f"n={n_upper} → n={n_lower}<br/>ΔE = {delta_e:.2f} eV"},
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
    except Exception:
        time.sleep(2)
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from all CDNs")

# Download broken-axis module for y-axis break
broken_axis_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/broken-axis.js",
    "https://code.highcharts.com/modules/broken-axis.js",
]
broken_axis_js = None
for url in broken_axis_urls:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            broken_axis_js = response.read().decode("utf-8")
        break
    except Exception:
        time.sleep(2)
        continue
if broken_axis_js is None:
    raise RuntimeError("Failed to download broken-axis.js from all CDNs")

js_literal = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{broken_axis_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome with CDP viewport override
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone is eaten by Chrome chrome (~139 px)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 — guards against occasional ±1–2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
