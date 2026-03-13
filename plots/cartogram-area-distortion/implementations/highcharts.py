""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: highcharts unknown | Python 3.14.3
Quality: 85/100 | Created: 2026-03-13
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
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
# NE states spread out more to reduce crowding (adjusted from geographic centers)
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
    "PA": (-77, 41.5),
    "NY": (-74, 44),
    "NJ": (-70.5, 39.5),
    "DE": (-73, 37),
    "MD": (-76, 38),
    "CT": (-68.5, 42.5),
    "RI": (-66.5, 41),
    "MA": (-68, 44),
    "VT": (-71.5, 46),
    "NH": (-69.5, 45),
    "ME": (-67, 47),
}

# Distinct region colors - colorblind-friendly palette
region_colors = {"Northeast": "#3A6DB5", "South": "#D97941", "Midwest": "#49873A", "West": "#7B57A0"}

# Simplified US continental outline for geographic reference
us_outline = [
    [-124.7, 48.4],
    [-124.2, 42.0],
    [-122.4, 37.8],
    [-120.5, 34.5],
    [-117.1, 32.5],
    [-114.7, 32.7],
    [-111.0, 31.3],
    [-108.2, 31.8],
    [-106.6, 31.8],
    [-104.0, 29.5],
    [-100.0, 26.5],
    [-97.0, 26.0],
    [-94.5, 29.5],
    [-91.0, 29.0],
    [-88.5, 30.2],
    [-85.5, 30.0],
    [-84.0, 30.5],
    [-82.0, 25.0],
    [-80.0, 25.5],
    [-80.5, 31.5],
    [-78.5, 33.5],
    [-75.5, 35.0],
    [-75.0, 37.5],
    [-74.0, 39.5],
    [-73.5, 40.5],
    [-71.5, 41.0],
    [-70.0, 41.5],
    [-69.5, 43.0],
    [-67.0, 44.5],
    [-67.0, 47.5],
    [-69.5, 47.5],
    [-75.0, 45.0],
    [-79.5, 43.5],
    [-83.0, 46.0],
    [-84.5, 46.5],
    [-88.5, 48.0],
    [-92.0, 48.5],
    [-95.0, 49.0],
    [-104.0, 49.0],
    [-117.0, 49.0],
    [-124.7, 48.4],
]

# Build data per region, with adaptive label sizing based on population
data_by_region = {r: [] for r in region_colors}
for abbr, name, pop, region in states_data:
    lon, lat = geo_positions[abbr]
    label_size = "24px" if pop > 5000 else "20px" if pop > 2000 else "16px"
    data_by_region[region].append(
        {
            "name": name,
            "code": abbr,
            "x": lon,
            "y": lat,
            "z": pop,
            "region": region,
            "dataLabels": {"style": {"fontSize": label_size}},
        }
    )

# Use highcharts-core to validate and build chart options
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bubble",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "plotBackgroundColor": "transparent",
    "spacing": [90, 50, 90, 50],
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "cartogram-area-distortion \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "600", "color": "#1a1a2e"},
    "y": 50,
}

chart.options.subtitle = {
    "text": ("Dorling Cartogram \u2014 Circle area proportional to state population (2020 U.S. Census, thousands)"),
    "style": {"fontSize": "34px", "color": "#5a5a6e", "fontWeight": "300"},
    "y": 98,
}

chart.options.x_axis = {"visible": False, "min": -128, "max": -62}
chart.options.y_axis = {"visible": False, "min": 24, "max": 50}

chart.options.legend = {
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
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "style": {"fontSize": "30px"},
    "headerFormat": "",
    "pointFormat": ("<b>{point.name}</b> ({point.code})<br/>Population: {point.z:,.0f}k<br/>Region: {point.region}"),
    "backgroundColor": "rgba(255,255,255,0.96)",
    "borderColor": "#aaaaaa",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0,0,0,0.15)", "offsetX": 2, "offsetY": 2, "width": 4},
}

chart.options.plot_options = {
    "bubble": {
        "minSize": 28,
        "maxSize": 175,
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
                "textOutline": "2.5px rgba(0,0,0,0.45)",
            },
            "allowOverlap": True,
        },
        "opacity": 0.88,
        "borderWidth": 2,
        "borderColor": "rgba(255,255,255,0.9)",
    }
}

# Convert validated options to dict, then add series with custom data properties
# (highcharts-core strips custom point properties during serialization,
# so we merge them back as raw dicts for the final JSON output)
options_dict = json.loads(chart.options.to_json())

# Build series: reference outline + one bubble series per region
series_list = []

# Faint US continental outline as geographic reference
series_list.append(
    {
        "type": "line",
        "name": "U.S. Outline",
        "data": [[lon, lat] for lon, lat in us_outline],
        "color": "rgba(180,180,190,0.35)",
        "lineWidth": 2,
        "enableMouseTracking": False,
        "showInLegend": False,
        "marker": {"enabled": False},
        "zIndex": 0,
        "dashStyle": "Dot",
    }
)

# One bubble series per region for legend grouping
for region_name, color in region_colors.items():
    points = data_by_region[region_name]
    points.sort(key=lambda p: -p["z"])
    series_list.append({"type": "bubble", "name": region_name, "color": color, "data": points, "zIndex": 1})

options_dict["series"] = series_list

# Annotation explaining the area encoding
options_dict["annotations"] = [
    {
        "draggable": "",
        "labels": [
            {
                "point": {"x": -68, "y": 28, "xAxis": 0, "yAxis": 0},
                "text": ("<b>Circle area = Population</b><br/>Largest: California 39,538k<br/>Smallest: Wyoming 577k"),
                "backgroundColor": "rgba(255,255,255,0.95)",
                "borderColor": "#c0c0c8",
                "borderRadius": 10,
                "borderWidth": 1.5,
                "style": {"fontSize": "26px", "color": "#333333", "lineHeight": "38px"},
                "padding": 18,
                "shape": "rect",
            }
        ],
    }
]

chart_json = json.dumps(options_dict)

# Download Highcharts JS libraries for inline embedding
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

# Generate HTML with inline scripts for headless Chrome rendering
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{more_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:#fafbfc;">
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
<body style="margin:0; background:#fafbfc;">
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
