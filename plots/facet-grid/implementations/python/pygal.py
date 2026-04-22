""" pyplots.ai
facet-grid: Faceted Grid Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

from io import BytesIO

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data - Plant growth experiment across different soil types and light conditions
np.random.seed(42)

# Create faceted data: 2 row categories (soil type) x 3 column categories (light level)
row_cats = ["Sandy Soil", "Clay Soil"]
col_cats = ["Low Light", "Medium Light", "High Light"]

# Generate plant growth data (height vs days) for each condition
data = {}
base_growth_rates = {
    ("Sandy Soil", "Low Light"): 0.4,
    ("Sandy Soil", "Medium Light"): 0.8,
    ("Sandy Soil", "High Light"): 1.0,
    ("Clay Soil", "Low Light"): 0.5,
    ("Clay Soil", "Medium Light"): 1.2,
    ("Clay Soil", "High Light"): 0.9,
}

# Days as x-axis (shared across all facets)
days = [0, 5, 10, 15, 20, 25, 30]

for row_cat in row_cats:
    for col_cat in col_cats:
        rate = base_growth_rates[(row_cat, col_cat)]
        # Generate growth curve with some variation
        heights = [d * rate + np.random.normal(0, 1) for d in days]
        heights = [max(0, h) for h in heights]  # No negative heights
        data[(row_cat, col_cat)] = heights

# Custom style for pyplots
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4CAF50", "#FF5722"),
    font_family="sans-serif",
    title_font_size=40,
    label_font_size=28,
    major_label_font_size=24,
    legend_font_size=28,
    value_font_size=20,
    stroke_width=4,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create individual charts for each facet
# Target: 4800 x 2700 px total grid (2 rows x 3 cols)
cell_width = 1500
cell_height = 1250

charts = []
for row_idx, row_cat in enumerate(row_cats):
    row_charts = []
    for col_idx, col_cat in enumerate(col_cats):
        # Create chart for this facet
        chart = pygal.Line(
            width=cell_width,
            height=cell_height,
            style=custom_style,
            show_legend=False,
            show_y_guides=True,
            show_x_guides=False,
            x_title="Days" if row_idx == len(row_cats) - 1 else "",
            y_title="Height (cm)" if col_idx == 0 else "",
            title=f"{col_cat}" if row_idx == 0 else "",
            show_dots=True,
            dots_size=8,
            stroke_style={"width": 4},
            range=(0, 35),
            truncate_label=-1,
        )

        # Add x-axis labels (days)
        chart.x_labels = [str(d) for d in days]

        # Add data series
        chart.add(row_cat, data[(row_cat, col_cat)])

        row_charts.append(chart)
    charts.append(row_charts)

# Render each chart to PNG and combine them
images = []
for _row_idx, row_charts in enumerate(charts):
    row_images = []
    for chart in row_charts:
        # Render to SVG bytes, then convert to PNG
        svg_bytes = chart.render()
        png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=cell_width, output_height=cell_height)
        img = Image.open(BytesIO(png_bytes))
        row_images.append(img)
    images.append(row_images)

# Create combined image (4800 x 2700 with space for title and row labels)
title_height = 150
row_label_width = 300
total_width = 4800
total_height = 2700

combined = Image.new("RGB", (total_width, total_height), "white")

# Calculate grid positioning
grid_width = total_width - row_label_width
grid_height = total_height - title_height
actual_cell_width = grid_width // len(col_cats)
actual_cell_height = grid_height // len(row_cats)

# Paste charts into grid
for row_idx, row_images in enumerate(images):
    for col_idx, img in enumerate(row_images):
        # Resize to fit cell
        img_resized = img.resize((actual_cell_width, actual_cell_height), Image.LANCZOS)
        x = row_label_width + col_idx * actual_cell_width
        y = title_height + row_idx * actual_cell_height
        combined.paste(img_resized, (x, y))

# Add main title and row labels using PIL
draw = ImageDraw.Draw(combined)

# Try to use a system font, fallback to default
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
except OSError:
    title_font = ImageFont.load_default()
    label_font = ImageFont.load_default()

# Draw main title
title_text = "facet-grid · pygal · pyplots.ai"
bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = bbox[2] - bbox[0]
title_x = (total_width - title_width) // 2
draw.text((title_x, 40), title_text, fill="#333333", font=title_font)

# Draw row labels (rotated 90 degrees)
for row_idx, row_cat in enumerate(row_cats):
    # Create a temporary image for rotated text
    temp_img = Image.new("RGBA", (400, 80), (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    temp_draw.text((10, 10), row_cat, fill="#333333", font=label_font)
    temp_img = temp_img.rotate(90, expand=True)

    # Position the rotated label
    label_y = title_height + row_idx * actual_cell_height + actual_cell_height // 2 - temp_img.height // 2
    combined.paste(temp_img, (50, label_y), temp_img)

# Save final image
combined.save("plot.png", dpi=(300, 300))

# Also save as HTML (interactive SVG grid)
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>facet-grid · pygal · pyplots.ai</title>
    <style>
        body { font-family: sans-serif; background: white; margin: 20px; }
        h1 { text-align: center; color: #333; font-size: 28px; }
        .grid { display: grid; grid-template-columns: 100px repeat(3, 1fr); gap: 10px; max-width: 1600px; margin: 0 auto; }
        .row-label { writing-mode: vertical-rl; text-orientation: mixed; transform: rotate(180deg);
                     display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; color: #333; }
        .col-header { text-align: center; font-size: 18px; font-weight: bold; color: #333; padding: 10px; }
        .chart { width: 100%; }
        .empty { }
    </style>
</head>
<body>
    <h1>facet-grid · pygal · pyplots.ai</h1>
    <div class="grid">
        <div class="empty"></div>
"""

# Add column headers
for col_cat in col_cats:
    html_content += f'        <div class="col-header">{col_cat}</div>\n'

# Add charts with row labels
for row_idx, row_cat in enumerate(row_cats):
    html_content += f'        <div class="row-label">{row_cat}</div>\n'
    for col_idx, _col_cat in enumerate(col_cats):
        chart = charts[row_idx][col_idx]
        svg_data = chart.render(is_unicode=True)
        # Remove XML declaration if present
        svg_data = svg_data.replace('<?xml version="1.0" encoding="utf-8"?>', "")
        html_content += f'        <div class="chart">{svg_data}</div>\n'

html_content += """    </div>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
