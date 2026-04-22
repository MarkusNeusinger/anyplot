""" pyplots.ai
marimekko-basic: Basic Marimekko Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Market share by region and product line
# Regions with different market sizes (determines bar widths)
regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
region_sizes = [450, 380, 520, 180, 120]  # Market size in millions USD

# Product lines (stacked within each region)
products = ["Enterprise", "SMB", "Consumer", "Government"]
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Market share percentages by region (each column sums to 100)
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
        # Each point: [x_position, y_value, width]
        data_points.append({"x": cumulative_x[j], "y": share, "z": region_sizes[j], "name": region, "product": product})
    series_data.append(
        {
            "name": product,
            "data": data_points,
            "color": colors[i],
            "borderColor": "#ffffff",
            "borderWidth": 2,
            "dataLabels": {
                "enabled": True,
                "format": "{point.y}%",
                "style": {"fontSize": "24px", "fontWeight": "bold", "textOutline": "2px #ffffff"},
            },
        }
    )

# Build Highcharts configuration
chart_options = {
    "chart": {
        "type": "variwide",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 250,
        "marginRight": 350,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {"text": "marimekko-basic · highcharts · pyplots.ai", "style": {"fontSize": "56px", "fontWeight": "bold"}},
    "subtitle": {
        "text": "Bar width = market size (USD millions), segment height = market share (%)",
        "style": {"fontSize": "32px"},
    },
    "xAxis": {
        "type": "linear",
        "min": 0,
        "max": total_width,
        "title": {"text": "Market Size (Millions USD)", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "28px"}, "format": "{value}"},
        "tickPositions": [0, 200, 400, 600, 800, 1000, 1200, 1400, 1650],
        "plotBands": [
            {
                "from": cumulative_x[i],
                "to": cumulative_x[i] + region_sizes[i],
                "color": "#f8f8f8" if i % 2 == 0 else "#ffffff",
            }
            for i in range(len(regions))
        ],
    },
    "yAxis": {
        "min": 0,
        "max": 100,
        "title": {"text": "Market Share (%)", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "28px"}, "format": "{value}%"},
        "gridLineColor": "#e0e0e0",
        "gridLineWidth": 1,
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "32px", "fontWeight": "normal"},
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
    },
    "plotOptions": {
        "variwide": {
            "stacking": "normal",
            "groupPadding": 0,
            "pointPadding": 0,
            "borderWidth": 2,
            "borderColor": "#ffffff",
        }
    },
    "series": series_data,
}

# Download Highcharts JS modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
variwide_url = "https://code.highcharts.com/modules/variwide.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(variwide_url, timeout=30) as response:
    variwide_js = response.read().decode("utf-8")

# Build region label data for JavaScript
region_label_data = json.dumps(
    [
        {"name": regions[i], "x": cumulative_x[i] + region_sizes[i] / 2, "width": region_sizes[i]}
        for i in range(len(regions))
    ]
)

# Generate HTML with inline scripts - add region labels via chart.events.load
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{variwide_js}</script>
</head>
<body style="margin:0;">
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
                                color: '#333333',
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

# Save HTML for interactive version
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/variwide.js"></script>
</head>
<body style="margin:0;">
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
                                color: '#333333',
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
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Write temp HTML and take screenshot
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()  # Clean up temp file
