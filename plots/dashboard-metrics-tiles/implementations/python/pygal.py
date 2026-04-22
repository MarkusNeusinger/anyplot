""" pyplots.ai
dashboard-metrics-tiles: Real-Time Dashboard Tiles
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

from io import BytesIO

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data - Dashboard metrics with history and status
np.random.seed(42)

metrics = [
    {
        "name": "CPU Usage",
        "value": 45,
        "unit": "%",
        "change": -5.2,
        "status": "good",
        "history": [52, 48, 55, 51, 47, 50, 48, 45, 46, 44, 45],
    },
    {
        "name": "Memory",
        "value": 72,
        "unit": "%",
        "change": 8.3,
        "status": "warning",
        "history": [65, 66, 68, 67, 70, 69, 71, 70, 72, 71, 72],
    },
    {
        "name": "Response Time",
        "value": 120,
        "unit": "ms",
        "change": -15.0,
        "status": "good",
        "history": [145, 142, 138, 135, 130, 128, 125, 122, 121, 120, 120],
    },
    {
        "name": "Error Rate",
        "value": 2.1,
        "unit": "%",
        "change": 45.0,
        "status": "critical",
        "history": [1.2, 1.4, 1.3, 1.5, 1.6, 1.8, 1.9, 2.0, 2.0, 2.1, 2.1],
    },
    {
        "name": "Throughput",
        "value": 1250,
        "unit": "req/s",
        "change": 12.5,
        "status": "good",
        "history": [1100, 1120, 1150, 1180, 1200, 1210, 1220, 1230, 1240, 1245, 1250],
    },
    {
        "name": "Active Users",
        "value": 3420,
        "unit": "",
        "change": 5.8,
        "status": "good",
        "history": [3200, 3220, 3280, 3310, 3350, 3380, 3390, 3400, 3410, 3415, 3420],
    },
]

# Color palette
COLORS = {
    "good": "#2ECC71",  # Green
    "warning": "#F1C40F",  # Yellow
    "critical": "#E74C3C",  # Red
    "change_positive": "#2ECC71",  # Green for favorable
    "change_negative": "#E74C3C",  # Red for unfavorable
    "sparkline": "#306998",  # Python Blue
    "text_primary": "#1a1a1a",
    "text_secondary": "#666666",
    "background": "#ffffff",
    "tile_bg": "#f8f9fa",
}

# Determine if change is favorable (depends on metric type)
LOWER_IS_BETTER = {"CPU Usage", "Memory", "Response Time", "Error Rate"}


def is_favorable_change(metric_name, change):
    """Determine if the change is favorable for display coloring."""
    if metric_name in LOWER_IS_BETTER:
        return change < 0  # Negative change is good
    return change > 0  # Positive change is good


# Layout settings
CANVAS_WIDTH = 4800
CANVAS_HEIGHT = 2700
TITLE_HEIGHT = 150
GRID_COLS = 3
GRID_ROWS = 2
TILE_MARGIN = 40
TILE_PADDING = 50

# Calculate tile dimensions
grid_width = CANVAS_WIDTH - 2 * TILE_MARGIN
grid_height = CANVAS_HEIGHT - TITLE_HEIGHT - 2 * TILE_MARGIN
tile_width = (grid_width - (GRID_COLS - 1) * TILE_MARGIN) // GRID_COLS
tile_height = (grid_height - (GRID_ROWS - 1) * TILE_MARGIN) // GRID_ROWS

# Create sparkline charts for each metric
sparkline_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground="transparent",
    foreground_strong="transparent",
    foreground_subtle="transparent",
    colors=(COLORS["sparkline"],),
    stroke_width=4,
)


def create_sparkline(history, width, height):
    """Create a sparkline chart for the given history data."""
    chart = pygal.Line(
        width=width,
        height=height,
        style=sparkline_style,
        show_legend=False,
        show_dots=False,
        show_y_labels=False,
        show_x_labels=False,
        show_y_guides=False,
        show_x_guides=False,
        margin=0,
        spacing=0,
        fill=True,
        stroke_style={"width": 4, "linecap": "round", "linejoin": "round"},
    )
    chart.add("", history)
    svg_bytes = chart.render()
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=width, output_height=height)
    return Image.open(BytesIO(png_bytes))


def draw_tile(draw, img, x, y, metric, fonts):
    """Draw a single metric tile at the specified position."""
    # Draw tile background with rounded corners (approximate with rectangle)
    tile_rect = [x, y, x + tile_width, y + tile_height]
    draw.rounded_rectangle(tile_rect, radius=20, fill=COLORS["tile_bg"])

    # Draw status indicator bar at top
    status_bar_height = 8
    status_color = COLORS[metric["status"]]
    draw.rectangle([x, y, x + tile_width, y + status_bar_height], fill=status_color)

    # Calculate content positions
    content_x = x + TILE_PADDING
    content_y = y + TILE_PADDING + status_bar_height

    # Draw metric name
    name_font = fonts["name"]
    draw.text((content_x, content_y), metric["name"], fill=COLORS["text_secondary"], font=name_font)
    content_y += 60

    # Draw main value with unit
    value_font = fonts["value"]
    value_text = f"{metric['value']:,}{metric['unit']}"
    draw.text((content_x, content_y), value_text, fill=COLORS["text_primary"], font=value_font)
    content_y += 120

    # Draw change indicator with arrow
    change = metric["change"]
    favorable = is_favorable_change(metric["name"], change)
    change_color = COLORS["change_positive"] if favorable else COLORS["change_negative"]
    arrow = "▲" if change > 0 else "▼" if change < 0 else "●"
    change_text = f"{arrow} {abs(change):.1f}%"
    change_font = fonts["change"]
    draw.text((content_x, content_y), change_text, fill=change_color, font=change_font)

    # Draw sparkline at the right side of the tile
    sparkline_width = 300
    sparkline_height = 100
    sparkline_x = x + tile_width - TILE_PADDING - sparkline_width
    sparkline_y = y + tile_height - TILE_PADDING - sparkline_height - 20

    sparkline_img = create_sparkline(metric["history"], sparkline_width, sparkline_height)
    img.paste(sparkline_img, (sparkline_x, sparkline_y), sparkline_img.convert("RGBA"))


# Create main canvas
canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), COLORS["background"])
draw = ImageDraw.Draw(canvas)

# Load fonts
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    value_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 96)
    name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
    change_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
except OSError:
    title_font = ImageFont.load_default()
    value_font = ImageFont.load_default()
    name_font = ImageFont.load_default()
    change_font = ImageFont.load_default()

fonts = {"title": title_font, "value": value_font, "name": name_font, "change": change_font}

# Draw main title
title_text = "dashboard-metrics-tiles · pygal · pyplots.ai"
bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = bbox[2] - bbox[0]
title_x = (CANVAS_WIDTH - title_width) // 2
draw.text((title_x, 50), title_text, fill=COLORS["text_primary"], font=title_font)

# Draw metric tiles in 3x2 grid
for idx, metric in enumerate(metrics):
    row = idx // GRID_COLS
    col = idx % GRID_COLS
    tile_x = TILE_MARGIN + col * (tile_width + TILE_MARGIN)
    tile_y = TITLE_HEIGHT + TILE_MARGIN + row * (tile_height + TILE_MARGIN)
    draw_tile(draw, canvas, tile_x, tile_y, metric, fonts)

# Save PNG output
canvas.save("plot.png", dpi=(300, 300))

# Create interactive HTML version with embedded SVG sparklines
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>dashboard-metrics-tiles · pygal · pyplots.ai</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #ffffff;
            padding: 40px;
        }
        h1 {
            text-align: center;
            color: #1a1a1a;
            font-size: 32px;
            margin-bottom: 40px;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .tile {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 24px;
            position: relative;
            overflow: hidden;
        }
        .status-bar {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }
        .status-good { background: #2ECC71; }
        .status-warning { background: #F1C40F; }
        .status-critical { background: #E74C3C; }
        .metric-name {
            color: #666666;
            font-size: 16px;
            margin-bottom: 8px;
        }
        .metric-value {
            color: #1a1a1a;
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .metric-change {
            font-size: 18px;
            font-weight: 600;
        }
        .change-positive { color: #2ECC71; }
        .change-negative { color: #E74C3C; }
        .sparkline {
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 120px;
            height: 50px;
        }
        .sparkline svg { width: 100%; height: 100%; }
        @media (max-width: 900px) {
            .dashboard { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 600px) {
            .dashboard { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <h1>dashboard-metrics-tiles · pygal · pyplots.ai</h1>
    <div class="dashboard">
"""

# Generate HTML tiles with SVG sparklines
for metric in metrics:
    favorable = is_favorable_change(metric["name"], metric["change"])
    change_class = "change-positive" if favorable else "change-negative"
    arrow = "▲" if metric["change"] > 0 else "▼" if metric["change"] < 0 else "●"

    # Create mini sparkline SVG
    mini_chart = pygal.Line(
        width=200,
        height=80,
        style=sparkline_style,
        show_legend=False,
        show_dots=False,
        show_y_labels=False,
        show_x_labels=False,
        show_y_guides=False,
        show_x_guides=False,
        margin=5,
        fill=True,
    )
    mini_chart.add("", metric["history"])
    sparkline_svg = mini_chart.render(is_unicode=True)
    sparkline_svg = sparkline_svg.replace('<?xml version="1.0" encoding="utf-8"?>', "")

    html_content += f"""        <div class="tile">
            <div class="status-bar status-{metric["status"]}"></div>
            <div class="metric-name">{metric["name"]}</div>
            <div class="metric-value">{metric["value"]:,}{metric["unit"]}</div>
            <div class="metric-change {change_class}">{arrow} {abs(metric["change"]):.1f}%</div>
            <div class="sparkline">{sparkline_svg}</div>
        </div>
"""

html_content += """    </div>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
