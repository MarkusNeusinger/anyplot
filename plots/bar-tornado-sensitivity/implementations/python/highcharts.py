"""anyplot.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Updated: 2026-06-02
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — first series always #009E73
COLOR_HIGH = "#009E73"  # green — high/upside scenario (Imprint position 1)
COLOR_LOW = "#4467A3"  # blue — low/downside scenario (Imprint position 3)

# Subtle region tints
POS_BAND = "rgba(0,158,115,0.04)"
NEG_BAND = "rgba(174,48,48,0.04)"
TOP_ROW_BAND = "rgba(0,158,115,0.07)"  # highlight for the widest-range driver row

# Data — NPV sensitivity for a capital investment project
base_npv = 12.5  # Base case NPV in $M

parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Material Cost",
    "Labor Cost",
    "Project Duration",
    "Tax Rate",
    "Salvage Value",
    "Inflation Rate",
    "Market Share",
    "Operating Expenses",
]

# Realistic sensitivity values — some parameters have inverse effects on NPV
low_values = [17.2, 9.2, 14.8, 14.0, 14.2, 13.8, 10.8, 13.2, 9.8, 14.5]
high_values = [8.1, 16.5, 10.3, 11.2, 11.0, 11.4, 13.9, 12.0, 15.5, 10.8]

# Sort by total range (widest bar first — classic tornado ordering)
ranges = [abs(high_values[i] - low_values[i]) for i in range(len(parameters))]
sorted_indices = sorted(range(len(parameters)), key=lambda i: ranges[i], reverse=True)

sorted_params = [parameters[i] for i in sorted_indices]
sorted_low = [round(low_values[i] - base_npv, 1) for i in sorted_indices]
sorted_high = [round(high_values[i] - base_npv, 1) for i in sorted_indices]
n_params = len(sorted_params)
top_driver = sorted_params[0]
# The widest bar tip value (max absolute delta) for callout anchor
max_positive = max(sorted_low[0], sorted_high[0])

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bar",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginLeft": 460,
    "marginRight": 80,
    "marginTop": 270,
    "marginBottom": 140,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "bar-tornado-sensitivity · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "600", "color": INK},
    "y": 50,
}

chart.options.subtitle = {
    "text": "NPV Sensitivity Analysis — Base Case: $12.5M",
    "style": {"fontSize": "44px", "fontWeight": "400", "color": INK_SOFT},
    "y": 114,
}

chart.options.x_axis = {
    "categories": sorted_params,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "400"}},
    "lineWidth": 1,
    "lineColor": INK_SOFT,
    "tickWidth": 0,
    # Subtle highlight band for the top-driver row (widest range, index 0 at top)
    "plotBands": [{"from": -0.5, "to": 0.5, "color": TOP_ROW_BAND}],
}

chart.options.y_axis = {
    "title": {
        "text": "Change in NPV ($M)",
        "style": {"fontSize": "44px", "color": INK, "fontWeight": "500"},
        "margin": 28,
    },
    "labels": {"style": {"fontSize": "40px", "color": INK_SOFT}, "format": "{value}"},
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    # Shade the positive and negative NPV-change half-planes
    "plotBands": [
        {
            "from": -8,
            "to": 0,
            "color": NEG_BAND,
            "label": {
                "text": "Negative Impact",
                "style": {"fontSize": "26px", "color": "rgba(174,48,48,0.35)", "fontStyle": "italic"},
                "align": "right",
                "x": -20,
                "verticalAlign": "bottom",
                "y": -16,
            },
        },
        {
            "from": 0,
            "to": 8,
            "color": POS_BAND,
            "label": {
                "text": "Positive Impact",
                "style": {"fontSize": "26px", "color": "rgba(0,158,115,0.35)", "fontStyle": "italic"},
                "align": "left",
                "x": 20,
                "verticalAlign": "bottom",
                "y": -16,
            },
        },
    ],
    "plotLines": [
        {
            "value": 0,
            "width": 3,
            "color": INK,
            "zIndex": 5,
            "label": {
                "text": "Base",
                "align": "center",
                "verticalAlign": "top",
                "rotation": 0,
                "style": {"fontSize": "32px", "fontWeight": "bold", "color": INK},
                "y": 18,
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "44px", "fontWeight": "400", "color": INK_SOFT},
    "verticalAlign": "top",
    "layout": "horizontal",
    "align": "center",
    "y": 165,
    "floating": True,
    "symbolRadius": 3,
    "symbolHeight": 16,
    "symbolWidth": 24,
    "itemDistance": 50,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 12,
}

chart.options.credits = {"enabled": False}
chart.options.accessibility = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "<b>{point.key}</b><br/>",
    "pointFormat": "{series.name}: <b>{point.y:.1f}M</b>",
    "style": {"fontSize": "34px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

chart.options.plot_options = {
    "bar": {
        "grouping": True,
        "borderWidth": 0,
        "pointPadding": 0.05,
        "groupPadding": 0.1,
        "borderRadius": 2,
        "dataLabels": {
            "enabled": True,
            "format": "{y:.1f}",
            "style": {"fontSize": "30px", "fontWeight": "600", "textOutline": f"2px {PAGE_BG}", "color": INK},
        },
    }
}

# Responsive rules — degrade gracefully for smaller viewports
chart.options.responsive = {
    "rules": [
        {
            "condition": {"maxWidth": 1600},
            "chartOptions": {
                "legend": {"itemStyle": {"fontSize": "22px"}},
                "xAxis": {"labels": {"style": {"fontSize": "22px"}}},
                "yAxis": {"labels": {"style": {"fontSize": "20px"}}, "title": {"style": {"fontSize": "22px"}}},
            },
        }
    ]
}

# High scenario first → gets #009E73 (Imprint first series, green = upside)
high_series = BarSeries()
high_series.name = "High Scenario"
high_series.data = [{"y": v} for v in sorted_high]
high_series.color = COLOR_HIGH

low_series = BarSeries()
low_series.name = "Low Scenario"
low_series.data = [{"y": v} for v in sorted_low]
low_series.color = COLOR_LOW

chart.add_series(high_series)
chart.add_series(low_series)

# Embed Highcharts JS inline (CDN scripts fail in headless file:// context)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

config_json = json.dumps(chart.options.to_dict())
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        var hcChart = Highcharts.chart('container', {config_json});

        // Use chart.renderer.label (callout shape) to highlight the top sensitivity driver.
        // toPixels converts data values to absolute pixel coordinates at render time.
        var tipX = hcChart.yAxis[0].toPixels({max_positive});
        var rowY = hcChart.xAxis[0].toPixels(0);  // center y of first row (Discount Rate)

        hcChart.renderer.label(
            '★ Top Driver: {top_driver}',
            tipX - 340,
            rowY - 44,
            'callout',
            tipX + 5,
            rowY
        )
        .attr({{
            fill: 'rgba(0,158,115,0.10)',
            stroke: '{COLOR_HIGH}',
            'stroke-width': 1.5,
            padding: 14,
            r: 4,
            zIndex: 7,
        }})
        .css({{
            color: '{COLOR_HIGH}',
            fontSize: '28px',
            fontWeight: '700',
        }})
        .add();
    }});
    </script>
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
# CDP override must come before get() — authoritative viewport size
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dimensions
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
