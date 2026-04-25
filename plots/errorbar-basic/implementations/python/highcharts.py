""" anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: highcharts unknown | Python 3.14.4
Quality: 91/100 | Updated: 2026-04-25
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.boxplot import ErrorBarSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
ERROR_COLOR = "#1A1A17" if THEME == "light" else "#F0EFE8"
BRAND = "#009E73"

# Data — clinical trial: response (mg/dL) across treatment groups, with ±1 SE error bars
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
values = [47.2, 58.4, 53.7, 71.5, 62.8, 49.3]
errors = [3.4, 4.1, 3.8, 5.2, 4.6, 3.1]
control_mean = values[0]

# Build chart with the highcharts_core class API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginTop": 240,
    "marginBottom": 220,
    "marginLeft": 280,
    "marginRight": 200,
    "style": {"fontFamily": "Helvetica, Arial, sans-serif", "color": INK},
}

chart.options.title = {
    "text": "errorbar-basic · highcharts · anyplot.ai",
    "align": "left",
    "x": 60,
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": f"Treatment C shows peak response at {values[3]:.1f} mg/dL — Control baseline at {control_mean:.1f} mg/dL",
    "align": "left",
    "x": 60,
    "style": {"fontSize": "36px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Treatment Group", "style": {"fontSize": "42px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickWidth": 2,
}

chart.options.y_axis = {
    "title": {"text": "Response (mg/dL)", "style": {"fontSize": "42px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "tickInterval": 15,
    "min": 0,
    "max": 90,
    "plotLines": [
        {
            "value": control_mean,
            "color": INK_MUTED,
            "width": 3,
            "dashStyle": "Dash",
            "zIndex": 4,
            "label": {
                "text": f"Control mean ({control_mean:.1f})",
                "align": "left",
                "x": 20,
                "y": -16,
                "style": {"fontSize": "30px", "color": INK_MUTED, "fontStyle": "italic"},
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 60,
    "itemStyle": {"fontSize": "32px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": GRID,
    "borderWidth": 1,
    "borderRadius": 8,
    "padding": 20,
    "symbolHeight": 28,
    "symbolWidth": 36,
}

chart.options.plot_options = {
    "column": {"pointPadding": 0.15, "groupPadding": 0.1, "borderWidth": 0, "pointWidth": 360},
    "errorbar": {"whiskerLength": "55%", "whiskerWidth": 8, "stemWidth": 8, "lineWidth": 8},
}

chart.options.credits = {"enabled": False}

# Series via the class API (LM-01: idiomatic ColumnSeries + ErrorBarSeries)
column_series = ColumnSeries.from_array([[cat, val] for cat, val in zip(categories, values, strict=True)])
column_series.name = "Mean response"
column_series.color = BRAND
chart.add_series(column_series)

error_series = ErrorBarSeries.from_array(
    [[i, val - err, val + err] for i, (val, err) in enumerate(zip(values, errors, strict=True))]
)
error_series.name = "± standard error"
error_series.color = ERROR_COLOR
error_series.stem_color = ERROR_COLOR
error_series.whisker_color = ERROR_COLOR
error_series.show_in_legend = True
chart.add_series(error_series)

# Embed Highcharts JS inline (headless Chrome cannot fetch CDN over file://)
HC_BASE = "https://cdn.jsdelivr.net/npm/highcharts@11.4.8"
with urllib.request.urlopen(f"{HC_BASE}/highcharts.js", timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(f"{HC_BASE}/highcharts-more.js", timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

chart_js = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

Path(f"plot-{THEME}.html").write_text(html_content, encoding="utf-8")

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
