""" pyplots.ai
bar-race-animated: Animated Bar Chart Race
Library: pygal 3.1.0 | Python 3.13.11
Quality: 87/100 | Created: 2026-01-11
"""

from io import BytesIO

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data - Technology companies market cap evolution (2019-2024)
np.random.seed(42)

companies = ["Apple", "Microsoft", "Alphabet", "Amazon", "Meta", "Tesla", "NVIDIA", "Samsung"]
years = [2019, 2020, 2021, 2022, 2023, 2024]

# Generate realistic market cap data (in billions USD)
base_values = {
    "Apple": 1200,
    "Microsoft": 900,
    "Alphabet": 800,
    "Amazon": 700,
    "Meta": 400,
    "Tesla": 100,
    "NVIDIA": 150,
    "Samsung": 300,
}

growth_rates = {
    "Apple": [1.0, 1.3, 1.8, 1.5, 2.0, 2.8],
    "Microsoft": [1.0, 1.4, 2.0, 1.6, 2.2, 2.9],
    "Alphabet": [1.0, 1.2, 1.6, 1.2, 1.5, 2.0],
    "Amazon": [1.0, 1.5, 1.6, 1.0, 1.3, 1.8],
    "Meta": [1.0, 1.5, 1.8, 0.6, 1.2, 1.8],
    "Tesla": [1.0, 5.0, 8.0, 4.0, 6.0, 7.0],
    "NVIDIA": [1.0, 2.0, 4.0, 2.5, 6.0, 14.0],
    "Samsung": [1.0, 1.1, 1.3, 0.9, 1.1, 1.4],
}

# Calculate market cap for each year
data = {}
for company in companies:
    data[company] = [int(base_values[company] * growth_rates[company][i]) for i in range(len(years))]

# Colors for consistent entity tracking - distinct hues to avoid confusion
company_colors = {
    "Apple": "#306998",  # Python Blue (primary)
    "Microsoft": "#FFD43B",  # Python Yellow (primary)
    "Alphabet": "#34A853",  # Google Green (distinct from blues)
    "Amazon": "#FF9900",  # Amazon Orange
    "Meta": "#E040FB",  # Purple (distinct from blue tones)
    "Tesla": "#CC0000",  # Tesla Red
    "NVIDIA": "#76B900",  # NVIDIA Green
    "Samsung": "#795548",  # Brown (distinct from all other colors)
}

# Create individual charts for each year
charts = []
for year_idx, year in enumerate(years):
    # Get values for this year and sort by value (descending)
    year_data = [(company, data[company][year_idx]) for company in companies]
    year_data.sort(key=lambda x: x[1], reverse=True)

    # Create style for this chart
    year_style = Style(
        background="white",
        plot_background="white",
        foreground="#333333",
        foreground_strong="#333333",
        foreground_subtle="#666666",
        title_font_size=52,
        label_font_size=36,
        major_label_font_size=32,
        legend_font_size=32,
        value_font_size=32,
        tooltip_font_size=28,
    )

    chart = pygal.HorizontalBar(
        width=1500,
        height=950,
        style=year_style,
        show_legend=False,  # Disable legend on individual charts - use global legend only
        title=str(year),
        x_title="Market Cap ($B)",
        print_values=True,
        print_values_position="middle",
        value_formatter=lambda x: f"${x:,.0f}B",
        margin=40,
        spacing=12,
        truncate_label=-1,
        show_x_labels=True,
        x_label_rotation=0,
        show_minor_x_labels=False,
    )

    # Set x_labels for company names (shown on y-axis for horizontal bar)
    chart.x_labels = [company for company, _ in year_data]

    # Add each company as a separate series with its value at the correct position
    # Use None placeholders for other positions to avoid stacking
    num_companies = len(year_data)
    for idx, (company, value) in enumerate(year_data):
        values = [None] * num_companies
        values[idx] = {"value": value, "color": company_colors[company]}
        chart.add(company, values)

    charts.append(chart)

# Render each chart to PNG and combine into grid
chart_images = []
for chart in charts:
    svg_data = chart.render()
    png_data = cairosvg.svg2png(bytestring=svg_data, output_width=1500, output_height=950)
    img = Image.open(BytesIO(png_data))
    chart_images.append(img)

# Create 3x2 grid layout (4800 x 2700 final size)
grid_width = 4800
grid_height = 2700
title_height = 160
legend_height = 120
content_height = grid_height - title_height - legend_height
cell_width = grid_width // 3
cell_height = content_height // 2

combined = Image.new("RGB", (grid_width, grid_height), "white")
draw = ImageDraw.Draw(combined)

# Load fonts
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    legend_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
except OSError:
    title_font = ImageFont.load_default()
    legend_font = ImageFont.load_default()

# Add main title
title_text = "bar-race-animated · pygal · pyplots.ai"
bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = bbox[2] - bbox[0]
draw.text(((grid_width - title_width) // 2, 40), title_text, fill="#333333", font=title_font)

# Paste charts into grid
positions = [
    (0, 0),
    (1, 0),
    (2, 0),  # Top row: 2019, 2020, 2021
    (0, 1),
    (1, 1),
    (2, 1),  # Bottom row: 2022, 2023, 2024
]

for idx, (col, row) in enumerate(positions):
    if idx < len(chart_images):
        img = chart_images[idx].resize((cell_width, cell_height), Image.Resampling.LANCZOS)
        x = col * cell_width
        y = title_height + row * cell_height
        combined.paste(img, (x, y))

# Add legend at bottom - larger boxes and centered layout
legend_y = grid_height - legend_height + 20
box_size = 40
spacing_between = grid_width // len(companies)
legend_x_start = spacing_between // 2 - 80  # Center the legend items

for i, company in enumerate(companies):
    x_pos = legend_x_start + i * spacing_between
    # Draw color box
    draw.rectangle([x_pos, legend_y, x_pos + box_size, legend_y + box_size], fill=company_colors[company])
    # Draw company name
    draw.text((x_pos + box_size + 12, legend_y - 2), company, fill="#333333", font=legend_font)

# Save as PNG
combined.save("plot.png", dpi=(300, 300))

# Save as HTML (interactive SVG version showing 2024 final state)
html_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    title_font_size=36,
    label_font_size=20,
    major_label_font_size=18,
    legend_font_size=18,
    value_font_size=16,
    tooltip_font_size=16,
)

html_chart = pygal.HorizontalBar(
    width=1200,
    height=800,
    style=html_style,
    show_legend=True,
    title="Tech Company Market Cap 2024 · bar-race-animated · pygal · pyplots.ai",
    x_title="Market Cap (Billion USD)",
    print_values=True,
    value_formatter=lambda x: f"${x:,.0f}B",
)

final_data = [(company, data[company][-1]) for company in companies]
final_data.sort(key=lambda x: x[1], reverse=True)

for company, value in final_data:
    html_chart.add(company, [{"value": value, "color": company_colors[company]}])

html_chart.render_to_file("plot.html")
