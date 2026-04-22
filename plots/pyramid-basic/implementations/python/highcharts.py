""" pyplots.ai
pyramid-basic: Basic Pyramid Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Population pyramid by age group (typical demographic data)
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
# Male population (displayed as negative for left side)
male_values = [-50, -62, -75, -68, -58, -52, -42, -28, -12]
# Female population (displayed as positive for right side)
female_values = [48, 60, 72, 70, 62, 55, 48, 35, 18]

# Find max absolute value for symmetric axis
max_val = max(max(abs(v) for v in male_values), max(female_values))
axis_max = int(max_val * 1.1)  # Add 10% padding

# Chart options as dictionary
chart_options = {
    "chart": {
        "type": "bar",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginLeft": 200,
        "marginRight": 200,
        "marginBottom": 150,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {
        "text": "Population by Age Group · pyramid-basic · highcharts · pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold"},
    },
    "subtitle": {"text": "Male (left) vs Female (right) - Population in Millions", "style": {"fontSize": "32px"}},
    "xAxis": [
        {
            "categories": age_groups,
            "reversed": False,
            "title": {"text": "Age Group", "style": {"fontSize": "36px"}},
            "labels": {"style": {"fontSize": "28px"}},
            "accessibility": {"description": "Age groups"},
        },
        {
            # Mirror axis for the right side
            "opposite": True,
            "reversed": False,
            "categories": age_groups,
            "linkedTo": 0,
            "labels": {"style": {"fontSize": "28px"}},
            "accessibility": {"description": "Age groups (mirror)"},
        },
    ],
    "yAxis": {
        "title": {"text": "Population (Millions)", "style": {"fontSize": "36px"}},
        "labels": {
            "style": {"fontSize": "28px"},
            "formatter": "__FORMATTER_PLACEHOLDER__",  # Will be replaced with JS function
        },
        "min": -axis_max,
        "max": axis_max,
        "gridLineColor": "#e0e0e0",
        "plotLines": [{"color": "#666666", "width": 2, "value": 0, "zIndex": 5}],
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "28px"},
        "align": "center",
        "verticalAlign": "bottom",
        "y": -50,
    },
    "tooltip": {
        "formatter": "__TOOLTIP_FORMATTER__",  # Will be replaced with JS function
        "style": {"fontSize": "24px"},
    },
    "plotOptions": {
        "bar": {
            "pointPadding": 0.1,
            "borderWidth": 0,
            "groupPadding": 0.1,
            "dataLabels": {
                "enabled": True,
                "style": {"fontSize": "22px", "fontWeight": "bold"},
                "formatter": "__DATALABEL_FORMATTER__",  # Will be replaced with JS function
            },
        }
    },
    "series": [
        {
            "name": "Male",
            "data": male_values,
            "color": "#306998",  # Python Blue
        },
        {
            "name": "Female",
            "data": female_values,
            "color": "#FFD43B",  # Python Yellow
        },
    ],
    "credits": {"enabled": False},
}

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate JSON and replace formatter placeholders with actual JS functions
chart_options_json = json.dumps(chart_options)

# Replace the formatter placeholders with actual JavaScript functions
chart_options_json = chart_options_json.replace(
    '"__FORMATTER_PLACEHOLDER__"', "function() { return Math.abs(this.value); }"
)
chart_options_json = chart_options_json.replace(
    '"__TOOLTIP_FORMATTER__"',
    """function() {
        return '<b>' + this.series.name + ', Age ' + this.point.category + '</b><br/>' +
               'Population: ' + Highcharts.numberFormat(Math.abs(this.point.y), 0) + ' Million';
    }""",
)
chart_options_json = chart_options_json.replace('"__DATALABEL_FORMATTER__"', "function() { return Math.abs(this.y); }")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_options_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
