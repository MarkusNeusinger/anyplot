""" pyplots.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: highcharts unknown | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Unicode chess symbols (white pieces are outline, black pieces are filled)
PIECES = {
    "K": "\u2654",  # White King
    "Q": "\u2655",  # White Queen
    "R": "\u2656",  # White Rook
    "B": "\u2657",  # White Bishop
    "N": "\u2658",  # White Knight
    "P": "\u2659",  # White Pawn
    "k": "\u265a",  # Black King
    "q": "\u265b",  # Black Queen
    "r": "\u265c",  # Black Rook
    "b": "\u265d",  # Black Bishop
    "n": "\u265e",  # Black Knight
    "p": "\u265f",  # Black Pawn
}

# Chess position: Scholar's Mate (after 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#)
# White has just delivered checkmate
pieces = {
    # White pieces (back rank)
    "a1": "R",
    "b1": "N",
    "c1": "B",
    "d1": "Q",
    "e1": "K",
    "f1": "B",
    "g1": "N",
    "h1": "R",
    # White pawns
    "a2": "P",
    "b2": "P",
    "c2": "P",
    "d2": "P",
    "f2": "P",
    "g2": "P",
    "h2": "P",
    # White moved pieces
    "e4": "P",  # e4 pawn
    "c4": "B",  # Bishop on c4
    "f7": "Q",  # Queen delivers checkmate on f7
    # Black pieces (back rank, missing pieces captured)
    "a8": "r",
    "b8": "n",
    "c8": "b",
    "d8": "q",
    "e8": "k",  # King in checkmate
    "f8": "b",
    "h8": "r",
    # Black pawns
    "a7": "p",
    "b7": "p",
    "c7": "p",
    "d7": "p",
    "g7": "p",
    "h7": "p",
    # Black moved pieces
    "e5": "p",  # e5 pawn
    "c6": "n",  # Knight on c6
    "f6": "n",  # Knight on f6
}

# Board colors (traditional chess board colors)
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"

# Build data for heatmap (board squares)
board_data = []
columns = list("abcdefgh")
for row in range(8):
    for col in range(8):
        # h1 should be light (white at bottom right corner)
        is_light = (row + col) % 2 == 1
        color_value = 1 if is_light else 0
        board_data.append({"x": col, "y": row, "value": color_value})

# Build piece annotations
piece_annotations = []
for square, piece in pieces.items():
    col = columns.index(square[0])
    row = int(square[1]) - 1
    symbol = PIECES[piece]
    piece_annotations.append(
        {
            "point": {"x": col, "y": row, "xAxis": 0, "yAxis": 0},
            "text": symbol,
            "allowOverlap": True,
            "backgroundColor": "transparent",
            "borderWidth": 0,
            "style": {"fontSize": "72px", "fontFamily": "DejaVu Sans, Arial Unicode MS, sans-serif"},
            "verticalAlign": "middle",
            "align": "center",
            "y": 0,
        }
    )

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - square format for chess board
chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#FFFFFF",
    "marginTop": 120,
    "marginBottom": 150,
    "marginLeft": 120,
    "marginRight": 80,
    "spacingBottom": 20,
}

# Title
chart.options.title = {
    "text": "Scholar's Mate · chessboard-pieces · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
    "y": 50,
}

# Color axis for board squares
chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, DARK_SQUARE], [1, LIGHT_SQUARE]], "visible": False}

# X-axis (columns a-h) - at bottom of chart
chart.options.x_axis = {
    "categories": list("abcdefgh"),
    "title": {"text": None},
    "labels": {"style": {"fontSize": "40px", "fontWeight": "bold"}, "y": 40, "enabled": True},
    "lineWidth": 3,
    "lineColor": "#333333",
    "tickWidth": 0,
    "opposite": False,
    "tickLength": 0,
}

# Y-axis (rows 1-8)
chart.options.y_axis = {
    "categories": ["1", "2", "3", "4", "5", "6", "7", "8"],
    "title": {"text": None},
    "labels": {"style": {"fontSize": "40px", "fontWeight": "bold"}, "x": -15},
    "lineWidth": 3,
    "lineColor": "#333333",
    "tickWidth": 0,
    "reversed": False,
    "startOnTick": False,
    "endOnTick": False,
}

# Legend hidden
chart.options.legend = {"enabled": False}

# Annotations for pieces
chart.options.annotations = [{"labels": piece_annotations, "labelOptions": {"shape": "rect"}}]

# Heatmap series for board squares
chart.options.series = [
    {
        "type": "heatmap",
        "name": "Board",
        "data": board_data,
        "borderWidth": 2,
        "borderColor": "#333333",
        "dataLabels": {"enabled": False},
        "colsize": 1,
        "rowsize": 1,
    }
]

# Plot options
chart.options.plot_options = {"heatmap": {"borderRadius": 0, "pointPadding": 0}}

# Tooltip disabled
chart.options.tooltip = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

heatmap_url = "https://code.highcharts.com/modules/heatmap.js"
with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background-color: #FFFFFF;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML output
with open("plot.html", "w", encoding="utf-8") as f:
    # For the HTML file, use CDN links for easier viewing
    html_output = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/heatmap.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0; background-color: #FFFFFF;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(html_output)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
