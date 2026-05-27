""" anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: highcharts unknown | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-15
"""

import http.server
import json
import os
import socketserver
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Simulated country data over 20 years (Gapminder-style)
np.random.seed(42)
n_countries = 20
n_years = 20
years = list(range(2000, 2000 + n_years))

# Country names (regions)
countries = [
    "Country A",
    "Country B",
    "Country C",
    "Country D",
    "Country E",
    "Country F",
    "Country G",
    "Country H",
    "Country I",
    "Country J",
    "Country K",
    "Country L",
    "Country M",
    "Country N",
    "Country O",
    "Country P",
    "Country Q",
    "Country R",
    "Country S",
    "Country T",
]

# Region assignment for color coding
regions = ["Region 1", "Region 2", "Region 3", "Region 4"]
country_regions = [regions[i % 4] for i in range(n_countries)]
region_colors = {regions[i]: IMPRINT[i % len(IMPRINT)] for i in range(len(regions))}

# Generate time-series data for each country
# GDP per capita (x): starts between 1000-50000, grows with some noise
# Life expectancy (y): starts between 50-80, generally increases
# Population (size): starts between 5M-500M, grows slowly
data_by_year = {}
for year_idx, year in enumerate(years):
    year_data = []
    for c_idx in range(n_countries):
        base_gdp = 5000 + c_idx * 2500
        gdp_growth = 1 + 0.03 * year_idx + np.random.randn() * 0.02
        gdp = base_gdp * (1.05**year_idx) * gdp_growth

        base_life = 55 + (c_idx % 10) * 2.5
        life_exp = base_life + year_idx * 0.3 + np.random.randn() * 0.5
        life_exp = min(85, max(45, life_exp))

        base_pop = (10 + c_idx * 25) * 1e6
        population = base_pop * (1.012**year_idx)

        year_data.append(
            {
                "country": countries[c_idx],
                "region": country_regions[c_idx],
                "gdp": round(gdp, 0),
                "life_exp": round(life_exp, 1),
                "population": round(population, 0),
            }
        )
    data_by_year[year] = year_data

# Find data bounds for axis scaling
all_gdps = []
all_life_exps = []
for year in years:
    for point in data_by_year[year]:
        all_gdps.append(point["gdp"])
        all_life_exps.append(point["life_exp"])

gdp_min, gdp_max = min(all_gdps), max(all_gdps)
life_min, life_max = min(all_life_exps), max(all_life_exps)

# Add 10% padding for better layout
gdp_min = max(0, gdp_min - 0.1 * (gdp_max - gdp_min))
gdp_max = gdp_max + 0.1 * (gdp_max - gdp_min)
life_min = life_min - 0.1 * (life_max - life_min)
life_max = life_max + 0.1 * (life_max - life_min)

# Convert Python data to JSON
all_data_json = json.dumps(
    {
        str(year): [
            [
                {
                    "x": data_by_year[year][c_idx]["gdp"],
                    "y": data_by_year[year][c_idx]["life_exp"],
                    "z": data_by_year[year][c_idx]["population"] / 1e6,
                    "name": countries[c_idx],
                }
                for c_idx in range(n_countries)
                if country_regions[c_idx] == region
            ]
            for region in regions
        ]
        for year in years
    }
)

years_json = json.dumps(years)
regions_json = json.dumps(regions)
colors_json = json.dumps([region_colors[r] for r in regions])

# Custom JavaScript for animated bubble chart with controls
chart_js = f"""
document.addEventListener('DOMContentLoaded', function() {{
    if (!window.Highcharts) {{
        console.error('Highcharts not loaded!');
        return;
    }}
    console.log('Highcharts loaded successfully');
}});

(function() {{
    var allData = {all_data_json};
    var years = {years_json};
    var regions = {regions_json};
    var colors = {colors_json};
    var currentYearIdx = 0;
    var isPlaying = false;
    var animationInterval = null;
    var chart;

    function getDataForYear(yearIdx) {{
        var year = years[yearIdx];
        return allData[year];
    }}

    function updateChart(yearIdx) {{
        var data = getDataForYear(yearIdx);
        for (var i = 0; i < chart.series.length; i++) {{
            chart.series[i].setData(data[i], false);
        }}
        chart.setTitle(null, {{text: 'Year: ' + years[yearIdx]}});
        chart.redraw();
        document.getElementById('yearSlider').value = yearIdx;
        document.getElementById('yearDisplay').textContent = years[yearIdx];
    }}

    function play() {{
        if (isPlaying) return;
        isPlaying = true;
        document.getElementById('playBtn').textContent = '⏸ Pause';
        animationInterval = setInterval(function() {{
            currentYearIdx++;
            if (currentYearIdx >= years.length) {{
                currentYearIdx = 0;
            }}
            updateChart(currentYearIdx);
        }}, 800);
    }}

    function pause() {{
        isPlaying = false;
        document.getElementById('playBtn').textContent = '▶ Play';
        if (animationInterval) {{
            clearInterval(animationInterval);
            animationInterval = null;
        }}
    }}

    function togglePlay() {{
        if (isPlaying) {{
            pause();
        }} else {{
            play();
        }}
    }}

    function onSliderChange(value) {{
        pause();
        currentYearIdx = parseInt(value);
        updateChart(currentYearIdx);
    }}

    // Build initial series
    var initialData = getDataForYear(0);
    var series = [];
    for (var i = 0; i < regions.length; i++) {{
        series.push({{
            name: regions[i],
            color: colors[i],
            data: initialData[i],
            marker: {{
                symbol: 'circle'
            }}
        }});
    }}

    console.log('Creating chart...');
    chart = Highcharts.chart('container', {{
        chart: {{
            type: 'bubble',
            width: 4800,
            height: 2700,
            backgroundColor: '{PAGE_BG}',
            marginBottom: 300,
            marginTop: 180,
            marginLeft: 180,
            marginRight: 120,
            events: {{
                load: function() {{
                    updateChart(0);
                }}
            }}
        }},
        title: {{
            text: 'scatter-animated-controls · highcharts · anyplot.ai',
            style: {{
                fontSize: '28px',
                fontWeight: 'bold',
                color: '{INK}'
            }},
            y: 40
        }},
        subtitle: {{
            text: 'Year: ' + years[0],
            style: {{
                fontSize: '56px',
                fontWeight: 'bold',
                color: '{INK}'
            }},
            y: 100
        }},
        xAxis: {{
            title: {{
                text: 'GDP per Capita (USD)',
                style: {{
                    fontSize: '22px',
                    color: '{INK}'
                }},
                y: 20
            }},
            labels: {{
                style: {{
                    fontSize: '18px',
                    color: '{INK_SOFT}'
                }},
                format: '${{value:,.0f}}'
            }},
            min: {gdp_min},
            max: {gdp_max},
            lineColor: '{INK_SOFT}',
            tickColor: '{INK_SOFT}',
            gridLineColor: '{GRID}'
        }},
        yAxis: {{
            title: {{
                text: 'Life Expectancy (Years)',
                style: {{
                    fontSize: '22px',
                    color: '{INK}'
                }},
                x: -15
            }},
            labels: {{
                style: {{
                    fontSize: '18px',
                    color: '{INK_SOFT}'
                }}
            }},
            min: {life_min},
            max: {life_max},
            lineColor: '{INK_SOFT}',
            tickColor: '{INK_SOFT}',
            gridLineColor: '{GRID}'
        }},
        legend: {{
            enabled: true,
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'top',
            y: 120,
            itemStyle: {{
                fontSize: '18px',
                color: '{INK_SOFT}'
            }},
            symbolRadius: 12,
            symbolHeight: 24,
            symbolWidth: 24,
            itemDistance: 50,
            backgroundColor: '{ELEVATED_BG}',
            borderColor: '{INK_SOFT}',
            borderWidth: 1
        }},
        tooltip: {{
            useHTML: true,
            headerFormat: '<span style="font-size: 18px; font-weight: bold;">{{point.key}}</span><br/>',
            pointFormat: '<span style="font-size: 16px;">GDP: ${{point.x:,.0f}}<br/>Life Exp: {{point.y:.1f}} years<br/>Pop: {{point.z:.1f}}M</span>',
            backgroundColor: '{ELEVATED_BG}',
            style: {{
                fontSize: '16px',
                color: '{INK}'
            }}
        }},
        plotOptions: {{
            bubble: {{
                minSize: 30,
                maxSize: 100,
                opacity: 0.8,
                marker: {{
                    fillOpacity: 0.75,
                    lineWidth: 2,
                    lineColor: '{PAGE_BG}'
                }},
                dataLabels: {{
                    enabled: false
                }}
            }}
        }},
        series: series
    }});

    window.togglePlay = togglePlay;
    window.onSliderChange = onSliderChange;
}})();
"""

# Generate HTML with CDN scripts (using jsDelivr as it's accessible)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11.0.0/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11.0.0/highcharts-more.js"></script>
    <style>
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: {PAGE_BG};
            overflow: hidden;
        }}
        #container {{
            width: 4800px;
            height: 2700px;
        }}
        #controls {{
            position: absolute;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 50px;
            background-color: {ELEVATED_BG};
            padding: 35px 80px;
            border-radius: 12px;
            border: 1px solid {INK_SOFT};
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            z-index: 1000;
        }}
        #playBtn {{
            font-size: 18px;
            padding: 16px 40px;
            cursor: pointer;
            background-color: {INK};
            color: {PAGE_BG};
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: opacity 0.2s;
        }}
        #playBtn:hover {{
            opacity: 0.85;
        }}
        #yearSlider {{
            width: 600px;
            height: 12px;
            cursor: pointer;
        }}
        #yearDisplay {{
            font-size: 28px;
            font-weight: bold;
            color: {INK};
            min-width: 120px;
            text-align: center;
        }}
        .control-label {{
            font-size: 18px;
            color: {INK_SOFT};
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="controls">
        <button id="playBtn" onclick="togglePlay()">▶ Play</button>
        <span class="control-label">Year:</span>
        <input type="range" id="yearSlider" min="0" max="{len(years) - 1}" value="0"
               onchange="onSliderChange(this.value)" oninput="onSliderChange(this.value)">
        <span id="yearDisplay">{years[0]}</span>
    </div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save interactive HTML (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Use local HTTP server to serve HTML (allows CDN scripts to load)
with tempfile.TemporaryDirectory() as temp_dir:
    html_path = Path(temp_dir) / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Start HTTP server in a background thread
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=temp_dir, **kwargs)

        def log_message(self, format, *args):
            pass  # Suppress logging

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as httpd:
        port = httpd.server_address[1]  # Get the assigned port
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        time.sleep(1)  # Give server time to start

        # Take screenshot
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=4800,2700")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"http://127.0.0.1:{port}/")

        # Wait for page to load and Highcharts to initialize
        for _ in range(40):
            try:
                # Check if Highcharts is loaded and chart exists
                result = driver.execute_script("""
                    if (window.Highcharts && Highcharts.charts && Highcharts.charts[0]) {
                        return {loaded: true, chartExists: true};
                    }
                    return {loaded: !!window.Highcharts, chartExists: false};
                """)
                if result.get("chartExists"):
                    break
            except Exception:
                pass
            time.sleep(0.5)

        # Additional wait and take screenshot
        time.sleep(2)
        driver.save_screenshot(f"plot-{THEME}.png")

        # Try to get console logs for debugging
        try:
            logs = driver.get_log("browser")
            # Print any errors or important messages
            for log in logs:
                if log["level"] in ("SEVERE", "WARNING"):
                    pass  # Silently skip logging
        except Exception:
            pass

        driver.quit()

        httpd.shutdown()
