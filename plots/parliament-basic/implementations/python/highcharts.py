""" pyplots.ai
parliament-basic: Parliament Seat Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import math
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Legislative assembly with 6 parties (neutral context, no real politics)
parties = [
    {"name": "Progressive Alliance", "seats": 85, "color": "#306998"},
    {"name": "Unity Party", "seats": 72, "color": "#FFD43B"},
    {"name": "Liberty Coalition", "seats": 48, "color": "#9467BD"},
    {"name": "Green Forum", "seats": 35, "color": "#2CA02C"},
    {"name": "Social Democrats", "seats": 28, "color": "#17BECF"},
    {"name": "Reform Movement", "seats": 12, "color": "#8C564B"},
]
total_seats = sum(p["seats"] for p in parties)


def calculate_seat_positions(parties_data, total_seats, rows=5):
    """Calculate x,y positions for seats in semicircular arcs.

    Seats are arranged so parties are grouped together across all rows,
    maintaining left-to-right party ordering in the semicircle.
    """
    positions = []

    # Calculate seats per row (more seats in outer rows)
    seats_per_row = []
    base = total_seats // rows
    extra = total_seats % rows
    for i in range(rows):
        row_seats = base + (1 if i >= rows - extra else 0)
        seats_per_row.append(row_seats)

    # For each row, distribute party seats proportionally
    for row_idx, row_seat_count in enumerate(seats_per_row):
        radius = 0.4 + row_idx * 0.15
        seat_in_row = 0

        for party_idx, party in enumerate(parties_data):
            # Proportionally allocate seats to this party in this row
            party_seats_in_row = round(party["seats"] / total_seats * row_seat_count)

            # Adjust to ensure we don't exceed row count
            remaining_parties = len(parties_data) - party_idx - 1
            remaining_seats = row_seat_count - seat_in_row
            if remaining_parties == 0:
                party_seats_in_row = remaining_seats
            elif party_seats_in_row > remaining_seats - remaining_parties:
                party_seats_in_row = max(1, remaining_seats - remaining_parties)

            for _ in range(party_seats_in_row):
                if seat_in_row >= row_seat_count:
                    break
                angle = math.pi - (seat_in_row + 0.5) * math.pi / row_seat_count
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                positions.append((x, y, party_idx))
                seat_in_row += 1

    return positions


# Calculate positions for all seats
seat_positions = calculate_seat_positions(parties, total_seats, rows=5)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 (landscape, more width for legend)
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginRight": 450,
    "marginBottom": 150,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "parliament-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
}

# Subtitle showing total seats
chart.options.subtitle = {"text": f"Total Seats: {total_seats}", "style": {"fontSize": "36px"}}

# X and Y axes - hidden but scaled for semicircle layout
chart.options.x_axis = {
    "title": {"text": None},
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickLength": 0,
    "min": -1.2,
    "max": 1.2,
}
chart.options.y_axis = {
    "title": {"text": None},
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "min": -0.1,
    "max": 1.2,
}

# Legend showing party names with seat counts
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "32px", "fontWeight": "normal"},
    "itemMarginTop": 15,
    "itemMarginBottom": 15,
    "symbolRadius": 12,
    "symbolHeight": 24,
    "symbolWidth": 24,
    "x": -40,
}

chart.options.credits = {"enabled": False}

# Tooltip configuration
chart.options.tooltip = {"headerFormat": "", "pointFormat": "<b>{series.name}</b>", "style": {"fontSize": "24px"}}

# Add a series for each party
for idx, party in enumerate(parties):
    # Get positions for this party's seats
    party_seats = [(x, y) for x, y, p_idx in seat_positions if p_idx == idx]

    series = ScatterSeries()
    series.name = f"{party['name']} ({party['seats']} seats)"
    series.data = [[float(x), float(y)] for x, y in party_seats]
    series.color = party["color"]
    series.marker = {"radius": 16, "symbol": "circle", "lineWidth": 1, "lineColor": "#333333"}

    chart.add_series(series)

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)

# Setup Chrome for screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()  # Clean up temp file
