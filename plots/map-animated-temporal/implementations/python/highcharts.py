""" anyplot.ai
map-animated-temporal: Animated Map over Time
Library: highcharts unknown | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-27
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: PM2.5 air quality readings spreading across Europe over 10 days
np.random.seed(42)

n_days = 10
base_date = pd.Timestamp("2024-03-01")
timestamps = [base_date + pd.Timedelta(days=i) for i in range(n_days)]

# Seed monitoring stations in Western Europe
start_lons = [2.3, -0.1, 4.9, 7.4, 12.5]
start_lats = [48.9, 51.5, 50.8, 47.4, 41.9]
cities = ["Paris", "London", "Brussels", "Zurich", "Rome"]

# Build data with temporal spread: more stations report as event develops
data_records = []
for day_idx, ts in enumerate(timestamps):
    n_points = 5 + day_idx * 3
    for i in range(n_points):
        if i < len(start_lons):
            lon = start_lons[i] + np.random.randn() * 0.5
            lat = start_lats[i] + np.random.randn() * 0.5
            label = cities[i]
        else:
            base_lon = np.random.choice(start_lons) + day_idx * 0.8 + np.random.randn() * 2
            base_lat = np.random.choice(start_lats) + np.random.randn() * 2
            lon = np.clip(base_lon, -10, 40)
            lat = np.clip(base_lat, 35, 60)
            label = f"Station {i + 1}"
        pm25 = 20 + day_idx * 8 + np.random.randn() * 12
        data_records.append({"timestamp": ts, "lon": lon, "lat": lat, "value": max(5.0, pm25), "label": label})

df = pd.DataFrame(data_records)

frames_data = {}
for ts in timestamps:
    frame_df = df[df["timestamp"] == ts]
    frames_data[ts.strftime("%Y-%m-%d")] = frame_df[["lon", "lat", "value", "label"]].to_dict("records")

# Download Highcharts JS, Highmaps module, and Europe map topology
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
highmaps_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/map.js"
europe_map_url = "https://cdn.jsdelivr.net/npm/@highcharts/map-collection/custom/europe.topo.json"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highmaps_url, timeout=30) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(europe_map_url, timeout=30) as response:
    europe_map_json = response.read().decode("utf-8")

dates_list = list(frames_data.keys())

all_frames_js = []
for date_str, points in frames_data.items():
    pts = [f"{{lon: {p['lon']:.2f}, lat: {p['lat']:.2f}, z: {p['value']:.1f}, name: '{p['label']}'}}" for p in points]
    all_frames_js.append(f"'{date_str}': [{', '.join(pts)}]")

frames_js_str = "{" + ", ".join(all_frames_js) + "}"

js_code = f"""
var topology = {europe_map_json};
var frameData = {frames_js_str};
var dates = {dates_list};
var currentIndex = 0;
var isPlaying = false;
var playInterval;
var initialData = frameData[dates[0]];

var chart = Highcharts.mapChart('container', {{
    chart: {{
        map: topology,
        width: 3200,
        height: 1800,
        backgroundColor: '{PAGE_BG}',
        marginBottom: 250,
        style: {{ fontFamily: 'Arial, sans-serif' }}
    }},
    title: {{
        text: 'map-animated-temporal · python · highcharts · anyplot.ai',
        style: {{ fontSize: '66px', fontWeight: 'bold', color: '{INK}' }}
    }},
    subtitle: {{
        text: 'Date: ' + dates[0],
        style: {{ fontSize: '44px', color: '{INK_SOFT}' }}
    }},
    mapNavigation: {{
        enabled: false
    }},
    colorAxis: {{
        min: 5,
        max: 115,
        stops: [
            [0, '#009E73'],
            [1, '#4467A3']
        ],
        labels: {{
            style: {{ fontSize: '44px', color: '{INK_SOFT}' }}
        }},
        title: {{
            text: 'PM2.5 (µg/m³)',
            style: {{ fontSize: '40px', color: '{INK}' }}
        }}
    }},
    legend: {{
        enabled: true,
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'bottom',
        y: -148,
        symbolWidth: 620,
        symbolHeight: 26,
        itemStyle: {{ fontSize: '36px', color: '{INK_SOFT}' }},
        backgroundColor: 'none',
        borderWidth: 0,
        padding: 4
    }},
    series: [{{
        name: 'Europe',
        borderColor: '{INK_SOFT}',
        borderWidth: 0.5,
        nullColor: '{ELEVATED_BG}',
        showInLegend: false
    }}, {{
        type: 'mapbubble',
        name: 'PM2.5',
        data: initialData,
        minSize: 30,
        maxSize: 100,
        colorKey: 'z',
        marker: {{
            fillOpacity: 0.85,
            lineWidth: 2,
            lineColor: '{INK}'
        }},
        dataLabels: {{
            enabled: false
        }},
        tooltip: {{
            pointFormat: '{{point.name}}<br>PM2.5: {{point.z:.1f}} µg/m³'
        }},
        showInLegend: false
    }}]
}});

function updateChart(index) {{
    var date = dates[index];
    var data = frameData[date];
    chart.series[1].setData(data, true, {{ duration: 800 }});
    chart.setTitle(null, {{ text: 'Date: ' + date }});
    currentIndex = index;
    document.getElementById('slider').value = index;
    document.getElementById('dateDisplay').textContent = date;
}}

function playAnimation() {{
    if (isPlaying) {{
        clearInterval(playInterval);
        isPlaying = false;
        document.getElementById('playBtn').textContent = '▶ Play';
    }} else {{
        isPlaying = true;
        document.getElementById('playBtn').textContent = '⏸ Pause';
        playInterval = setInterval(function() {{
            currentIndex = (currentIndex + 1) % dates.length;
            updateChart(currentIndex);
            if (currentIndex === dates.length - 1) {{
                clearInterval(playInterval);
                isPlaying = false;
                document.getElementById('playBtn').textContent = '▶ Play';
            }}
        }}, 1500);
    }}
}}

function onSliderChange(value) {{
    if (isPlaying) {{
        clearInterval(playInterval);
        isPlaying = false;
        document.getElementById('playBtn').textContent = '▶ Play';
    }}
    updateChart(parseInt(value));
}}
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Animated Map over Time</title>
    <script>{highcharts_js}</script>
    <script>{highmaps_js}</script>
    <style>
        body {{ margin: 0; background: {PAGE_BG}; font-family: Arial, sans-serif; }}
        #container {{ width: 3200px; height: 1800px; }}
        #controls {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 30px;
            background: {ELEVATED_BG};
            padding: 18px 48px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.10);
            z-index: 100;
        }}
        #playBtn {{
            font-size: 36px;
            padding: 12px 40px;
            cursor: pointer;
            background: #009E73;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
        }}
        #playBtn:hover {{ opacity: 0.85; }}
        #slider {{
            width: 700px;
            height: 20px;
            cursor: pointer;
            accent-color: #009E73;
        }}
        #dateDisplay {{
            font-size: 36px;
            font-weight: bold;
            min-width: 220px;
            color: {INK};
        }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="controls">
        <button id="playBtn" onclick="playAnimation()">&#9654; Play</button>
        <input type="range" id="slider" min="0" max="{len(dates_list) - 1}" value="0"
               onchange="onSliderChange(this.value)" oninput="onSliderChange(this.value)">
        <span id="dateDisplay">{dates_list[0]}</span>
    </div>
    <script>{js_code}</script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Generate PNG via Selenium with CDP viewport override for exact 3200×1800
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 to satisfy post-render gate
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
