"""anyplot.ai
chessboard-pieces: Chess Board with Pieces for Position Diagrams
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Unicode chess symbols (white pieces are outline, black pieces are filled)
PIECES = {
    "K": "♔",  # White King
    "Q": "♕",  # White Queen
    "R": "♖",  # White Rook
    "B": "♗",  # White Bishop
    "N": "♘",  # White Knight
    "P": "♙",  # White Pawn
    "k": "♚",  # Black King
    "q": "♛",  # Black Queen
    "r": "♜",  # Black Rook
    "b": "♝",  # Black Bishop
    "n": "♞",  # Black Knight
    "p": "♟",  # Black Pawn
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
            "style": {"fontSize": "72px", "fontFamily": "DejaVu Sans, Arial Unicode MS, sans-serif", "color": INK},
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
    "backgroundColor": PAGE_BG,
    "marginTop": 120,
    "marginBottom": 150,
    "marginLeft": 120,
    "marginRight": 80,
    "spacingBottom": 20,
}

# Title
chart.options.title = {
    "text": "Scholar's Mate · chessboard-pieces · highcharts · anyplot.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": INK},
    "y": 50,
}

# Color axis for board squares
chart.options.color_axis = {"min": 0, "max": 1, "stops": [[0, DARK_SQUARE], [1, LIGHT_SQUARE]], "visible": False}

# X-axis (columns a-h) - at bottom of chart
chart.options.x_axis = {
    "categories": list("abcdefgh"),
    "title": {"text": None},
    "labels": {"style": {"fontSize": "40px", "fontWeight": "bold", "color": INK_SOFT}, "y": 40, "enabled": True},
    "lineWidth": 3,
    "lineColor": INK_SOFT,
    "tickWidth": 0,
    "opposite": False,
    "tickLength": 0,
}

# Y-axis (rows 1-8)
chart.options.y_axis = {
    "categories": ["1", "2", "3", "4", "5", "6", "7", "8"],
    "title": {"text": None},
    "labels": {"style": {"fontSize": "40px", "fontWeight": "bold", "color": INK_SOFT}, "x": -15},
    "lineWidth": 3,
    "lineColor": INK_SOFT,
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
        "borderColor": INK_SOFT,
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


# Download Highcharts JS and required modules
def download_script(url, timeout=30, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2**attempt)


highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
highcharts_js = download_script(highcharts_url, timeout=60)

heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/heatmap.js"
heatmap_js = download_script(heatmap_url, timeout=60)

annotations_url = "https://cdn.jsdelivr.net/npm/highcharts/modules/annotations.js"
annotations_js = download_script(annotations_url, timeout=60)

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
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML output with theme suffix
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
