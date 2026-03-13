"""pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-13
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - US states population (2020 Census, in thousands)
states_population = [
    ("CA", "California", 39538),
    ("TX", "Texas", 29146),
    ("FL", "Florida", 21538),
    ("NY", "New York", 20201),
    ("PA", "Pennsylvania", 13002),
    ("IL", "Illinois", 12812),
    ("OH", "Ohio", 11799),
    ("GA", "Georgia", 10712),
    ("NC", "North Carolina", 10439),
    ("MI", "Michigan", 10077),
    ("NJ", "New Jersey", 9289),
    ("VA", "Virginia", 8632),
    ("WA", "Washington", 7615),
    ("AZ", "Arizona", 7151),
    ("MA", "Massachusetts", 7030),
    ("TN", "Tennessee", 6910),
    ("IN", "Indiana", 6786),
    ("MO", "Missouri", 6154),
    ("MD", "Maryland", 6177),
    ("WI", "Wisconsin", 5894),
    ("CO", "Colorado", 5774),
    ("MN", "Minnesota", 5707),
    ("SC", "South Carolina", 5119),
    ("AL", "Alabama", 5024),
    ("LA", "Louisiana", 4658),
    ("KY", "Kentucky", 4506),
    ("OR", "Oregon", 4238),
    ("OK", "Oklahoma", 3960),
    ("CT", "Connecticut", 3606),
    ("UT", "Utah", 3272),
    ("IA", "Iowa", 3191),
    ("NV", "Nevada", 3104),
    ("AR", "Arkansas", 3012),
    ("MS", "Mississippi", 2961),
    ("KS", "Kansas", 2937),
    ("NM", "New Mexico", 2118),
    ("NE", "Nebraska", 1962),
    ("ID", "Idaho", 1901),
    ("WV", "West Virginia", 1794),
    ("HI", "Hawaii", 1456),
    ("NH", "New Hampshire", 1378),
    ("ME", "Maine", 1362),
    ("MT", "Montana", 1085),
    ("RI", "Rhode Island", 1098),
    ("DE", "Delaware", 990),
    ("SD", "South Dakota", 887),
    ("ND", "North Dakota", 779),
    ("AK", "Alaska", 733),
    ("VT", "Vermont", 643),
    ("WY", "Wyoming", 577),
]

# Format data for Highcharts mapbubble series (colorValue reinforces size)
bubble_data = [{"code": code, "name": name, "z": pop, "colorValue": pop} for code, name, pop in states_population]

# Chart configuration
chart_config = {
    "chart": {"map": None, "width": 4800, "height": 2700, "backgroundColor": "#ffffff", "spacing": [60, 80, 80, 80]},
    "title": {
        "text": "US Population Cartogram \u00b7 cartogram-area-distortion \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "500", "color": "#1a1a2e"},
        "y": 40,
    },
    "subtitle": {
        "text": "Bubble area proportional to state population \u2014 2020 Census (thousands)",
        "style": {"fontSize": "34px", "color": "#666666"},
        "y": 90,
    },
    "mapNavigation": {"enabled": False},
    "colorAxis": {
        "min": 500,
        "max": 40000,
        "stops": [[0, "#deebf7"], [0.15, "#9ecae1"], [0.35, "#4292c6"], [0.6, "#306998"], [1, "#08306b"]],
        "labels": {"style": {"fontSize": "28px"}},
    },
    "legend": {
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "symbolHeight": 500,
        "symbolWidth": 40,
        "title": {"text": "Population<br/>(thousands)", "style": {"fontSize": "32px", "fontWeight": "bold"}},
        "itemStyle": {"fontSize": "28px"},
    },
    "credits": {"enabled": False},
    "tooltip": {
        "style": {"fontSize": "32px"},
        "headerFormat": "",
        "pointFormat": "<b>{point.name}</b><br/>Population: {point.z}k",
    },
    "series": [
        {
            "type": "map",
            "name": "States",
            "borderColor": "#cccccc",
            "borderWidth": 1,
            "nullColor": "#f0f0f0",
            "showInLegend": False,
            "enableMouseTracking": False,
            "colorAxis": False,
        },
        {
            "type": "mapbubble",
            "name": "Population",
            "joinBy": ["postal-code", "code"],
            "data": bubble_data,
            "minSize": "4%",
            "maxSize": "22%",
            "colorKey": "colorValue",
            "borderColor": "#ffffff",
            "borderWidth": 2,
            "dataLabels": {
                "enabled": True,
                "format": "{point.code}",
                "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#ffffff", "textOutline": "none"},
            },
        },
    ],
}

chart_json = json.dumps(chart_config)

# Download required JavaScript files
highmaps_url = "https://code.highcharts.com/maps/highmaps.js"
us_topo_url = "https://code.highcharts.com/mapdata/countries/us/us-all.topo.json"

headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*", "Referer": "https://www.highcharts.com/"}

req = urllib.request.Request(highmaps_url, headers=headers)
with urllib.request.urlopen(req, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

req = urllib.request.Request(us_topo_url, headers=headers)
with urllib.request.urlopen(req, timeout=60) as response:
    us_topo = response.read().decode("utf-8")

# Generate HTML with inline scripts for headless Chrome
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var topology = {us_topo};
        var chartConfig = {chart_json};
        chartConfig.chart.map = topology;
        Highcharts.mapChart('container', chartConfig);
    </script>
</body>
</html>"""

# Save interactive HTML version
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/maps/highmaps.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        fetch('https://code.highcharts.com/mapdata/countries/us/us-all.topo.json')
            .then(function(r) {{ return r.json(); }})
            .then(function(topology) {{
                var chartConfig = {chart_json};
                chartConfig.chart.map = topology;
                chartConfig.chart.width = null;
                chartConfig.chart.height = null;
                Highcharts.mapChart('container', chartConfig);
            }});
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Write temp HTML and take screenshot with headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
