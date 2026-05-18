""" anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-18
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette — continents in canonical order, first is always #009E73
CONTINENT_COLORS = {
    "Asia": "#009E73",
    "Africa": "#D55E00",
    "Europe": "#0072B2",
    "Americas": "#CC79A7",
    "Oceania": "#E69F00",
}

# Data — major world cities, metropolitan population (millions)
cities = [
    {"name": "Tokyo", "lat": 35.7, "lon": 139.7, "pop": 37.4, "continent": "Asia"},
    {"name": "Delhi", "lat": 28.6, "lon": 77.2, "pop": 32.9, "continent": "Asia"},
    {"name": "Shanghai", "lat": 31.2, "lon": 121.5, "pop": 29.2, "continent": "Asia"},
    {"name": "Dhaka", "lat": 23.8, "lon": 90.4, "pop": 23.2, "continent": "Asia"},
    {"name": "Beijing", "lat": 39.9, "lon": 116.4, "pop": 21.5, "continent": "Asia"},
    {"name": "Mumbai", "lat": 19.1, "lon": 72.9, "pop": 21.3, "continent": "Asia"},
    {"name": "Osaka", "lat": 34.7, "lon": 135.5, "pop": 19.0, "continent": "Asia"},
    {"name": "Karachi", "lat": 24.9, "lon": 67.1, "pop": 16.8, "continent": "Asia"},
    {"name": "Manila", "lat": 14.6, "lon": 121.0, "pop": 14.4, "continent": "Asia"},
    {"name": "Jakarta", "lat": -6.2, "lon": 106.8, "pop": 11.2, "continent": "Asia"},
    {"name": "Bangkok", "lat": 13.8, "lon": 100.5, "pop": 11.1, "continent": "Asia"},
    {"name": "Seoul", "lat": 37.6, "lon": 127.0, "pop": 9.9, "continent": "Asia"},
    {"name": "Singapore", "lat": 1.3, "lon": 103.8, "pop": 6.0, "continent": "Asia"},
    {"name": "Cairo", "lat": 30.0, "lon": 31.2, "pop": 21.8, "continent": "Africa"},
    {"name": "Kinshasa", "lat": -4.3, "lon": 15.3, "pop": 17.0, "continent": "Africa"},
    {"name": "Lagos", "lat": 6.5, "lon": 3.4, "pop": 15.4, "continent": "Africa"},
    {"name": "Johannesburg", "lat": -26.2, "lon": 28.0, "pop": 6.0, "continent": "Africa"},
    {"name": "Nairobi", "lat": -1.3, "lon": 36.8, "pop": 5.1, "continent": "Africa"},
    {"name": "Istanbul", "lat": 41.0, "lon": 29.0, "pop": 15.6, "continent": "Europe"},
    {"name": "Moscow", "lat": 55.8, "lon": 37.6, "pop": 12.6, "continent": "Europe"},
    {"name": "Paris", "lat": 48.9, "lon": 2.3, "pop": 11.1, "continent": "Europe"},
    {"name": "London", "lat": 51.5, "lon": -0.1, "pop": 9.5, "continent": "Europe"},
    {"name": "Madrid", "lat": 40.4, "lon": -3.7, "pop": 6.7, "continent": "Europe"},
    {"name": "Berlin", "lat": 52.5, "lon": 13.4, "pop": 3.6, "continent": "Europe"},
    {"name": "São Paulo", "lat": -23.5, "lon": -46.6, "pop": 22.4, "continent": "Americas"},
    {"name": "Mexico City", "lat": 19.4, "lon": -99.1, "pop": 21.8, "continent": "Americas"},
    {"name": "New York", "lat": 40.7, "lon": -74.0, "pop": 18.9, "continent": "Americas"},
    {"name": "Buenos Aires", "lat": -34.6, "lon": -58.4, "pop": 15.4, "continent": "Americas"},
    {"name": "Rio de Janeiro", "lat": -22.9, "lon": -43.2, "pop": 13.6, "continent": "Americas"},
    {"name": "Los Angeles", "lat": 34.1, "lon": -118.2, "pop": 12.5, "continent": "Americas"},
    {"name": "Bogotá", "lat": 4.6, "lon": -74.1, "pop": 11.3, "continent": "Americas"},
    {"name": "Lima", "lat": -12.0, "lon": -77.0, "pop": 11.0, "continent": "Americas"},
    {"name": "Chicago", "lat": 41.9, "lon": -87.6, "pop": 8.9, "continent": "Americas"},
    {"name": "Toronto", "lat": 43.7, "lon": -79.4, "pop": 6.3, "continent": "Americas"},
    {"name": "Sydney", "lat": -33.9, "lon": 151.2, "pop": 5.4, "continent": "Oceania"},
    {"name": "Melbourne", "lat": -37.8, "lon": 145.0, "pop": 5.1, "continent": "Oceania"},
    {"name": "Auckland", "lat": -36.8, "lon": 174.8, "pop": 1.7, "continent": "Oceania"},
]

# Group cities by continent for individual series
continent_data = {}
for city in cities:
    continent_data.setdefault(city["continent"], []).append(
        {"name": city["name"], "lat": city["lat"], "lon": city["lon"], "z": city["pop"], "population": city["pop"]}
    )

# Build Highmaps mapbubble series list
series_list = []
for continent, data in continent_data.items():
    series_list.append(
        {
            "type": "mapbubble",
            "name": continent,
            "data": data,
            "color": CONTINENT_COLORS[continent],
            "marker": {"fillOpacity": 0.65, "lineWidth": 1.5, "lineColor": PAGE_BG},
            "minSize": 25,
            "maxSize": 120,
        }
    )

# Theme-adaptive map land and border colors
MAP_LAND = "#E0DDD6" if THEME == "light" else "#2A2A26"
MAP_BORDER = "#B8B5AC" if THEME == "light" else "#4A4A44"

chart_config = {
    "chart": {
        "map": None,
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "spacing": [120, 100, 80, 100],
        "style": {"color": INK},
    },
    "title": {
        "text": "World City Populations · bubble-map-geographic · python · highcharts · anyplot.ai",
        "style": {"fontSize": "44px", "fontWeight": "bold", "color": INK},
        "y": 70,
    },
    "subtitle": {
        "text": "Bubble size proportional to metropolitan population (millions)",
        "style": {"fontSize": "32px", "color": INK_SOFT},
        "y": 126,
    },
    "mapNavigation": {"enabled": False},
    "legend": {
        "enabled": True,
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "floating": True,
        "x": -60,
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "padding": 30,
        "itemStyle": {"fontSize": "34px", "color": INK_SOFT, "fontWeight": "normal"},
        "itemHoverStyle": {"color": INK},
        "title": {"text": "Continent", "style": {"fontSize": "38px", "fontWeight": "bold", "color": INK}},
        "symbolRadius": 12,
        "symbolHeight": 30,
        "symbolWidth": 30,
        "itemMarginBottom": 12,
        "bubbleLegend": {
            "enabled": True,
            "borderWidth": 1,
            "borderColor": INK_SOFT,
            "color": INK_MUTED,
            "connectorColor": INK_SOFT,
            "connectorDistance": 60,
            "connectorWidth": 1,
            "labels": {"align": "right", "style": {"fontSize": "26px", "color": INK_SOFT}, "format": "{value}M"},
            "title": {"text": "Population", "style": {"fontSize": "28px", "color": INK, "fontWeight": "bold"}},
            "ranges": [{"value": 5}, {"value": 15}, {"value": 35}],
            "maxSize": 120,
            "minSize": 25,
            "zThreshold": 0,
        },
    },
    "tooltip": {
        "useHTML": True,
        "headerFormat": "<span style='font-size: 30px; font-weight: bold;'>{point.name}</span><br/>",
        "pointFormat": (
            "<span style='font-size: 26px;'>"
            "Continent: <b>{series.name}</b><br/>"
            "Population: <b>{point.population:.1f}M</b><br/>"
            "Coords: ({point.lat:.1f}°, {point.lon:.1f}°)"
            "</span>"
        ),
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "style": {"color": INK},
    },
    "plotOptions": {"mapbubble": {"sizeBy": "area", "zMin": 0, "zMax": 40, "dataLabels": {"enabled": False}}},
    "series": [
        {
            "type": "map",
            "name": "World",
            "showInLegend": False,
            "nullColor": MAP_LAND,
            "borderColor": MAP_BORDER,
            "borderWidth": 0.5,
            "states": {"inactive": {"opacity": 1}},
        }
    ]
    + series_list,
}

chart_json = json.dumps(chart_config)

# Download JS files and map topology (jsdelivr — avoids CDN rate-limiting)
highmaps_url = "https://cdn.jsdelivr.net/npm/highcharts@12/highmaps.js"
world_url = "https://cdn.jsdelivr.net/npm/@highcharts/map-collection/custom/world.topo.json"
hc_more_url = "https://cdn.jsdelivr.net/npm/highcharts@12.6.0/highcharts-more.js"

with urllib.request.urlopen(highmaps_url, timeout=60) as r:
    highmaps_js = r.read().decode("utf-8")

with urllib.request.urlopen(world_url, timeout=60) as r:
    world_topo = r.read().decode("utf-8")

# Try to load highcharts-more for bubbleLegend support; falls back gracefully
hc_more_script = ""
try:
    with urllib.request.urlopen(hc_more_url, timeout=30) as r:
        hc_more_script = f"<script>{r.read().decode('utf-8')}</script>"
except Exception:
    pass

# Build HTML with inline scripts (required for headless Chrome file:// protocol)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    {hc_more_script}
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var topology = {world_topo};
        var chartConfig = {chart_json};
        chartConfig.chart.map = topology;
        Highcharts.mapChart('container', chartConfig);
    </script>
</body>
</html>"""

# Save theme-suffixed HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot PNG artifact
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
