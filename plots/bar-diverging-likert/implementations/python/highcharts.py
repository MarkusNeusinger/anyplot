""" anyplot.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-01
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from highcharts_core.utility_classes.javascript_functions import CallbackFunction
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — semantic color mapping for Likert sentiment polarity
# positive→green (#009E73), negative→red (#AE3030), neutral→muted (theme-adaptive)
color_sd = "#AE3030"  # Strongly Disagree — semantic negative (Imprint matte red)
color_d = "#BD8233"  # Disagree — warm moderate-negative (Imprint ochre)
color_n = INK_MUTED  # Neutral — theme-adaptive muted gray
color_a = "#4467A3"  # Agree — cool moderate-positive (Imprint blue)
color_sa = "#009E73"  # Strongly Agree — semantic positive (Imprint brand green)

# Data — Employee Engagement Survey (8 questions, 5-point Likert scale)
# Columns: question, strongly_disagree, disagree, neutral, agree, strongly_agree
survey_data = [
    ("Clear career growth path", 18, 22, 15, 28, 17),
    ("Fair compensation", 25, 20, 12, 23, 20),
    ("Good work-life balance", 8, 12, 10, 35, 35),
    ("Supportive management", 12, 18, 14, 32, 24),
    ("Meaningful work", 5, 10, 8, 38, 39),
    ("Collaborative culture", 10, 15, 18, 33, 24),
    ("Adequate resources", 20, 25, 15, 25, 15),
    ("Effective communication", 15, 20, 18, 28, 19),
]

# Sort by net agreement ascending (lowest net at top of horizontal bar chart)
survey_data.sort(key=lambda r: (r[4] + r[5]) - (r[1] + r[2]))
categories = [r[0] for r in survey_data]

# Build per-series data (negative values = left/disagree, positive = right/agree)
# Neutral is split evenly across the center midpoint
sd_data, d_data, nl_data, nr_data, a_data, sa_data = [], [], [], [], [], []

for row in survey_data:
    _, sd, d, n, a, sa = row
    sd_data.append(
        {"y": -sd, "dataLabels": {"format": f"{sd}%"}} if sd >= 8 else {"y": -sd, "dataLabels": {"enabled": False}}
    )
    d_data.append(
        {"y": -d, "dataLabels": {"format": f"{d}%"}} if d >= 8 else {"y": -d, "dataLabels": {"enabled": False}}
    )
    nl_data.append(
        {"y": -n / 2, "dataLabels": {"enabled": True, "format": f"{n}%"}}
        if n >= 12
        else {"y": -n / 2, "dataLabels": {"enabled": False}}
    )
    nr_data.append({"y": n / 2, "dataLabels": {"enabled": False}})
    a_data.append({"y": a, "dataLabels": {"format": f"{a}%"}} if a >= 8 else {"y": a, "dataLabels": {"enabled": False}})
    sa_data.append(
        {"y": sa, "dataLabels": {"format": f"{sa}%"}} if sa >= 8 else {"y": sa, "dataLabels": {"enabled": False}}
    )

# Chart — canvas is 3200×1800 (landscape, all four sync points kept in sync)
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bar",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginLeft": 680,
    "marginRight": 60,
    "marginTop": 140,
    "marginBottom": 190,
}

chart.options.title = {
    "text": "bar-diverging-likert · highcharts · anyplot.ai",
    "style": {"fontSize": "60px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Employee Engagement Survey Results",
    "style": {"fontSize": "40px", "color": INK_SOFT, "fontWeight": "300"},
}

chart.options.x_axis = {
    "categories": categories,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "38px", "color": INK_SOFT}},
    "lineWidth": 0,
    "tickWidth": 0,
}

y_axis_formatter = CallbackFunction.from_js_literal("function() { return Math.abs(this.value) + '%'; }")
chart.options.y_axis = {
    "title": {"text": "← Disagree    |    Agree →", "style": {"fontSize": "44px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}, "formatter": y_axis_formatter},
    "tickInterval": 10,
    "max": 85,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "plotLines": [{"value": 0, "width": 2, "color": INK, "zIndex": 5}],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal", "color": INK_SOFT},
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "symbolRadius": 0,
    "symbolHeight": 20,
    "symbolWidth": 26,
    "y": -10,
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "bar": {
        "stacking": "normal",
        "borderWidth": 0,
        "pointWidth": 46,
        "groupPadding": 0.1,
        "dataLabels": {
            "enabled": True,
            "inside": True,
            "style": {"fontSize": "22px", "fontWeight": "bold", "textOutline": "none"},
        },
    }
}

chart.options.tooltip = {"style": {"fontSize": "28px"}, "shared": False}

# --- Series (stacking order: innermost first) ---
# Left side:  nl (neutral-left, inner) → d (disagree) → sd (strongly disagree, outer)
# Right side: nr (neutral-right, inner) → a (agree)   → sa (strongly agree, outer)

s_nl = BarSeries()
s_nl.name = "Neutral"
s_nl.id = "neutral"
s_nl.data = nl_data
s_nl.color = color_n
s_nl.legend_index = 2
s_nl.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": INK, "textOutline": "none"},
}
chart.add_series(s_nl)

s_d = BarSeries()
s_d.name = "Disagree"
s_d.data = d_data
s_d.color = color_d
s_d.legend_index = 1
s_d.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#FAF8F1", "textOutline": "none"},
}
chart.add_series(s_d)

s_sd = BarSeries()
s_sd.name = "Strongly Disagree"
s_sd.data = sd_data
s_sd.color = color_sd
s_sd.legend_index = 0
s_sd.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#FAF8F1", "textOutline": "none"},
}
chart.add_series(s_sd)

# Linked to "neutral" so only one legend entry appears for both halves
s_nr = BarSeries()
s_nr.name = "Neutral"
s_nr.data = nr_data
s_nr.color = color_n
s_nr.linked_to = "neutral"
s_nr.data_labels = {"enabled": False}
chart.add_series(s_nr)

s_a = BarSeries()
s_a.name = "Agree"
s_a.data = a_data
s_a.color = color_a
s_a.legend_index = 3
s_a.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#FAF8F1", "textOutline": "none"},
}
chart.add_series(s_a)

s_sa = BarSeries()
s_sa.name = "Strongly Agree"
s_sa.data = sa_data
s_sa.color = color_sa
s_sa.legend_index = 4
s_sa.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#FAF8F1", "textOutline": "none"},
}
chart.add_series(s_sa)

# --- Render ---
# Download Highcharts JS with retry and fallback CDN (inline required for headless Chrome)
highcharts_js = None
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
for url in cdn_urls:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
            break
        except Exception:
            time.sleep(2 * (attempt + 1))
    if highcharts_js:
        break

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact for the site (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium with CDP viewport override for exact 3200×1800
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
# CDP override is the authoritative viewport — --window-size alone loses ~139 px in headless mode
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net — pin saved PNG to exactly 3200×1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
