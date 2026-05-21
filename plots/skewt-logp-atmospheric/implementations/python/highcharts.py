"""anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: highcharts unknown | Python 3.13.13
Quality: 78/100 | Updated: 2026-05-21
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
PAGE_BG_RGB = (250, 248, 241) if THEME == "light" else (26, 26, 23)
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
TEMP_COLOR = "#009E73"  # green — temperature profile (first/primary)
DEW_COLOR = "#D55E00"  # vermillion — dewpoint profile
DRY_AD_COLOR = "#0072B2"  # blue — dry adiabats
MOIST_AD_COLOR = "#CC79A7"  # pink — moist adiabats
MIX_COLOR = "#E69F00"  # orange — mixing ratio lines

# Pressure/temperature extents
TEMP_MIN, TEMP_MAX = -80, 50
P_MIN, P_MAX = 100, 1000
LOG_PMIN = np.log10(P_MIN)  # 2.0
LOG_PMAX = np.log10(P_MAX)  # 3.0
LOG_PRANGE = LOG_PMAX - LOG_PMIN  # 1.0
SKEW_FACTOR = float(TEMP_MAX - TEMP_MIN)  # 130.0 °C — full-width skew

# Sounding data — standard atmospheric profile
np.random.seed(42)
pressure = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100])
temperature = np.array([28, 22, 15, 4, -18, -32, -45, -52, -56, -56, -55])
dewpoint = np.array([20, 16, 10, -2, -25, -42, -55, -62, -70, -75, -80])

# Reference pressure array for background lines
p_fine = np.linspace(P_MAX, P_MIN, 80)
yfrac_fine = (np.log10(p_fine) - LOG_PMIN) / LOG_PRANGE  # 0=top(100 hPa), 1=bottom(1000 hPa)

# Sounding yfrac for profile data
yfrac_s = (np.log10(pressure) - LOG_PMIN) / LOG_PRANGE

# Download Highcharts JS (required — headless Chrome cannot load CDN from file://)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Create Highcharts chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "plotBackgroundColor": ELEVATED_BG,
    "marginLeft": 150,
    "marginRight": 80,
    "marginTop": 110,
    "marginBottom": 130,
    "style": {"fontFamily": "Arial, sans-serif"},
}

chart.options.title = {
    "text": "skewt-logp-atmospheric · python · highcharts · anyplot.ai",
    "style": {"fontSize": "56px", "color": INK, "fontWeight": "bold"},
    "margin": 20,
}

chart.options.subtitle = {"text": ""}

# X-axis: skewed temperature coordinates
# At P_MAX=1000 hPa (bottom): x = T (no skew offset)
# At P_MIN=100 hPa (top): x = T - 130 (full SKEW_FACTOR offset leftward)
# Tick positions at 1000 hPa, where x == T exactly
x_tick_positions = [float(t) for t in range(-80, 60, 10)]

chart.options.x_axis = {
    "min": TEMP_MIN - SKEW_FACTOR,  # -210
    "max": float(TEMP_MAX),  # 50
    "startOnTick": False,
    "endOnTick": False,
    "tickPositions": x_tick_positions,
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "48px", "color": INK_SOFT}, "margin": 14},
    "labels": {"style": {"fontSize": "40px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 0,
}

# Y-axis: pressure (hPa), logarithmic, reversed (1000 hPa at bottom)
isobar_pressures = [1000, 850, 700, 500, 400, 300, 200, 150, 100]

chart.options.y_axis = {
    "type": "logarithmic",
    "reversed": True,
    "min": P_MIN,
    "max": P_MAX,
    "startOnTick": False,
    "endOnTick": False,
    "tickPositions": isobar_pressures,
    "allowDecimals": False,
    "title": {"text": "Pressure (hPa)", "style": {"fontSize": "48px", "color": INK_SOFT}, "margin": 14},
    "labels": {"style": {"fontSize": "40px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineOpacity": 0.45,
    "minorGridLineWidth": 0,
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"color": INK, "fontSize": "40px", "fontWeight": "normal"},
    "itemHoverStyle": {"color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 8,
    "padding": 20,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "symbolWidth": 60,
    "symbolHeight": 8,
}

chart.options.tooltip = {"enabled": False}

chart.options.plot_options = {
    "line": {
        "animation": False,
        "enableMouseTracking": False,
        "marker": {"enabled": False},
        "states": {"hover": {"enabled": False}},
    }
}

chart.options.credits = {"enabled": False}

# ── Series ──────────────────────────────────────────────────────────────────

# 1. Isotherms (skewed, every 10°C, gray dashed — background layer)
for idx, t_val in enumerate(np.arange(-80, 60, 10)):
    x_arr = float(t_val) - (1 - yfrac_fine) * SKEW_FACTOR
    pts = [[float(x), float(p)] for x, p in zip(x_arr, p_fine, strict=False)]
    s = LineSeries()
    s.data = pts
    s.color = INK_SOFT
    s.line_width = 1
    s.dash_style = "Dash"
    s.opacity = 0.35
    if idx == 0:
        s.id = "isotherms"
        s.name = "Isotherm"
        s.show_in_legend = True
    else:
        s.linked_to = "isotherms"
        s.show_in_legend = False
    chart.add_series(s)

# 2. Dry adiabats (Poisson equation, blue solid thin)
for idx, st in enumerate(np.arange(-40, 60, 10)):
    p_arr = np.linspace(P_MAX, P_MIN, 60)
    theta = st + 273.15
    t_arr = theta * (p_arr / 1000) ** 0.286 - 273.15
    mask = np.isfinite(t_arr)
    p_m, t_m = p_arr[mask], t_arr[mask]
    if len(p_m) < 2:
        continue
    yfrac_m = (np.log10(p_m) - LOG_PMIN) / LOG_PRANGE
    x_m = t_m - (1 - yfrac_m) * SKEW_FACTOR
    pts = [[float(x), float(p)] for x, p in zip(x_m, p_m, strict=False)]
    s = LineSeries()
    s.data = pts
    s.color = DRY_AD_COLOR
    s.line_width = 1.5
    s.opacity = 0.60
    if idx == 0:
        s.id = "dry_adiabats"
        s.name = "Dry Adiabat"
        s.show_in_legend = True
    else:
        s.linked_to = "dry_adiabats"
        s.show_in_legend = False
    chart.add_series(s)

# 3. Moist adiabats (~6 K/100 hPa saturated lapse rate, pink dashed thin)
for idx, st in enumerate(np.arange(-20, 40, 10)):
    p_arr = np.linspace(P_MAX, P_MIN, 60)
    t_arr = np.zeros(len(p_arr))
    t_arr[0] = float(st)
    for j in range(1, len(p_arr)):
        dp = p_arr[j - 1] - p_arr[j]
        t_arr[j] = t_arr[j - 1] - 0.6 * dp / 10
    mask = np.isfinite(t_arr)
    p_m, t_m = p_arr[mask], t_arr[mask]
    if len(p_m) < 2:
        continue
    yfrac_m = (np.log10(p_m) - LOG_PMIN) / LOG_PRANGE
    x_m = t_m - (1 - yfrac_m) * SKEW_FACTOR
    pts = [[float(x), float(p)] for x, p in zip(x_m, p_m, strict=False)]
    s = LineSeries()
    s.data = pts
    s.color = MOIST_AD_COLOR
    s.line_width = 1.5
    s.dash_style = "Dash"
    s.opacity = 0.55
    if idx == 0:
        s.id = "moist_adiabats"
        s.name = "Moist Adiabat"
        s.show_in_legend = True
    else:
        s.linked_to = "moist_adiabats"
        s.show_in_legend = False
    chart.add_series(s)

# 4. Mixing ratio lines (vapor pressure formula, orange dotted thin)
for idx, mr in enumerate([1, 2, 4, 8, 16, 32]):
    p_arr = np.linspace(P_MAX, 200, 40)
    e_arr = mr * p_arr / (622 + mr)
    ln_ratio = np.log(e_arr / 6.112)
    td_arr = 243.5 * ln_ratio / (17.67 - ln_ratio)
    mask = np.isfinite(td_arr) & (td_arr >= TEMP_MIN - 5)
    p_m, td_m = p_arr[mask], td_arr[mask]
    if len(p_m) < 2:
        continue
    yfrac_m = (np.log10(p_m) - LOG_PMIN) / LOG_PRANGE
    x_m = td_m - (1 - yfrac_m) * SKEW_FACTOR
    pts = [[float(x), float(p)] for x, p in zip(x_m, p_m, strict=False)]
    s = LineSeries()
    s.data = pts
    s.color = MIX_COLOR
    s.line_width = 1.5
    s.dash_style = "Dot"
    s.opacity = 0.60
    if idx == 0:
        s.id = "mixing_ratios"
        s.name = "Mixing Ratio"
        s.show_in_legend = True
    else:
        s.linked_to = "mixing_ratios"
        s.show_in_legend = False
    chart.add_series(s)

# 5. Temperature profile — #009E73 (first Okabe-Ito; primary series)
x_temp = temperature - (1 - yfrac_s) * SKEW_FACTOR
temp_data = [[float(x), float(p)] for x, p in zip(x_temp, pressure, strict=False)]
temp_series = LineSeries()
temp_series.data = temp_data
temp_series.name = "Temperature"
temp_series.show_in_legend = True
temp_series.color = TEMP_COLOR
temp_series.line_width = 6
temp_series.marker = {
    "enabled": True,
    "radius": 10,
    "symbol": "circle",
    "fillColor": TEMP_COLOR,
    "lineWidth": 2,
    "lineColor": PAGE_BG,
}
temp_series.z_index = 10
chart.add_series(temp_series)

# 6. Dewpoint profile — #D55E00, dashed thick
x_dew = dewpoint - (1 - yfrac_s) * SKEW_FACTOR
dew_data = [[float(x), float(p)] for x, p in zip(x_dew, pressure, strict=False)]
dew_series = LineSeries()
dew_series.data = dew_data
dew_series.name = "Dewpoint"
dew_series.show_in_legend = True
dew_series.color = DEW_COLOR
dew_series.line_width = 6
dew_series.dash_style = "Dash"
dew_series.marker = {
    "enabled": True,
    "radius": 10,
    "symbol": "circle",
    "fillColor": DEW_COLOR,
    "lineWidth": 2,
    "lineColor": PAGE_BG,
}
dew_series.z_index = 10
chart.add_series(dew_series)

# ── Export ──────────────────────────────────────────────────────────────────

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG_RGB)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
