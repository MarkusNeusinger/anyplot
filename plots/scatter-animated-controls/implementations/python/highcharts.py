""" pyplots.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


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
region_colors = {
    "Region 1": "#306998",  # Python Blue
    "Region 2": "#FFD43B",  # Python Yellow
    "Region 3": "#9467BD",  # Purple
    "Region 4": "#17BECF",  # Cyan
}

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

# Build series data for Highcharts motion chart
# Format: each series is a region, data points have x, y, z (bubble size), name
series_config = []
for region in regions:
    series_data = []
    for c_idx in range(n_countries):
        if country_regions[c_idx] == region:
            # Create data sequence for this country over all years
            country_sequence = []
            for year in years:
                yd = data_by_year[year][c_idx]
                country_sequence.append(
                    {
                        "x": yd["gdp"],
                        "y": yd["life_exp"],
                        "z": yd["population"] / 1e6,  # Population in millions for sizing
                        "name": yd["country"],
                    }
                )
            series_data.append({"name": countries[c_idx], "data": country_sequence})
    series_config.append({"name": region, "color": region_colors[region], "data": series_data})

# Build the motion data structure for Highcharts
# Motion module expects data in specific format with sequence key
motion_data_js = []
for region in regions:
    region_points = []
    for c_idx in range(n_countries):
        if country_regions[c_idx] == region:
            sequences = []
            for year in years:
                yd = data_by_year[year][c_idx]
                sequences.append([yd["gdp"], yd["life_exp"], yd["population"] / 1e6])
            region_points.append({"name": countries[c_idx], "sequence": sequences})
    motion_data_js.append({"name": region, "color": region_colors[region], "data": region_points})

# Download Highcharts JS files
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Build custom JavaScript for animated bubble chart with controls
# Since Highcharts doesn't have built-in motion module in core, we'll implement animation manually
initial_year_idx = 0
initial_data = []
for region in regions:
    region_points = []
    for c_idx in range(n_countries):
        if country_regions[c_idx] == region:
            yd = data_by_year[years[0]][c_idx]
            region_points.append(
                {"x": yd["gdp"], "y": yd["life_exp"], "z": yd["population"] / 1e6, "name": countries[c_idx]}
            )
    initial_data.append(region_points)

# Convert Python data to JSON-like JS string
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

chart_js = f"""
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

    chart = Highcharts.chart('container', {{
        chart: {{
            type: 'bubble',
            width: 4800,
            height: 2700,
            backgroundColor: '#ffffff',
            marginBottom: 350,
            marginTop: 200,
            marginLeft: 200,
            marginRight: 100,
            events: {{
                load: function() {{
                    // Initial state
                    updateChart(0);
                }}
            }}
        }},
        title: {{
            text: 'scatter-animated-controls · highcharts · pyplots.ai',
            style: {{
                fontSize: '56px',
                fontWeight: 'bold'
            }},
            y: 60
        }},
        subtitle: {{
            text: 'Year: {years[0]}',
            style: {{
                fontSize: '84px',
                fontWeight: 'bold',
                color: '#444444'
            }},
            y: 140
        }},
        xAxis: {{
            title: {{
                text: 'GDP per Capita (USD)',
                style: {{
                    fontSize: '40px'
                }},
                y: 20
            }},
            labels: {{
                style: {{
                    fontSize: '32px'
                }},
                format: '${{value:,.0f}}',
                step: 2
            }},
            min: 0,
            max: 100000,
            tickInterval: 20000,
            gridLineWidth: 1,
            gridLineColor: 'rgba(0,0,0,0.1)'
        }},
        yAxis: {{
            title: {{
                text: 'Life Expectancy (Years)',
                style: {{
                    fontSize: '40px'
                }},
                x: -15
            }},
            labels: {{
                style: {{
                    fontSize: '32px'
                }}
            }},
            min: 40,
            max: 90,
            tickInterval: 5,
            gridLineColor: 'rgba(0,0,0,0.1)'
        }},
        legend: {{
            enabled: true,
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'top',
            y: 160,
            itemStyle: {{
                fontSize: '32px'
            }},
            symbolRadius: 12,
            symbolHeight: 24,
            symbolWidth: 24,
            itemDistance: 60
        }},
        tooltip: {{
            useHTML: true,
            headerFormat: '<span style="font-size: 28px; font-weight: bold;">{{point.key}}</span><br/>',
            pointFormat: '<span style="font-size: 24px;">GDP: ${{point.x:,.0f}}<br/>Life Exp: {{point.y:.1f}} years<br/>Pop: {{point.z:.1f}}M</span>',
            style: {{
                fontSize: '24px'
            }}
        }},
        plotOptions: {{
            bubble: {{
                minSize: 30,
                maxSize: 100,
                opacity: 0.8,
                marker: {{
                    fillOpacity: 0.75,
                    lineWidth: 3,
                    lineColor: 'rgba(0,0,0,0.3)'
                }},
                dataLabels: {{
                    enabled: false
                }}
            }}
        }},
        series: series
    }});

    // Expose functions to global scope for button handlers
    window.togglePlay = togglePlay;
    window.onSliderChange = onSliderChange;
}})();
"""

# Generate HTML with play controls
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
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
            background: rgba(255,255,255,0.98);
            padding: 35px 80px;
            border-radius: 25px;
            box-shadow: 0 6px 30px rgba(0,0,0,0.2);
            z-index: 1000;
        }}
        #playBtn {{
            font-size: 42px;
            padding: 25px 60px;
            cursor: pointer;
            background: #306998;
            color: white;
            border: none;
            border-radius: 15px;
            font-weight: bold;
        }}
        #playBtn:hover {{
            background: #254b73;
        }}
        #yearSlider {{
            width: 800px;
            height: 25px;
            cursor: pointer;
            accent-color: #306998;
        }}
        #yearDisplay {{
            font-size: 56px;
            font-weight: bold;
            color: #306998;
            min-width: 150px;
            text-align: center;
        }}
        .control-label {{
            font-size: 36px;
            color: #555;
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

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the interactive HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Set exact viewport size to capture full chart including controls
driver.set_window_size(4800, 2900)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
