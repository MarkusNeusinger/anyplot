""" pyplots.ai
map-animated-temporal: Animated Map over Time
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Simulated sensor readings spreading across Europe over time
np.random.seed(42)

# Create time steps (10 days)
n_days = 10
base_date = pd.Timestamp("2024-01-01")
timestamps = [base_date + pd.Timedelta(days=i) for i in range(n_days)]

# Starting points in Western Europe, gradually spreading eastward
start_lons = [2.3, -0.1, 4.9, 7.4, 12.5]  # Paris, London, Brussels, Zurich, Rome
start_lats = [48.9, 51.5, 50.8, 47.4, 41.9]
cities = ["Paris", "London", "Brussels", "Zurich", "Rome"]

# Build data with temporal spread pattern
data_records = []
for day_idx, ts in enumerate(timestamps):
    # More points appear as time progresses
    n_points = 5 + day_idx * 3  # 5 to 32 points
    for i in range(n_points):
        if i < len(start_lons):
            # Original cities
            lon = start_lons[i] + np.random.randn() * 0.5
            lat = start_lats[i] + np.random.randn() * 0.5
            label = cities[i]
        else:
            # New spreading points - drift eastward over time
            base_lon = np.random.choice(start_lons) + day_idx * 0.8 + np.random.randn() * 2
            base_lat = np.random.choice(start_lats) + np.random.randn() * 2
            lon = np.clip(base_lon, -10, 40)
            lat = np.clip(base_lat, 35, 60)
            label = f"Sensor {i + 1}"
        value = 50 + day_idx * 5 + np.random.randn() * 15
        data_records.append({"timestamp": ts, "lon": lon, "lat": lat, "value": max(10, value), "label": label})

df = pd.DataFrame(data_records)

# Prepare data grouped by timestamp for animation frames
frames_data = {}
for ts in timestamps:
    frame_df = df[df["timestamp"] == ts]
    frames_data[ts.strftime("%Y-%m-%d")] = frame_df[["lon", "lat", "value", "label"]].to_dict("records")

# Download Highcharts JS and Highmaps modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
highmaps_url = "https://code.highcharts.com/maps/modules/map.js"
europe_map_url = "https://code.highcharts.com/mapdata/custom/europe.topo.json"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highmaps_url, timeout=30) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(europe_map_url, timeout=30) as response:
    europe_map_json = response.read().decode("utf-8")

# Build JavaScript for animated map
dates_list = list(frames_data.keys())
all_frames_js = []
for date_str, points in frames_data.items():
    points_js = []
    for p in points:
        points_js.append(f"{{lon: {p['lon']:.2f}, lat: {p['lat']:.2f}, z: {p['value']:.1f}, name: '{p['label']}'}}")
    all_frames_js.append(f"'{date_str}': [{', '.join(points_js)}]")

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
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        marginBottom: 200
    }},
    title: {{
        text: 'map-animated-temporal · highcharts · pyplots.ai',
        style: {{ fontSize: '48px', fontWeight: 'bold' }}
    }},
    subtitle: {{
        text: 'Date: ' + dates[0],
        style: {{ fontSize: '36px' }}
    }},
    mapNavigation: {{
        enabled: false
    }},
    colorAxis: {{
        min: 10,
        max: 120,
        stops: [
            [0, '#306998'],
            [0.5, '#17BECF'],
            [1, '#9467BD']
        ],
        labels: {{
            style: {{ fontSize: '24px' }},
            format: '{{value}}'
        }},
        title: {{
            text: 'Sensor Value',
            style: {{ fontSize: '28px' }}
        }},
        showInLegend: true
    }},
    legend: {{
        enabled: true,
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle',
        floating: false,
        borderWidth: 1,
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        padding: 20,
        itemStyle: {{ fontSize: '24px' }},
        symbolHeight: 400,
        symbolWidth: 30,
        y: -50
    }},
    series: [{{
        name: 'Europe',
        borderColor: '#606060',
        nullColor: 'rgba(230, 230, 230, 0.5)',
        showInLegend: false
    }}, {{
        type: 'mapbubble',
        name: 'Sensor Readings',
        data: initialData,
        minSize: 40,
        maxSize: 120,
        colorKey: 'z',
        marker: {{
            fillOpacity: 0.85,
            lineWidth: 2,
            lineColor: '#333333'
        }},
        dataLabels: {{
            enabled: false
        }},
        tooltip: {{
            pointFormat: '{{point.name}}<br>Value: {{point.z:.1f}}'
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
        body {{ margin: 0; font-family: Arial, sans-serif; }}
        #container {{ width: 4800px; height: 2700px; }}
        #controls {{
            position: absolute;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 30px;
            background: rgba(255, 255, 255, 0.95);
            padding: 25px 50px;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 100;
        }}
        #playBtn {{
            font-size: 32px;
            padding: 15px 40px;
            cursor: pointer;
            background: #306998;
            color: white;
            border: none;
            border-radius: 10px;
        }}
        #playBtn:hover {{ background: #254c73; }}
        #slider {{
            width: 600px;
            height: 20px;
            cursor: pointer;
        }}
        #dateDisplay {{
            font-size: 32px;
            font-weight: bold;
            min-width: 200px;
            color: #306998;
        }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="controls">
        <button id="playBtn" onclick="playAnimation()">▶ Play</button>
        <input type="range" id="slider" min="0" max="{len(dates_list) - 1}" value="0"
               onchange="onSliderChange(this.value)" oninput="onSliderChange(this.value)">
        <span id="dateDisplay">{dates_list[0]}</span>
    </div>
    <script>{js_code}</script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Generate PNG screenshot using Selenium
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
time.sleep(8)  # Wait for map and chart to render fully
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
