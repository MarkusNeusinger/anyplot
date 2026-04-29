""" anyplot.ai
marimekko-basic: Basic Marimekko Chart
Library: highcharts unknown | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-27
"""

import json
import os
import tempfile
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Data - Market share by region and product line
regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
region_sizes = [450, 380, 520, 180, 120]  # Market size in millions USD

products = ["Enterprise", "SMB", "Consumer", "Government"]
colors = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]  # Okabe-Ito positions 1-4

market_share = {
    "North America": [42, 28, 22, 8],
    "Europe": [35, 32, 25, 8],
    "Asia Pacific": [28, 25, 38, 9],
    "Latin America": [25, 35, 32, 8],
    "Middle East": [45, 20, 25, 10],
}

# Calculate cumulative widths for x positioning
total_width = sum(region_sizes)
cumulative_x = []
running_x = 0
for size in region_sizes:
    cumulative_x.append(running_x)
    running_x += size

# Build series data for variwide stacked chart
series_data = []
for i, product in enumerate(products):
    data_points = []
    for j, region in enumerate(regions):
        share = market_share[region][i]
        data_points.append({"x": cumulative_x[j], "y": share, "z": region_sizes[j], "name": region})
    series_data.append(
        {
            "name": product,
            "data": data_points,
            "color": colors[i],
            "borderColor": PAGE_BG,
            "borderWidth": 2,
            "dataLabels": {
                "enabled": True,
                "format": "{point.y}%",
                "style": {"fontSize": "24px", "fontWeight": "bold", "textOutline": f"2px {PAGE_BG}", "color": INK},
            },
        }
    )

# Build Highcharts configuration
chart_options = {
    "chart": {
        "type": "variwide",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 250,
        "marginRight": 350,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {
        "text": "marimekko-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "56px", "fontWeight": "bold", "color": INK},
    },
    "subtitle": {
        "text": "Bar width = market size (USD millions), segment height = market share (%)",
        "style": {"fontSize": "32px", "color": INK_SOFT},
    },
    "xAxis": {
        "type": "linear",
        "min": 0,
        "max": total_width,
        "title": {"text": "Market Size (Millions USD)", "style": {"fontSize": "36px", "color": INK}},
        "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}, "format": "{value}"},
        "tickPositions": [0, 200, 400, 600, 800, 1000, 1200, 1400, 1650],
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
        "gridLineWidth": 2,
    },
    "yAxis": {
        "min": 0,
        "max": 100,
        "title": {"text": "Market Share (%)", "style": {"fontSize": "36px", "color": INK}},
        "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}, "format": "{value}%"},
        "gridLineColor": GRID,
        "gridLineWidth": 2,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "32px", "fontWeight": "normal", "color": INK_SOFT},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "align": "right",
        "verticalAlign": "middle",
        "layout": "vertical",
        "x": -50,
        "y": 0,
        "symbolWidth": 40,
        "symbolHeight": 40,
        "symbolRadius": 0,
        "itemMarginBottom": 15,
    },
    "tooltip": {
        "style": {"fontSize": "24px"},
        "headerFormat": "<b>{point.key}</b><br/>",
        "pointFormat": "{series.name}: {point.y}%<br/>Market Size: ${point.z}M",
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
    },
    "plotOptions": {
        "variwide": {
            "stacking": "normal",
            "groupPadding": 0,
            "pointPadding": 0,
            "borderWidth": 2,
            "borderColor": PAGE_BG,
        }
    },
    "series": series_data,
}

# Load Highcharts JS from local npm package (CDN blocked in CI; install via: npm install highcharts --prefix /tmp/hc-tmp)
HC_NPM = Path("/tmp/hc-tmp/node_modules/highcharts")
highcharts_js = (HC_NPM / "highcharts.js").read_text(encoding="utf-8")
variwide_js = (HC_NPM / "modules/variwide.js").read_text(encoding="utf-8")

# Build region label data for JavaScript
region_label_data = json.dumps(
    [{"name": regions[i], "x": cumulative_x[i] + region_sizes[i] / 2} for i in range(len(regions))]
)

chart_options_json = json.dumps(chart_options)

# HTML for Selenium capture (inline JS, fixed 4800x2700 container)
html_capture = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{variwide_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var regionLabels = {region_label_data};
            var chartOptions = {chart_options_json};

            chartOptions.chart.events = {{
                load: function() {{
                    var chart = this;
                    var xAxis = chart.xAxis[0];
                    var yPos = chart.plotTop + chart.plotHeight + 80;

                    regionLabels.forEach(function(region) {{
                        var xPos = xAxis.toPixels(region.x);
                        chart.renderer.text(region.name, xPos, yPos)
                            .attr({{ zIndex: 10 }})
                            .css({{
                                fontSize: '32px',
                                fontWeight: 'bold',
                                color: '{INK}',
                                textAnchor: 'middle'
                            }})
                            .add();
                    }});
                }}
            }};

            Highcharts.chart('container', chartOptions);
        }});
    </script>
</body>
</html>"""

# HTML for interactive site (CDN links, fluid container)
html_interactive = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/variwide.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var regionLabels = {region_label_data};
            var chartOptions = {chart_options_json};

            chartOptions.chart.events = {{
                load: function() {{
                    var chart = this;
                    var xAxis = chart.xAxis[0];
                    var yPos = chart.plotTop + chart.plotHeight + 80;

                    regionLabels.forEach(function(region) {{
                        var xPos = xAxis.toPixels(region.x);
                        chart.renderer.text(region.name, xPos, yPos)
                            .attr({{ zIndex: 10 }})
                            .css({{
                                fontSize: '24px',
                                fontWeight: 'bold',
                                color: '{INK}',
                                textAnchor: 'middle'
                            }})
                            .add();
                    }});
                }}
            }};

            Highcharts.chart('container', chartOptions);
        }});
    </script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_interactive)

# Write temp HTML and take screenshot for PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_capture)
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
