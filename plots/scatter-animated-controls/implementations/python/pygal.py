""" pyplots.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import io
import json

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data: Simulated country development metrics over years
np.random.seed(42)

# 12 countries tracked over 4 key time points
countries = [
    "Country A",
    "Country B",
    "Country C",
    "Country D",
    "Country E",
    "Country F",
    "Country G",
    "Country H",
    "Country I",
    "Country J",
    "Country K",
    "Country L",
]
years = [2000, 2007, 2014, 2021]

# Base values for each country
base_gdp = np.array([5, 8, 12, 15, 20, 25, 3, 10, 18, 30, 6, 22])
base_life = np.array([55, 60, 65, 70, 72, 75, 50, 62, 68, 78, 58, 74])
population = np.array([50, 80, 120, 45, 200, 30, 150, 90, 60, 25, 180, 40])

# Regions for color coding
regions = [
    "Region 1",
    "Region 2",
    "Region 1",
    "Region 2",
    "Region 3",
    "Region 3",
    "Region 1",
    "Region 2",
    "Region 3",
    "Region 3",
    "Region 1",
    "Region 2",
]

# Generate data for each year with population-based marker sizes
data_by_year = {}
# Scale population to reasonable dot sizes (min 8, max 40)
pop_min, pop_max = population.min(), population.max()

for year_idx, year in enumerate(years):
    data_by_year[year] = {"Region 1": [], "Region 2": [], "Region 3": []}
    for i, country in enumerate(countries):
        growth_factor = 1 + year_idx * 0.15 + np.random.uniform(-0.05, 0.1)
        life_improvement = year_idx * 2.5 + np.random.uniform(-1, 2)

        gdp = base_gdp[i] * growth_factor
        life_exp = min(85, base_life[i] + life_improvement)
        pop = population[i] * (1 + year_idx * 0.02)

        # Calculate dot size based on population (scaled 8-40)
        pop_normalized = (population[i] - pop_min) / (pop_max - pop_min)
        dot_size = 8 + pop_normalized * 32

        region = regions[i]
        data_by_year[year][region].append(
            {
                "value": (round(gdp, 1), round(life_exp, 1)),
                "node": {"r": dot_size},  # pygal node radius for size encoding
                "label": f"{country}: GDP ${round(gdp, 1)}k, Life {round(life_exp, 1)}y, Pop {round(pop, 0)}M",
            }
        )

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#6B8E23"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=48,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=2,
)

# Create interactive HTML with slider control (similar to slider-control-basic)
html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>scatter-animated-controls · pygal · pyplots.ai</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: white;
            margin: 0;
            padding: 40px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{
            width: 100%;
            max-width: 1600px;
        }}
        .title {{
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            font-size: 18px;
            color: #666;
            margin-bottom: 20px;
        }}
        .slider-container {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 30px 40px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .slider-label {{
            font-size: 24px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .year-display {{
            font-size: 48px;
            font-weight: 700;
            color: #306998;
            background: white;
            padding: 10px 30px;
            border-radius: 8px;
            border: 3px solid #306998;
        }}
        .slider-wrapper {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .year-label {{
            font-size: 18px;
            font-weight: 500;
            color: #666;
            min-width: 50px;
        }}
        input[type="range"] {{
            flex: 1;
            height: 12px;
            -webkit-appearance: none;
            appearance: none;
            background: #ddd;
            border-radius: 6px;
            outline: none;
        }}
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 32px;
            height: 32px;
            background: #306998;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }}
        input[type="range"]::-moz-range-thumb {{
            width: 32px;
            height: 32px;
            background: #306998;
            border-radius: 50%;
            cursor: pointer;
            border: none;
        }}
        .chart-container {{
            position: relative;
            width: 100%;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .chart {{
            display: none;
            width: 100%;
        }}
        .chart.active {{
            display: block;
        }}
        .chart svg {{
            width: 100%;
            height: auto;
        }}
        .legend-box {{
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: flex;
            justify-content: center;
            gap: 40px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 18px;
        }}
        .legend-color {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">scatter-animated-controls · pygal · pyplots.ai</div>
        <div class="subtitle">Country Development Metrics Over Time (Use Slider to Animate)</div>
        <div class="slider-container">
            <div class="slider-label">
                <span>Select Year</span>
                <span class="year-display" id="yearDisplay">{initial_year}</span>
            </div>
            <div class="slider-wrapper">
                <span class="year-label">{min_year}</span>
                <input type="range" id="yearSlider" min="0" max="{max_index}" value="0" step="1">
                <span class="year-label">{max_year}</span>
            </div>
        </div>
        <div class="chart-container">
            {charts_html}
        </div>
        <div class="legend-box">
            <div class="legend-item">
                <div class="legend-color" style="background: #306998;"></div>
                <span>Region 1</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FFD43B;"></div>
                <span>Region 2</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #6B8E23;"></div>
                <span>Region 3</span>
            </div>
        </div>
    </div>
    <script>
        const years = {years_json};
        const slider = document.getElementById('yearSlider');
        const yearDisplay = document.getElementById('yearDisplay');
        const charts = document.querySelectorAll('.chart');

        function updateChart() {{
            const index = parseInt(slider.value);
            const year = years[index];
            yearDisplay.textContent = year;
            charts.forEach((chart, i) => {{
                chart.classList.toggle('active', i === index);
            }});
        }}

        slider.addEventListener('input', updateChart);
        updateChart();
    </script>
</body>
</html>
"""

# Generate SVG for each year for HTML slider
charts_html_parts = []

for idx, year in enumerate(years):
    year_chart = pygal.XY(
        width=4800,
        height=2700,
        style=custom_style,
        title=f"Year {year}",
        x_title="GDP per Capita (thousands USD)",
        y_title="Life Expectancy (years)",
        show_x_guides=True,
        show_y_guides=True,
        dots_size=18,
        stroke=False,
        show_legend=False,
        margin=120,
        margin_top=180,
        margin_bottom=150,
        truncate_legend=-1,
        range=(45, 90),
        xrange=(0, 50),
    )

    # Add data series by region
    for region in ["Region 1", "Region 2", "Region 3"]:
        points = data_by_year[year][region]
        year_chart.add(region, points)

    svg_content = year_chart.render().decode("utf-8")
    active_class = "active" if idx == 0 else ""
    charts_html_parts.append(f'<div class="chart {active_class}" data-year="{year}">{svg_content}</div>')

# Combine into final HTML
final_html = html_template.format(
    initial_year=years[0],
    min_year=years[0],
    max_year=years[-1],
    max_index=len(years) - 1,
    charts_html="\n".join(charts_html_parts),
    years_json=json.dumps(years),
)

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(final_html)

# Create PNG showing year 2021 (most recent) as the static preview
# Custom style with year watermark for PNG
png_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#6B8E23"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=48,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=2,
)

png_chart = pygal.XY(
    width=4800,
    height=2700,
    style=png_style,
    title="scatter-animated-controls · pygal · pyplots.ai",
    x_title="GDP per Capita (thousands USD)",
    y_title="Life Expectancy (years)",
    show_x_guides=True,
    show_y_guides=True,
    dots_size=18,
    stroke=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    margin=120,
    margin_top=180,
    margin_bottom=200,
    truncate_legend=-1,
    range=(45, 90),
    xrange=(0, 50),
    explicit_size=True,
)

# Add data for 2021 (latest year) for PNG preview
for region in ["Region 1", "Region 2", "Region 3"]:
    points = data_by_year[2021][region]
    png_chart.add(region, points)

# Render PNG and add year watermark
# Get SVG and convert to PNG
svg_data = png_chart.render()
png_bytes = cairosvg.svg2png(bytestring=svg_data, output_width=4800, output_height=2700)

# Open as PIL image and add year watermark
img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
draw = ImageDraw.Draw(img)

# Large year watermark in center-right of plot area
year_text = "2021"
# Use default font at large size (no external font file needed)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 400)
except OSError:
    font = ImageFont.load_default()

# Position: center-right area, semi-transparent
text_bbox = draw.textbbox((0, 0), year_text, font=font)
text_width = text_bbox[2] - text_bbox[0]
text_height = text_bbox[3] - text_bbox[1]
x_pos = 4800 - text_width - 300  # Right side with padding
y_pos = (2700 - text_height) // 2 - 100  # Vertically centered, slightly up

# Draw semi-transparent year watermark
watermark = Image.new("RGBA", img.size, (255, 255, 255, 0))
watermark_draw = ImageDraw.Draw(watermark)
watermark_draw.text((x_pos, y_pos), year_text, font=font, fill=(48, 105, 152, 40))  # Light blue, very transparent
img = Image.alpha_composite(img, watermark)

# Save final PNG
img.convert("RGB").save("plot.png")
