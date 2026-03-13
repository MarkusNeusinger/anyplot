"""pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: highcharts unknown | Python 3.14.3
Quality: 79/100 | Created: 2026-03-13
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - US states population (2020 Census, in thousands)
# Each tuple: (abbreviation, full_name, population_thousands, region)
states_data = [
    ("CA", "California", 39538, "West"),
    ("TX", "Texas", 29146, "South"),
    ("FL", "Florida", 21538, "South"),
    ("NY", "New York", 20201, "Northeast"),
    ("PA", "Pennsylvania", 13002, "Northeast"),
    ("IL", "Illinois", 12812, "Midwest"),
    ("OH", "Ohio", 11799, "Midwest"),
    ("GA", "Georgia", 10712, "South"),
    ("NC", "North Carolina", 10439, "South"),
    ("MI", "Michigan", 10077, "Midwest"),
    ("NJ", "New Jersey", 9289, "Northeast"),
    ("VA", "Virginia", 8632, "South"),
    ("WA", "Washington", 7615, "West"),
    ("AZ", "Arizona", 7151, "West"),
    ("MA", "Massachusetts", 7030, "Northeast"),
    ("TN", "Tennessee", 6910, "South"),
    ("IN", "Indiana", 6786, "Midwest"),
    ("MO", "Missouri", 6154, "Midwest"),
    ("MD", "Maryland", 6177, "South"),
    ("WI", "Wisconsin", 5894, "Midwest"),
    ("CO", "Colorado", 5774, "West"),
    ("MN", "Minnesota", 5707, "Midwest"),
    ("SC", "South Carolina", 5119, "South"),
    ("AL", "Alabama", 5024, "South"),
    ("LA", "Louisiana", 4658, "South"),
    ("KY", "Kentucky", 4506, "South"),
    ("OR", "Oregon", 4238, "West"),
    ("OK", "Oklahoma", 3960, "South"),
    ("CT", "Connecticut", 3606, "Northeast"),
    ("UT", "Utah", 3272, "West"),
    ("IA", "Iowa", 3191, "Midwest"),
    ("NV", "Nevada", 3104, "West"),
    ("AR", "Arkansas", 3012, "South"),
    ("MS", "Mississippi", 2961, "South"),
    ("KS", "Kansas", 2937, "Midwest"),
    ("NM", "New Mexico", 2118, "West"),
    ("NE", "Nebraska", 1962, "Midwest"),
    ("ID", "Idaho", 1901, "West"),
    ("WV", "West Virginia", 1794, "South"),
    ("HI", "Hawaii", 1456, "West"),
    ("NH", "New Hampshire", 1378, "Northeast"),
    ("ME", "Maine", 1362, "Northeast"),
    ("MT", "Montana", 1085, "West"),
    ("RI", "Rhode Island", 1098, "Northeast"),
    ("DE", "Delaware", 990, "South"),
    ("SD", "South Dakota", 887, "Midwest"),
    ("ND", "North Dakota", 779, "Midwest"),
    ("AK", "Alaska", 733, "West"),
    ("VT", "Vermont", 643, "Northeast"),
    ("WY", "Wyoming", 577, "West"),
]

# Dorling cartogram: circles positioned geographically, area proportional to value
# Inset positions for Alaska and Hawaii (standard cartographic convention)
# NE states spread slightly to reduce overlap
geo_positions = {
    "AK": (-114, 30),
    "HI": (-109, 27),
    "WA": (-120, 47.5),
    "OR": (-120.5, 44),
    "CA": (-122, 37),
    "NV": (-117, 39),
    "ID": (-114, 44),
    "MT": (-110, 47),
    "WY": (-108, 43),
    "UT": (-112, 39.5),
    "CO": (-106, 39),
    "AZ": (-112, 34),
    "NM": (-106, 34.5),
    "ND": (-100, 47.5),
    "SD": (-100, 44.5),
    "NE": (-100, 41),
    "KS": (-98, 38.5),
    "OK": (-97, 35.5),
    "TX": (-99, 31),
    "MN": (-94, 46),
    "IA": (-93, 42),
    "MO": (-92, 38.5),
    "AR": (-92, 35),
    "LA": (-92, 31),
    "WI": (-89, 44.5),
    "IL": (-89, 40),
    "MS": (-90, 33),
    "MI": (-85, 44.5),
    "IN": (-86, 40),
    "OH": (-82.5, 40.5),
    "KY": (-85.5, 37.5),
    "TN": (-86, 35.5),
    "AL": (-87, 33),
    "GA": (-83.5, 33),
    "FL": (-82, 28.5),
    "SC": (-80.5, 34),
    "NC": (-79, 35.5),
    "VA": (-78, 37.5),
    "WV": (-80.5, 39),
    "PA": (-76.5, 41),
    "NY": (-73.5, 43.5),
    "NJ": (-72.5, 40),
    "DE": (-74.5, 38.5),
    "MD": (-75.5, 39.5),
    "CT": (-71, 41.5),
    "RI": (-69.5, 41.5),
    "MA": (-70, 43),
    "VT": (-72, 45),
    "NH": (-70.5, 44),
    "ME": (-68, 46),
}

# Distinct region colors - colorblind-friendly palette
region_colors = {"Northeast": "#4472C4", "South": "#E07B39", "Midwest": "#548235", "West": "#7B57A0"}

# Build data: one point per state, z = population for area-proportional sizing
data_by_region = {r: [] for r in region_colors}
for abbr, name, pop, region in states_data:
    lon, lat = geo_positions[abbr]
    data_by_region[region].append({"name": name, "code": abbr, "x": lon, "y": lat, "z": pop, "region": region})

chart_config = {
    "chart": {
        "type": "bubble",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "plotBackgroundColor": "transparent",
        "spacing": [80, 40, 80, 40],
        "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
    },
    "title": {
        "text": "cartogram-area-distortion \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "600", "color": "#1a1a2e"},
        "y": 44,
    },
    "subtitle": {
        "text": "Dorling Cartogram \u2014 Circle area proportional to state population (2020 U.S. Census, thousands)",
        "style": {"fontSize": "34px", "color": "#555555", "fontWeight": "300"},
        "y": 92,
    },
    "xAxis": {"visible": False, "min": -127, "max": -63},
    "yAxis": {"visible": False, "min": 25, "max": 49},
    "legend": {
        "enabled": True,
        "layout": "horizontal",
        "align": "center",
        "verticalAlign": "bottom",
        "floating": False,
        "itemStyle": {"fontSize": "32px", "fontWeight": "normal", "color": "#333333"},
        "symbolRadius": 14,
        "symbolHeight": 26,
        "symbolWidth": 26,
        "itemDistance": 80,
        "y": -20,
        "title": {"text": "Region:  ", "style": {"fontSize": "32px", "fontWeight": "bold", "color": "#333333"}},
    },
    "credits": {"enabled": False},
    "tooltip": {
        "style": {"fontSize": "30px"},
        "headerFormat": "",
        "pointFormat": "<b>{point.name}</b> ({point.code})<br/>Population: {point.z:,.0f}k<br/>Region: {point.region}",
        "backgroundColor": "rgba(255,255,255,0.96)",
        "borderColor": "#aaaaaa",
        "borderRadius": 8,
        "shadow": True,
    },
    "plotOptions": {
        "bubble": {
            "minSize": 30,
            "maxSize": 180,
            "sizeBy": "area",
            "zMin": 0,
            "zMax": 42000,
            "clip": False,
            "dataLabels": {
                "enabled": True,
                "format": "{point.code}",
                "style": {
                    "fontSize": "24px",
                    "fontWeight": "700",
                    "color": "#ffffff",
                    "textOutline": "2.5px rgba(0,0,0,0.5)",
                },
                "allowOverlap": True,
            },
            "opacity": 0.92,
            "borderWidth": 2.5,
            "borderColor": "rgba(255,255,255,0.8)",
        }
    },
    "series": [],
}

# One series per region for legend grouping
for region_name, color in region_colors.items():
    points = data_by_region[region_name]
    # Sort large first so small bubbles render on top
    points.sort(key=lambda p: -p["z"])
    chart_config["series"].append({"name": region_name, "color": color, "data": points, "zIndex": 1})

# Annotation explaining the area encoding
chart_config["annotations"] = [
    {
        "draggable": "",
        "labels": [
            {
                "point": {"x": -69, "y": 28, "xAxis": 0, "yAxis": 0},
                "text": ("<b>Circle area = Population</b><br/>Largest: California 39,538k<br/>Smallest: Wyoming 577k"),
                "backgroundColor": "rgba(255,255,255,0.94)",
                "borderColor": "#bbbbbb",
                "borderRadius": 10,
                "borderWidth": 1,
                "style": {"fontSize": "26px", "color": "#333333", "lineHeight": "38px"},
                "padding": 18,
                "shape": "rect",
            }
        ],
    }
]

chart_json = json.dumps(chart_config)

# Download Highcharts JS libraries
highcharts_url = "https://code.highcharts.com/highcharts.js"
more_url = "https://code.highcharts.com/highcharts-more.js"
annotations_url = "https://code.highcharts.com/modules/annotations.js"

headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*", "Referer": "https://www.highcharts.com/"}

req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req, timeout=60) as response:
    highcharts_js = response.read().decode("utf-8")

req = urllib.request.Request(more_url, headers=headers)
with urllib.request.urlopen(req, timeout=60) as response:
    more_js = response.read().decode("utf-8")

req = urllib.request.Request(annotations_url, headers=headers)
with urllib.request.urlopen(req, timeout=60) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts for headless Chrome
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{more_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var chartConfig = {chart_json};
        Highcharts.chart('container', chartConfig);
    </script>
</body>
</html>"""

# Save interactive HTML version (CDN for portability)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0; background:#ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        var chartConfig = {chart_json};
        chartConfig.chart.width = null;
        chartConfig.chart.height = null;
        Highcharts.chart('container', chartConfig);
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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(6)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
