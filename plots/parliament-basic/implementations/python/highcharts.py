""" anyplot.ai
parliament-basic: Parliament Seat Chart
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Legislative assembly with 6 parties (neutral context, no real politics)
parties = [
    {"name": "Progressive Alliance", "seats": 85},
    {"name": "Unity Party", "seats": 72},
    {"name": "Liberty Coalition", "seats": 48},
    {"name": "Green Forum", "seats": 35},
    {"name": "Social Democrats", "seats": 28},
    {"name": "Reform Movement", "seats": 12},
]
total_seats = sum(p["seats"] for p in parties)

# Calculate seat positions inline
positions = []
rows = 5

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

    for party_idx, party in enumerate(parties):
        # Proportionally allocate seats to this party in this row
        party_seats_in_row = round(party["seats"] / total_seats * row_seat_count)

        # Adjust to ensure we don't exceed row count
        remaining_parties = len(parties) - party_idx - 1
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

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginRight": 450,
    "marginBottom": 150,
    "marginTop": 150,
}

# Title and styling
chart.options.title = {
    "text": "parliament-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
}

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
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "itemMarginTop": 15,
    "itemMarginBottom": 15,
    "symbolRadius": 12,
    "symbolHeight": 24,
    "symbolWidth": 24,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "x": -40,
}

chart.options.credits = {"enabled": False}

# Tooltip
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b>",
    "style": {"fontSize": "18px", "color": INK},
}

# Set color palette
chart.options.colors = IMPRINT

# Add a series for each party
for idx, party in enumerate(parties):
    # Get positions for this party's seats
    party_seats = [[float(x), float(y)] for x, y, p_idx in positions if p_idx == idx]

    series = ScatterSeries()
    series.name = f"{party['name']} ({party['seats']} seats)"
    series.data = party_seats
    series.color = IMPRINT[idx % len(IMPRINT)]
    series.marker = {"radius": 8, "symbol": "circle", "lineWidth": 1, "lineColor": PAGE_BG}

    chart.add_series(series)

# Download Highcharts JS (required for headless Chrome)
# Try multiple CDN sources
highcharts_urls = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js",
]

highcharts_js = None
for url in highcharts_urls:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=10) as response:
            highcharts_js = response.read().decode("utf-8")
            break
    except Exception:
        continue

if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from all CDN sources")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Setup Chrome for screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
