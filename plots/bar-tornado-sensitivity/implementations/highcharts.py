"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import tempfile
import time
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# Data - NPV sensitivity analysis for a capital investment project
base_npv = 12.5  # Base case NPV in $M

parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Material Cost",
    "Labor Cost",
    "Project Duration",
    "Tax Rate",
    "Salvage Value",
    "Inflation Rate",
    "Market Share",
    "Operating Expenses",
]

low_values = [8.1, 9.2, 10.0, 10.5, 10.8, 11.0, 11.2, 11.5, 9.8, 11.0]
high_values = [17.8, 16.5, 15.2, 14.8, 14.5, 14.2, 13.9, 13.6, 15.5, 14.0]

# Sort by total range (widest bar first)
ranges = [high_values[i] - low_values[i] for i in range(len(parameters))]
sorted_indices = sorted(range(len(parameters)), key=lambda i: ranges[i], reverse=True)

sorted_params = [parameters[i] for i in sorted_indices]
sorted_low = [round(low_values[i] - base_npv, 1) for i in sorted_indices]
sorted_high = [round(high_values[i] - base_npv, 1) for i in sorted_indices]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bar",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 380,
    "marginRight": 100,
    "marginTop": 140,
    "marginBottom": 200,
}

chart.options.title = {
    "text": "bar-tornado-sensitivity \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
    "y": 30,
}

chart.options.subtitle = {
    "text": "NPV Sensitivity Analysis \u2014 Base Case: $12.5M",
    "style": {"fontSize": "32px", "color": "#555555"},
    "y": 80,
}

chart.options.x_axis = {
    "categories": sorted_params,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "28px"}},
    "lineWidth": 0,
    "tickWidth": 0,
}

chart.options.y_axis = {
    "title": {"text": "Change in NPV ($M)", "style": {"fontSize": "28px"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.08)",
    "plotLines": [{"value": 0, "width": 3, "color": "#333333", "zIndex": 5}],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "align": "center",
    "y": 20,
}

chart.options.credits = {"enabled": False}
chart.options.accessibility = {"enabled": False}

chart.options.plot_options = {
    "bar": {"grouping": False, "borderWidth": 0, "pointWidth": 80, "pointPadding": 0, "groupPadding": 0.15}
}

# Low scenario series (negative deviations from base)
low_series = BarSeries()
low_series.name = "Low Scenario"
low_series.data = sorted_low
low_series.color = "#306998"

# High scenario series (positive deviations from base)
high_series = BarSeries()
high_series.name = "High Scenario"
high_series.data = sorted_high
high_series.color = "#FFD43B"

chart.add_series(low_series)
chart.add_series(high_series)

# Generate HTML with external CDN script
html_str = chart.to_js_literal()
html_content = (
    '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n'
    '<script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>\n'
    '</head>\n<body style="margin:0; padding:0; background:#ffffff;">\n'
    '<div id="container" style="width: 4800px; height: 2700px;"></div>\n'
    "<script>" + html_str + "</script>\n</body>\n</html>"
)

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element(By.ID, "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
