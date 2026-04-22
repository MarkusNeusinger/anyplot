""" pyplots.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

from io import BytesIO

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data - Dashboard showing sales performance across different dimensions
np.random.seed(42)

# Time series data for main overview chart (Panel A - wide)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
revenue = [120, 135, 142, 138, 155, 168, 172, 185, 178, 192, 205, 218]
costs = [85, 88, 92, 90, 98, 105, 108, 115, 112, 120, 128, 135]

# Category data for bar chart (Panel B)
categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]
category_sales = [450, 320, 280, 195, 165]

# Pie chart data for market share (Panel C)
regions = ["North", "South", "East", "West"]
region_shares = [35, 28, 22, 15]

# Scatter data for correlation (Panel D)
n_points = 40
marketing_spend = np.random.uniform(10, 100, n_points)
sales_response = marketing_spend * 2.5 + np.random.normal(0, 25, n_points)

# Gauge data for KPI (Panel E)
current_target_pct = 78

# Custom style for pyplots
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4CAF50", "#FF5722", "#9C27B0", "#00BCD4"),
    font_family="sans-serif",
    title_font_size=36,
    label_font_size=24,
    major_label_font_size=22,
    legend_font_size=22,
    value_font_size=18,
    stroke_width=4,
    opacity=0.9,
    opacity_hover=1.0,
)

# Mosaic layout pattern: "AAB;AAC;DDE"
# A = large chart (2x2), B = medium chart (1x1), C = medium chart (1x1)
# D = medium chart (2x1), E = small chart (1x1)

# Grid dimensions
total_width = 4800
total_height = 2700
title_height = 120
padding = 20

# Calculate cell sizes for 3-column, 3-row grid
grid_width = total_width - 2 * padding
grid_height = total_height - title_height - 2 * padding
col_width = grid_width // 3
row_height = grid_height // 3

# Panel A: Line chart (spans 2 cols, 2 rows) - Revenue & Costs over time
chart_a = pygal.Line(
    width=col_width * 2,
    height=row_height * 2,
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    show_y_guides=True,
    show_x_guides=False,
    x_title="Month",
    y_title="Amount ($K)",
    title="Monthly Revenue vs Costs",
    show_dots=True,
    dots_size=10,
    stroke_style={"width": 5},
    truncate_label=-1,
)
chart_a.x_labels = months
chart_a.add("Revenue", revenue)
chart_a.add("Costs", costs)

# Panel B: Horizontal bar chart (1 col, 1 row) - Category sales
chart_b = pygal.HorizontalBar(
    width=col_width,
    height=row_height,
    style=custom_style,
    show_legend=False,
    show_y_guides=True,
    title="Sales by Category",
    truncate_label=-1,
    print_values=True,
    print_values_position="center",
    value_font_size=16,
)
for cat, val in zip(categories, category_sales, strict=True):
    chart_b.add(cat, val)

# Panel C: Pie chart (1 col, 1 row) - Regional distribution
chart_c = pygal.Pie(
    width=col_width,
    height=row_height,
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    title="Regional Share",
    inner_radius=0.4,
    truncate_label=-1,
)
for region, share in zip(regions, region_shares, strict=True):
    chart_c.add(region, share)

# Panel D: XY scatter chart (2 cols, 1 row) - Marketing vs Sales
chart_d = pygal.XY(
    width=col_width * 2,
    height=row_height,
    style=custom_style,
    show_legend=False,
    show_y_guides=True,
    x_title="Marketing Spend ($K)",
    y_title="Sales ($K)",
    title="Marketing ROI Correlation",
    stroke=False,
    dots_size=12,
    truncate_label=-1,
)
# Convert to list of tuples for XY chart
scatter_data = [(float(x), float(y)) for x, y in zip(marketing_spend, sales_response, strict=True)]
chart_d.add("Correlation", scatter_data)

# Panel E: Gauge chart (1 col, 1 row) - Target achievement
chart_e = pygal.SolidGauge(
    width=col_width,
    height=row_height,
    style=custom_style,
    show_legend=False,
    title="Target Achievement",
    inner_radius=0.6,
    half_pie=True,
)
chart_e.add("Progress", [{"value": current_target_pct, "max_value": 100}])


# Helper function to render chart to PIL Image
def render_chart_to_image(chart, width, height):
    svg_bytes = chart.render()
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=width, output_height=height)
    return Image.open(BytesIO(png_bytes))


# Render all charts
img_a = render_chart_to_image(chart_a, col_width * 2, row_height * 2)
img_b = render_chart_to_image(chart_b, col_width, row_height)
img_c = render_chart_to_image(chart_c, col_width, row_height)
img_d = render_chart_to_image(chart_d, col_width * 2, row_height)
img_e = render_chart_to_image(chart_e, col_width, row_height)

# Create combined image
combined = Image.new("RGB", (total_width, total_height), "white")

# Place charts according to mosaic pattern: "AAB;AAC;DDE"
# Row 0: A (cols 0-1), B (col 2)
# Row 1: A (cols 0-1), C (col 2)
# Row 2: D (cols 0-1), E (col 2)

x_offset = padding
y_offset = title_height + padding

# Panel A: top-left, spans 2 cols x 2 rows
combined.paste(img_a, (x_offset, y_offset))

# Panel B: top-right, 1 col x 1 row
combined.paste(img_b, (x_offset + col_width * 2, y_offset))

# Panel C: middle-right, 1 col x 1 row
combined.paste(img_c, (x_offset + col_width * 2, y_offset + row_height))

# Panel D: bottom-left, 2 cols x 1 row
combined.paste(img_d, (x_offset, y_offset + row_height * 2))

# Panel E: bottom-right, 1 col x 1 row
combined.paste(img_e, (x_offset + col_width * 2, y_offset + row_height * 2))

# Add main title
draw = ImageDraw.Draw(combined)

try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
except OSError:
    title_font = ImageFont.load_default()

title_text = "subplot-mosaic · pygal · pyplots.ai"
bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = bbox[2] - bbox[0]
title_x = (total_width - title_width) // 2
draw.text((title_x, 30), title_text, fill="#333333", font=title_font)

# Save final image
combined.save("plot.png", dpi=(300, 300))

# Also save as HTML with interactive SVG grid
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>subplot-mosaic · pygal · pyplots.ai</title>
    <style>
        body { font-family: sans-serif; background: white; margin: 20px; }
        h1 { text-align: center; color: #333; font-size: 32px; margin-bottom: 20px; }
        .mosaic {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            grid-template-rows: 1fr 1fr 1fr;
            gap: 10px;
            max-width: 1600px;
            margin: 0 auto;
            height: 900px;
        }
        .panel-a { grid-column: 1 / 3; grid-row: 1 / 3; }
        .panel-b { grid-column: 3; grid-row: 1; }
        .panel-c { grid-column: 3; grid-row: 2; }
        .panel-d { grid-column: 1 / 3; grid-row: 3; }
        .panel-e { grid-column: 3; grid-row: 3; }
        .panel svg { width: 100%; height: 100%; }
    </style>
</head>
<body>
    <h1>subplot-mosaic · pygal · pyplots.ai</h1>
    <div class="mosaic">
"""


def get_svg_content(chart):
    svg = chart.render(is_unicode=True)
    return svg.replace('<?xml version="1.0" encoding="utf-8"?>', "")


html_content += f'        <div class="panel panel-a">{get_svg_content(chart_a)}</div>\n'
html_content += f'        <div class="panel panel-b">{get_svg_content(chart_b)}</div>\n'
html_content += f'        <div class="panel panel-c">{get_svg_content(chart_c)}</div>\n'
html_content += f'        <div class="panel panel-d">{get_svg_content(chart_d)}</div>\n'
html_content += f'        <div class="panel panel-e">{get_svg_content(chart_e)}</div>\n'

html_content += """    </div>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
