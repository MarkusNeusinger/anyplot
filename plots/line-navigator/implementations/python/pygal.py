""" pyplots.ai
line-navigator: Line Chart with Mini Navigator
Library: pygal 3.1.0 | Python 3.13.11
Quality: 86/100 | Created: 2026-01-20
"""

import io

import numpy as np
import pandas as pd
import pygal
from PIL import Image
from pygal.style import Style


# Data - Daily sensor readings over 3 years (1095 points)
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=1095, freq="D")

# Generate realistic sensor data with trend, seasonality, and noise
trend = np.linspace(50, 80, 1095)
seasonal = 15 * np.sin(2 * np.pi * np.arange(1095) / 365)  # Yearly cycle
noise = np.random.normal(0, 5, 1095)
values = trend + seasonal + noise

# Define selected range for the navigator view (middle portion)
selection_start = 400
selection_end = 600

# Create descriptive date range label for selected range
start_date = dates[selection_start].strftime("%b %Y")
end_date = dates[selection_end - 1].strftime("%b %Y")
# Use shorter label to avoid legend truncation
detail_label = f"{start_date} - {end_date}"

# Custom style for pyplots
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#306998", "#FFD43B"),
    title_font_size=56,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=32,
    value_font_size=24,
    stroke_width=3,
    opacity=".8",
    opacity_hover=".9",
)

# Main Chart - Shows selected range in detail
main_chart = pygal.Line(
    width=4800,
    height=2160,
    style=custom_style,
    title="line-navigator \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Date",
    y_title="Sensor Reading (mV)",
    show_x_guides=False,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    truncate_legend=-1,
    x_label_rotation=45,
    truncate_label=-1,
    show_dots=False,
    fill=False,
    stroke_style={"width": 4},
    interpolate="cubic",
    margin=80,
)

# Add selected range data to main chart
selected_values = list(values[selection_start:selection_end])
selected_dates = [dates[i].strftime("%Y-%m-%d") for i in range(selection_start, selection_end)]

# Sample labels for x-axis (show every 25th date to reduce overlap)
main_x_labels = [selected_dates[i] if i % 25 == 0 else "" for i in range(len(selected_dates))]
main_chart.x_labels = main_x_labels
main_chart.add(detail_label, selected_values)

# Navigator Chart - Shows full data extent with selection indicator
nav_style = Style(
    background="#f0f0f0",
    plot_background="#f0f0f0",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#8AAEC7", "#E67E22"),  # Lighter blue for full data, orange for selection
    title_font_size=44,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=36,
    value_font_size=28,
    stroke_width=2,
    opacity=".7",
)

nav_chart = pygal.Line(
    width=4800,
    height=540,
    style=nav_style,
    title="Navigator - Full Data Range (2022-2024)",
    x_title="",
    y_title="",
    show_x_guides=False,
    show_y_guides=False,
    show_y_labels=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=20,
    truncate_legend=-1,
    x_label_rotation=0,
    show_dots=False,
    fill=True,
    stroke_style={"width": 2},
    margin=50,
)

# Add full data to navigator
nav_x_labels = [dates[i].strftime("%Y-%m") if i % 182 == 0 else "" for i in range(len(dates))]
nav_chart.x_labels = nav_x_labels
nav_chart.add("Full Dataset (2022-2024)", list(values))

# Create selection indicator as a separate series (highlighted area)
selection_indicator = [None] * len(values)
for i in range(selection_start, selection_end):
    selection_indicator[i] = values[i]
nav_chart.add(f"Selected: {start_date} - {end_date}", selection_indicator)

# Render charts to PNG bytes in memory (no temp files)
main_png_bytes = main_chart.render_to_png()
nav_png_bytes = nav_chart.render_to_png()

# Combine both charts into single image using PIL
main_img = Image.open(io.BytesIO(main_png_bytes))
nav_img = Image.open(io.BytesIO(nav_png_bytes))

# Create combined image without gap between charts
combined_height = main_img.height + nav_img.height
combined = Image.new("RGB", (main_img.width, combined_height), "white")
combined.paste(main_img, (0, 0))
combined.paste(nav_img, (0, main_img.height))

# Save final combined plot
combined.save("plot.png")

# Also save HTML version
main_chart_html = pygal.Line(
    width=1200,
    height=540,
    style=custom_style,
    title="line-navigator \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Date",
    y_title="Sensor Reading (mV)",
    show_x_guides=False,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=True,
    x_label_rotation=45,
    truncate_label=-1,
    show_dots=False,
    fill=False,
    interpolate="cubic",
)
main_chart_html.x_labels = main_x_labels
main_chart_html.add(detail_label, selected_values)

nav_chart_html = pygal.Line(
    width=1200,
    height=150,
    style=nav_style,
    title="Navigator - Full Data Range",
    show_legend=True,
    legend_at_bottom=True,
    show_dots=False,
    fill=True,
)
nav_chart_html.x_labels = nav_x_labels
nav_chart_html.add("Full Dataset (2022-2024)", list(values))
nav_chart_html.add(f"Selected: {start_date} - {end_date}", selection_indicator)

# Create HTML with both charts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>line-navigator - pygal - pyplots.ai</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #fff; }}
        .chart-container {{ max-width: 1200px; margin: 0 auto; }}
        .main-chart {{ margin-bottom: 0; }}
        .nav-chart {{ background: #f0f0f0; }}
    </style>
</head>
<body>
    <div class="chart-container">
        <div class="main-chart">
            {main_chart_html.render(is_unicode=True)}
        </div>
        <div class="nav-chart">
            {nav_chart_html.render(is_unicode=True)}
        </div>
    </div>
</body>
</html>
"""

with open("plot.html", "w") as f:
    f.write(html_content)
