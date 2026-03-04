""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: highcharts unknown | Python 3.14.3
Quality: 93/100 | Created: 2026-03-04
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from highcharts_core.utility_classes.javascript_functions import CallbackFunction
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# Data - Employee Engagement Survey (8 questions, 5-point Likert scale)
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

# Sort by net agreement ascending (lowest net at bottom of horizontal bar chart)
survey_data.sort(key=lambda r: (r[4] + r[5]) - (r[1] + r[2]))
categories = [r[0] for r in survey_data]

# Diverging color palette: warm reds → muted neutral → cool blues
color_sd = "#C0392B"
color_d = "#E57373"
color_n = "#B0BEC5"
color_a = "#64B5F6"
color_sa = "#306998"

# Build per-series data
# Negative values for left side (disagree), positive for right side (agree)
# Neutral is split evenly across the center
sd_data = []
d_data = []
nl_data = []
nr_data = []
a_data = []
sa_data = []

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

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bar",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 380,
    "marginRight": 80,
    "marginTop": 130,
    "marginBottom": 200,
}

chart.options.title = {
    "text": "bar-diverging-likert \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Employee Engagement Survey Results",
    "style": {"fontSize": "32px", "color": "#888888", "fontWeight": "300"},
}

chart.options.x_axis = {
    "categories": categories,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "28px"}},
    "lineWidth": 0,
    "tickWidth": 0,
}

y_axis_formatter = CallbackFunction.from_js_literal("function() { return Math.abs(this.value) + '%'; }")
chart.options.y_axis = {
    "title": {"text": "\u2190 Disagree    |    Agree \u2192", "style": {"fontSize": "28px"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px"}, "formatter": y_axis_formatter},
    "tickInterval": 10,
    "max": 80,
    "gridLineWidth": 1,
    "gridLineColor": "#e8e8e8",
    "plotLines": [{"value": 0, "width": 3, "color": "#333333", "zIndex": 5}],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "30px", "fontWeight": "normal"},
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "symbolRadius": 0,
    "symbolHeight": 22,
    "symbolWidth": 30,
    "y": -30,
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "bar": {
        "stacking": "normal",
        "borderWidth": 0,
        "pointWidth": 55,
        "groupPadding": 0.1,
        "dataLabels": {
            "enabled": True,
            "inside": True,
            "style": {"fontSize": "22px", "fontWeight": "bold", "textOutline": "none"},
        },
    }
}

chart.options.tooltip = {"style": {"fontSize": "22px"}, "shared": False}

# Series in stacking order (first = closest to center axis)
# Left side: Neutral-left (inner) → Disagree (middle) → Strongly Disagree (outer)
# Right side: Neutral-right (inner) → Agree (middle) → Strongly Agree (outer)

# Neutral-left
s_nl = BarSeries()
s_nl.name = "Neutral"
s_nl.id = "neutral"
s_nl.data = nl_data
s_nl.color = color_n
s_nl.legend_index = 2
s_nl.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#555555", "textOutline": "none"},
}
chart.add_series(s_nl)

# Disagree
s_d = BarSeries()
s_d.name = "Disagree"
s_d.data = d_data
s_d.color = color_d
s_d.legend_index = 1
s_d.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#333333", "textOutline": "none"},
}
chart.add_series(s_d)

# Strongly Disagree
s_sd = BarSeries()
s_sd.name = "Strongly Disagree"
s_sd.data = sd_data
s_sd.color = color_sd
s_sd.legend_index = 0
s_sd.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#ffffff", "textOutline": "none"},
}
chart.add_series(s_sd)

# Neutral-right (linked to neutral-left for unified legend entry)
s_nr = BarSeries()
s_nr.name = "Neutral"
s_nr.data = nr_data
s_nr.color = color_n
s_nr.linked_to = "neutral"
s_nr.data_labels = {"enabled": False}
chart.add_series(s_nr)

# Agree
s_a = BarSeries()
s_a.name = "Agree"
s_a.data = a_data
s_a.color = color_a
s_a.legend_index = 3
s_a.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#333333", "textOutline": "none"},
}
chart.add_series(s_a)

# Strongly Agree
s_sa = BarSeries()
s_sa.name = "Strongly Agree"
s_sa.data = sa_data
s_sa.color = color_sa
s_sa.legend_index = 4
s_sa.data_labels = {
    "enabled": True,
    "inside": True,
    "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#ffffff", "textOutline": "none"},
}
chart.add_series(s_sa)

# Render - download Highcharts JS with retry and fallback CDN
highcharts_js = None
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
for url in cdn_urls:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
            break
        except urllib.error.HTTPError:
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
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
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
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element(By.ID, "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
