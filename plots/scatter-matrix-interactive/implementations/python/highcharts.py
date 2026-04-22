""" pyplots.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
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


# Data - Iris dataset (4 variables for a 4x4 matrix)
iris = load_iris()
data = iris.data
feature_names = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]
species = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]
colors = ["#306998", "#FFD43B", "#9467BD"]

n_vars = 4
n_points = len(data)

# Build chart configuration manually for scatter matrix with linked brushing
# Using synchronized charts in a grid layout

# Build series data for each cell in the matrix
chart_configs = []

for row in range(n_vars):
    for col in range(n_vars):
        if row == col:
            # Diagonal: histogram for univariate distribution
            # Create histogram data for each species
            series_data = []
            for sp_idx, sp_name in enumerate(species_names):
                sp_mask = species == sp_idx
                values = data[sp_mask, row]
                # Create histogram bins
                hist, bin_edges = np.histogram(values, bins=15)
                hist_data = []
                for i in range(len(hist)):
                    hist_data.append([float(bin_edges[i]), int(hist[i])])
                series_data.append(
                    {
                        "name": sp_name,
                        "data": hist_data,
                        "color": colors[sp_idx],
                        "type": "column",
                        "pointPadding": 0,
                        "groupPadding": 0,
                        "borderWidth": 0,
                    }
                )
            chart_configs.append(
                {
                    "type": "histogram",
                    "row": row,
                    "col": col,
                    "series": series_data,
                    "xTitle": feature_names[col] if row == n_vars - 1 else "",
                    "yTitle": feature_names[row] if col == 0 else "",
                }
            )
        else:
            # Off-diagonal: scatter plot
            series_data = []
            for sp_idx, sp_name in enumerate(species_names):
                sp_mask = species == sp_idx
                x_vals = data[sp_mask, col]
                y_vals = data[sp_mask, row]
                points = []
                for i, (x, y) in enumerate(zip(x_vals, y_vals, strict=True)):
                    points.append({"x": float(x), "y": float(y), "id": f"p{np.where(sp_mask)[0][i]}"})
                series_data.append({"name": sp_name, "data": points, "color": colors[sp_idx], "type": "scatter"})
            chart_configs.append(
                {
                    "type": "scatter",
                    "row": row,
                    "col": col,
                    "series": series_data,
                    "xTitle": feature_names[col] if row == n_vars - 1 else "",
                    "yTitle": feature_names[row] if col == 0 else "",
                }
            )

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download Highcharts More for extended features
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Download exporting module for selection handling
exporting_url = "https://code.highcharts.com/modules/exporting.js"
with urllib.request.urlopen(exporting_url, timeout=30) as response:
    exporting_js = response.read().decode("utf-8")

# Build JavaScript for all charts in the matrix
charts_js = ""
for config in chart_configs:
    row = config["row"]
    col = config["col"]
    container_id = f"chart_{row}_{col}"

    # Common chart options
    chart_options = {
        "chart": {
            "backgroundColor": "#ffffff",
            "animation": False,
            "zoomType": "xy",
            "panning": {"enabled": True, "type": "xy"},
            "panKey": "shift",
            "resetZoomButton": {"position": {"x": -10, "y": 10}, "theme": {"style": {"fontSize": "14px"}}},
            "marginLeft": 80 if col == 0 else 40,
            "marginBottom": 60 if row == n_vars - 1 else 30,
        },
        "title": {"text": None},
        "credits": {"enabled": False},
        "legend": {"enabled": False},
        "exporting": {"enabled": False},
        "xAxis": {
            "title": {"text": config["xTitle"], "style": {"fontSize": "18px", "fontWeight": "bold"}},
            "labels": {"style": {"fontSize": "16px"}},
            "gridLineWidth": 1,
            "gridLineColor": "rgba(0,0,0,0.15)",
        },
        "yAxis": {
            "title": {"text": config["yTitle"], "style": {"fontSize": "18px", "fontWeight": "bold"}},
            "labels": {"style": {"fontSize": "16px"}},
            "gridLineWidth": 1,
            "gridLineColor": "rgba(0,0,0,0.15)",
        },
        "plotOptions": {
            "scatter": {
                "marker": {
                    "radius": 8,
                    "symbol": "circle",
                    "states": {
                        "hover": {"enabled": True, "lineColor": "#000000", "lineWidth": 2},
                        "select": {"fillColor": None, "lineWidth": 3, "lineColor": "#000000"},
                    },
                },
                "allowPointSelect": True,
                "cursor": "pointer",
                "states": {"inactive": {"opacity": 0.3}},
            },
            "column": {"borderWidth": 0, "groupPadding": 0.05, "pointPadding": 0},
        },
        "series": config["series"],
        "tooltip": {
            "headerFormat": "<b>{series.name}</b><br>",
            "pointFormat": "x: {point.x:.2f}, y: {point.y:.2f}" if config["type"] == "scatter" else "Count: {point.y}",
            "style": {"fontSize": "16px"},
        },
    }

    charts_js += f"""
    var chart_{row}_{col} = Highcharts.chart('{container_id}', {json.dumps(chart_options)});
    allCharts.push({{chart: chart_{row}_{col}, row: {row}, col: {col}, type: '{config["type"]}'}});
    """

# Create linked brushing JavaScript
linked_brushing_js = """
var allCharts = [];
var selectedPoints = new Set();

function syncSelection(sourceChart, selectedIds) {
    selectedPoints = new Set(selectedIds);

    allCharts.forEach(function(chartObj) {
        if (chartObj.type !== 'scatter') return;

        chartObj.chart.series.forEach(function(series) {
            series.points.forEach(function(point) {
                if (point.id) {
                    if (selectedPoints.size === 0) {
                        point.setState('');
                        point.graphic && point.graphic.attr({opacity: 1});
                    } else if (selectedPoints.has(point.id)) {
                        point.setState('select');
                        point.graphic && point.graphic.attr({opacity: 1});
                    } else {
                        point.setState('');
                        point.graphic && point.graphic.attr({opacity: 0.15});
                    }
                }
            });
        });
    });
}

function clearAllSelections() {
    selectedPoints.clear();
    syncSelection(null, []);
}

// Add click handlers after charts are created
function setupClickHandlers() {
    allCharts.forEach(function(chartObj) {
        if (chartObj.type !== 'scatter') return;

        chartObj.chart.series.forEach(function(series) {
            series.options.point = series.options.point || {};
            series.options.point.events = series.options.point.events || {};
        });

        // Handle point selection on click
        Highcharts.addEvent(chartObj.chart.container, 'click', function(e) {
            var chart = chartObj.chart;
            var point = chart.hoverPoint;

            if (point && point.id) {
                if (e.ctrlKey || e.metaKey) {
                    // Multi-select with Ctrl/Cmd
                    if (selectedPoints.has(point.id)) {
                        selectedPoints.delete(point.id);
                    } else {
                        selectedPoints.add(point.id);
                    }
                } else {
                    // Single select
                    selectedPoints.clear();
                    selectedPoints.add(point.id);
                }
                syncSelection(chart, Array.from(selectedPoints));
            }
        });
    });
}

// Double-click to clear selection
document.addEventListener('dblclick', function() {
    clearAllSelections();
});
"""

# Build HTML with grid layout
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{exporting_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        .title {{
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
        }}
        .subtitle {{
            text-align: center;
            font-size: 22px;
            color: #666;
            margin-bottom: 15px;
        }}
        .matrix-container {{
            display: grid;
            grid-template-columns: repeat({n_vars}, 1fr);
            grid-template-rows: repeat({n_vars}, 1fr);
            gap: 8px;
            width: 4760px;
            height: 2350px;
            margin: 0 auto;
        }}
        .chart-cell {{
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }}
        .legend-container {{
            display: flex;
            justify-content: center;
            gap: 60px;
            margin-top: 20px;
            font-size: 24px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .legend-color {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
        }}
        .instructions {{
            text-align: center;
            font-size: 20px;
            color: #666;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="title">scatter-matrix-interactive &middot; highcharts &middot; pyplots.ai</div>
    <div class="subtitle">Iris Dataset - Interactive Scatter Plot Matrix with Linked Brushing</div>

    <div class="matrix-container">
"""

# Add chart containers
for row in range(n_vars):
    for col in range(n_vars):
        container_id = f"chart_{row}_{col}"
        html_content += f'        <div id="{container_id}" class="chart-cell"></div>\n'

html_content += f"""
    </div>

    <div class="legend-container">
        <div class="legend-item">
            <div class="legend-color" style="background-color: {colors[0]};"></div>
            <span>Setosa</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {colors[1]};"></div>
            <span>Versicolor</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {colors[2]};"></div>
            <span>Virginica</span>
        </div>
    </div>
    <div class="instructions">Click to select points | Ctrl+Click for multi-select | Double-click to clear | Drag to zoom | Shift+Drag to pan</div>

    <script>
    {linked_brushing_js}

    {charts_js}

    // Setup click handlers after charts are created
    setupClickHandlers();
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Export to PNG using Selenium
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
time.sleep(6)  # Wait for all charts to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
