""" pyplots.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import load_iris


# Load Iris dataset
iris = load_iris()
x = iris.data[:, 0]  # Sepal length
y = iris.data[:, 1]  # Sepal width
value = iris.data[:, 2]  # Petal length
categories = [str(iris.target_names[t]) for t in iris.target]  # Convert to native Python str
category_colors = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#9467BD"}

# Prepare data as JavaScript-friendly format
data_points = []
for i in range(len(x)):
    data_points.append(
        {"x": float(x[i]), "y": float(y[i]), "value": float(value[i]), "category": categories[i], "index": i}
    )

# Create histogram bins for petal length
hist_bins = np.histogram(value, bins=10)
hist_counts = hist_bins[0].tolist()
hist_edges = hist_bins[1].tolist()
hist_labels = [f"{hist_edges[i]:.1f}-{hist_edges[i + 1]:.1f}" for i in range(len(hist_counts))]

# Category counts for bar chart
category_counts = {}
for cat in categories:
    category_counts[cat] = category_counts.get(cat, 0) + 1

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Highcharts-more for additional chart types
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Create the HTML with three linked charts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 40px;
            background: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 48px;
            font-weight: 600;
            color: #1f2937;
            margin: 0;
        }}
        .subtitle {{
            font-size: 28px;
            color: #6b7280;
            margin-top: 10px;
        }}
        .charts-container {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 40px;
            height: 2400px;
            padding: 20px;
        }}
        .scatter-chart {{
            grid-row: span 2;
        }}
        .chart-box {{
            background: #fafafa;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .controls {{
            text-align: center;
            margin-top: 30px;
        }}
        .reset-btn {{
            padding: 16px 48px;
            font-size: 24px;
            background: #306998;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
        }}
        .reset-btn:hover {{
            background: #254d73;
        }}
        .selection-info {{
            font-size: 28px;
            color: #374151;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">linked-views-selection · highcharts · pyplots.ai</h1>
        <p class="subtitle">Iris Dataset: Select points in scatter plot to highlight in all views</p>
    </div>

    <div class="charts-container">
        <div id="scatter-container" class="chart-box scatter-chart"></div>
        <div id="bar-container" class="chart-box"></div>
        <div id="histogram-container" class="chart-box"></div>
    </div>

    <div class="controls">
        <button class="reset-btn" onclick="resetSelection()">Reset Selection</button>
        <div id="selection-info" class="selection-info">Click and drag on the scatter plot to select points</div>
    </div>

    <script>
        // Data points
        const allData = {json.dumps(data_points)};
        const categoryColors = {{"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#9467BD"}};
        const categoryList = ["setosa", "versicolor", "virginica"];

        // Track selected indices
        let selectedIndices = new Set();

        // Prepare scatter series data by category
        function getScatterSeries(highlightIndices = null) {{
            return categoryList.map(cat => {{
                const points = allData.filter(d => d.category === cat).map(d => {{
                    const isSelected = highlightIndices === null || highlightIndices.has(d.index);
                    return {{
                        x: d.x,
                        y: d.y,
                        index: d.index,
                        marker: {{
                            fillColor: isSelected ? categoryColors[cat] : '#cccccc',
                            lineColor: isSelected ? categoryColors[cat] : '#cccccc',
                            radius: isSelected ? 12 : 8
                        }},
                        opacity: isSelected ? 1 : 0.3
                    }};
                }});
                return {{
                    name: cat.charAt(0).toUpperCase() + cat.slice(1),
                    data: points,
                    color: categoryColors[cat],
                    marker: {{ radius: 12, symbol: 'circle' }}
                }};
            }});
        }}

        // Prepare bar chart data
        function getBarData(highlightIndices = null) {{
            return categoryList.map(cat => {{
                let count;
                if (highlightIndices === null || highlightIndices.size === 0) {{
                    count = allData.filter(d => d.category === cat).length;
                }} else {{
                    count = allData.filter(d => d.category === cat && highlightIndices.has(d.index)).length;
                }}
                const isActive = highlightIndices === null || highlightIndices.size === 0 || count > 0;
                return {{
                    name: cat.charAt(0).toUpperCase() + cat.slice(1),
                    y: count,
                    color: isActive ? categoryColors[cat] : '#cccccc'
                }};
            }});
        }}

        // Prepare histogram data
        function getHistogramData(highlightIndices = null) {{
            const bins = {json.dumps(hist_labels)};
            const edges = {json.dumps(hist_edges)};

            return bins.map((label, i) => {{
                let count;
                if (highlightIndices === null || highlightIndices.size === 0) {{
                    count = allData.filter(d => d.value >= edges[i] && d.value < edges[i+1]).length;
                }} else {{
                    count = allData.filter(d =>
                        highlightIndices.has(d.index) &&
                        d.value >= edges[i] &&
                        d.value < edges[i+1]
                    ).length;
                }}
                const isActive = highlightIndices === null || highlightIndices.size === 0 || count > 0;
                return {{
                    name: label,
                    y: count,
                    color: isActive ? '#306998' : '#cccccc'
                }};
            }});
        }}

        // Create scatter chart
        const scatterChart = Highcharts.chart('scatter-container', {{
            chart: {{
                type: 'scatter',
                zoomType: 'xy',
                backgroundColor: 'transparent',
                style: {{ fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }},
                events: {{
                    selection: function(event) {{
                        if (event.xAxis && event.yAxis) {{
                            const xMin = event.xAxis[0].min;
                            const xMax = event.xAxis[0].max;
                            const yMin = event.yAxis[0].min;
                            const yMax = event.yAxis[0].max;

                            selectedIndices = new Set();
                            allData.forEach(d => {{
                                if (d.x >= xMin && d.x <= xMax && d.y >= yMin && d.y <= yMax) {{
                                    selectedIndices.add(d.index);
                                }}
                            }});

                            updateAllCharts();
                            event.preventDefault();
                        }}
                        return false;
                    }}
                }}
            }},
            title: {{
                text: 'Sepal Dimensions by Species',
                style: {{ fontSize: '32px', fontWeight: '600' }}
            }},
            xAxis: {{
                title: {{
                    text: 'Sepal Length (cm)',
                    style: {{ fontSize: '24px' }}
                }},
                labels: {{ style: {{ fontSize: '20px' }} }},
                gridLineWidth: 1,
                gridLineColor: '#e5e7eb'
            }},
            yAxis: {{
                title: {{
                    text: 'Sepal Width (cm)',
                    style: {{ fontSize: '24px' }}
                }},
                labels: {{ style: {{ fontSize: '20px' }} }},
                gridLineColor: '#e5e7eb'
            }},
            legend: {{
                enabled: true,
                itemStyle: {{ fontSize: '22px' }},
                symbolRadius: 6
            }},
            plotOptions: {{
                scatter: {{
                    marker: {{
                        radius: 12,
                        states: {{
                            hover: {{ enabled: true, radiusPlus: 4 }}
                        }}
                    }},
                    states: {{
                        inactive: {{ opacity: 1 }}
                    }}
                }}
            }},
            tooltip: {{
                style: {{ fontSize: '18px' }},
                headerFormat: '<b>{{series.name}}</b><br>',
                pointFormat: 'Sepal: {{point.x:.1f}} x {{point.y:.1f}} cm'
            }},
            series: getScatterSeries()
        }});

        // Create bar chart
        const barChart = Highcharts.chart('bar-container', {{
            chart: {{
                type: 'column',
                backgroundColor: 'transparent',
                style: {{ fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }}
            }},
            title: {{
                text: 'Species Distribution',
                style: {{ fontSize: '28px', fontWeight: '600' }}
            }},
            xAxis: {{
                type: 'category',
                labels: {{ style: {{ fontSize: '20px' }} }}
            }},
            yAxis: {{
                title: {{
                    text: 'Count',
                    style: {{ fontSize: '22px' }}
                }},
                labels: {{ style: {{ fontSize: '18px' }} }},
                gridLineColor: '#e5e7eb'
            }},
            legend: {{ enabled: false }},
            plotOptions: {{
                column: {{
                    borderRadius: 6,
                    dataLabels: {{
                        enabled: true,
                        style: {{ fontSize: '20px', fontWeight: '600' }}
                    }}
                }}
            }},
            tooltip: {{
                style: {{ fontSize: '18px' }},
                pointFormat: '<b>{{point.y}}</b> specimens'
            }},
            series: [{{
                name: 'Count',
                data: getBarData(),
                colorByPoint: true
            }}]
        }});

        // Create histogram
        const histogramChart = Highcharts.chart('histogram-container', {{
            chart: {{
                type: 'column',
                backgroundColor: 'transparent',
                style: {{ fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }}
            }},
            title: {{
                text: 'Petal Length Distribution',
                style: {{ fontSize: '28px', fontWeight: '600' }}
            }},
            xAxis: {{
                type: 'category',
                labels: {{
                    style: {{ fontSize: '16px' }},
                    rotation: -45
                }}
            }},
            yAxis: {{
                title: {{
                    text: 'Count',
                    style: {{ fontSize: '22px' }}
                }},
                labels: {{ style: {{ fontSize: '18px' }} }},
                gridLineColor: '#e5e7eb'
            }},
            legend: {{ enabled: false }},
            plotOptions: {{
                column: {{
                    borderRadius: 4,
                    dataLabels: {{
                        enabled: true,
                        style: {{ fontSize: '18px', fontWeight: '600' }}
                    }}
                }}
            }},
            tooltip: {{
                style: {{ fontSize: '18px' }},
                pointFormat: '<b>{{point.y}}</b> specimens'
            }},
            series: [{{
                name: 'Count',
                data: getHistogramData(),
                colorByPoint: false,
                color: '#306998'
            }}]
        }});

        // Update all charts based on selection
        function updateAllCharts() {{
            const indices = selectedIndices.size > 0 ? selectedIndices : null;

            // Update scatter chart
            const newScatterSeries = getScatterSeries(indices);
            scatterChart.series.forEach((series, i) => {{
                series.setData(newScatterSeries[i].data, false);
            }});
            scatterChart.redraw();

            // Update bar chart
            barChart.series[0].setData(getBarData(indices), true);

            // Update histogram
            histogramChart.series[0].setData(getHistogramData(indices), true);

            // Update selection info
            const infoEl = document.getElementById('selection-info');
            if (selectedIndices.size > 0) {{
                infoEl.textContent = `Selected: ${{selectedIndices.size}} of ${{allData.length}} points`;
            }} else {{
                infoEl.textContent = 'Click and drag on the scatter plot to select points';
            }}
        }}

        // Reset selection
        function resetSelection() {{
            selectedIndices = new Set();
            scatterChart.zoomOut();
            updateAllCharts();
        }}
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save as plot.html for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)  # Wait for charts to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
