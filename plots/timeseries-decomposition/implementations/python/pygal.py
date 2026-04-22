""" pyplots.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

from io import BytesIO

import cairosvg
import numpy as np
import pandas as pd
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style
from statsmodels.tsa.seasonal import seasonal_decompose


# Data - Monthly CO2 measurements with clear trend and seasonality
np.random.seed(42)
dates = pd.date_range("2020-01-01", periods=72, freq="ME")  # 6 years monthly

# Create realistic CO2-like data with trend, seasonality, and noise
trend = np.linspace(410, 430, 72)  # Rising trend (ppm)
seasonal_pattern = 3 * np.sin(2 * np.pi * np.arange(72) / 12)  # Annual cycle
noise = np.random.normal(0, 0.5, 72)
values = trend + seasonal_pattern + noise

# Create time series and decompose
ts = pd.Series(values, index=dates)
decomposition = seasonal_decompose(ts, model="additive", period=12)

# Extract components
observed = decomposition.observed.values
trend_component = decomposition.trend.values
seasonal_component = decomposition.seasonal.values
residual_component = decomposition.resid.values

# Create x-axis labels (show every 6 months for readability)
x_labels = [d.strftime("%Y-%m") if i % 6 == 0 else "" for i, d in enumerate(dates)]

# Define components with their data, titles, colors, y-ranges, and y-axis labels
components = [
    ("Original Series (CO2 ppm)", observed, "#306998", (405, 437), "CO₂ (ppm)"),
    ("Trend Component", trend_component, "#FFD43B", (405, 435), "Trend (ppm)"),
    ("Seasonal Component", seasonal_component, "#44AA44", (-5, 5), "Seasonal (ppm)"),
    ("Residual Component", residual_component, "#E74C3C", (-3, 3), "Residual (ppm)"),
]

# Target: 4800 x 2700 px total (4 vertically stacked charts)
# Reserve left margin for y-axis labels drawn manually
title_height = 160
y_label_width = 220
chart_width = 4800 - y_label_width
chart_height = (2700 - title_height) // 4

charts = []
y_labels_list = []
for idx, (label, data, color, y_range, y_label) in enumerate(components):
    # Replace NaN with None for pygal
    clean_data = [None if np.isnan(v) else float(v) for v in data]
    y_labels_list.append(y_label)

    # Create custom style with component color and larger fonts for 4800x2700
    component_style = Style(
        background="white",
        plot_background="#fafafa",
        foreground="#333333",
        foreground_strong="#333333",
        foreground_subtle="#666666",
        colors=(color,),
        font_family="sans-serif",
        title_font_size=60,
        label_font_size=48,
        major_label_font_size=44,
        legend_font_size=44,
        value_font_size=36,
        stroke_width=5,
    )

    chart = pygal.Line(
        width=chart_width,
        height=chart_height,
        style=component_style,
        title=label,
        x_title="Date" if idx == 3 else "",
        show_legend=False,
        show_y_guides=True,
        show_x_guides=True,
        show_dots=False,
        stroke_style={"width": 5},
        range=y_range,
        truncate_label=-1,
        x_label_rotation=35 if idx == 3 else 0,
        margin_left=20,
        y_labels_major_count=6,
        show_minor_y_labels=False,
    )

    # Only show x-labels on the bottom chart
    if idx == 3:
        chart.x_labels = x_labels
    else:
        chart.x_labels = [""] * len(dates)

    chart.add(label, clean_data)
    charts.append(chart)

# Render each chart to PNG and combine them vertically
images = []
for chart in charts:
    svg_bytes = chart.render()
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=chart_width, output_height=chart_height)
    img = Image.open(BytesIO(png_bytes))
    images.append(img)

# Create combined image (4800 x 2700)
total_width = 4800
total_height = 2700

combined = Image.new("RGB", (total_width, total_height), "white")

# Load fonts with increased sizes for better readability
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 88)
    y_label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
except OSError:
    title_font = ImageFont.load_default()
    y_label_font = ImageFont.load_default()

# Add main title
draw = ImageDraw.Draw(combined)
title_text = "timeseries-decomposition · pygal · pyplots.ai"
bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = bbox[2] - bbox[0]
title_x = (total_width - title_width) // 2
draw.text((title_x, 40), title_text, fill="#333333", font=title_font)

# Paste charts vertically with space for y-axis labels
for idx, img in enumerate(images):
    y_position = title_height + idx * chart_height
    combined.paste(img, (y_label_width, y_position))

    # Draw rotated y-axis label on the left side
    y_label_text = y_labels_list[idx]
    label_img = Image.new("RGBA", (500, 120), (255, 255, 255, 0))
    label_draw = ImageDraw.Draw(label_img)
    label_draw.text((0, 0), y_label_text, fill="#333333", font=y_label_font)

    # Crop to text bounds and rotate
    label_bbox = label_img.getbbox()
    if label_bbox:
        label_img = label_img.crop(label_bbox)
    label_img = label_img.rotate(90, expand=True)

    # Center the rotated label vertically in the chart area
    label_x = (y_label_width - label_img.width) // 2
    label_y = y_position + (chart_height - label_img.height) // 2
    combined.paste(label_img, (label_x, label_y), label_img)

# Save final image
combined.save("plot.png", dpi=(300, 300))

# Also save as HTML (interactive SVG)
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>timeseries-decomposition · pygal · pyplots.ai</title>
    <style>
        body { font-family: sans-serif; background: white; margin: 20px; }
        h1 { text-align: center; color: #333; font-size: 28px; margin-bottom: 20px; }
        .charts { display: flex; flex-direction: column; max-width: 1200px; margin: 0 auto; }
        .chart { width: 100%; margin-bottom: 10px; }
        .chart svg { width: 100%; height: auto; }
    </style>
</head>
<body>
    <h1>timeseries-decomposition · pygal · pyplots.ai</h1>
    <div class="charts">
"""

for chart in charts:
    svg_data = chart.render(is_unicode=True)
    svg_data = svg_data.replace('<?xml version="1.0" encoding="utf-8"?>', "")
    html_content += f'        <div class="chart">{svg_data}</div>\n'

html_content += """    </div>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
