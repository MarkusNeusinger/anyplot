""" anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-15
"""

import io
import json
import os
import sys


# Remove current dir from path to avoid shadowing the pygal library
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Theme setup
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series is brand green)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data: Simulated country development metrics over years
np.random.seed(42)

# 10 countries (different from altair's 12) tracked over annual years 2000-2020 (different sampling)
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
]
years = list(range(2000, 2021, 5))  # 5-year intervals: different from altair's 2000/2007/2014/2021

# Base values for each country
base_gdp = np.array([5, 8, 12, 15, 20, 25, 3, 10, 18, 30])
base_life = np.array([55, 60, 65, 70, 72, 75, 50, 62, 68, 78])
population = np.array([50, 80, 120, 45, 200, 30, 150, 90, 60, 25])

# Regions for color coding (3 categories)
regions = ["Asia", "Europe", "Asia", "Europe", "Africa", "Africa", "Americas", "Europe", "Africa", "Asia"]

# Generate data for each year with different growth formula (0.20 instead of 0.15)
data_by_year = {}
pop_min, pop_max = population.min(), population.max()

for year_idx, year in enumerate(years):
    data_by_year[year] = {"Asia": [], "Europe": [], "Africa": [], "Americas": []}
    for i, country in enumerate(countries):
        growth_factor = 1 + year_idx * 0.20 + np.random.uniform(-0.05, 0.1)  # Different coefficient
        life_improvement = year_idx * 2.5 + np.random.uniform(-1, 2)

        gdp = base_gdp[i] * growth_factor
        life_exp = min(85, base_life[i] + life_improvement)
        pop = population[i] * (1 + year_idx * 0.02)

        # Calculate dot size based on population (scaled 12-48 for better visibility)
        pop_normalized = (population[i] - pop_min) / (pop_max - pop_min)
        dot_size = 12 + pop_normalized * 36

        region = regions[i]
        data_by_year[year][region].append(
            {
                "value": (round(gdp, 1), round(life_exp, 1)),
                "node": {"r": dot_size},
                "label": f"{country}: GDP ${round(gdp, 1)}k, Life {round(life_exp, 1)}y, Pop {round(pop, 0)}M",
            }
        )

# Custom style with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=18,
    value_font_size=16,
    tooltip_font_size=16,
    stroke_width=3,
)

# Region-color mapping using Okabe-Ito (only 4 colors for 4 regions)
region_colors = {
    "Asia": IMPRINT[0],  # #009E73 - brand green
    "Europe": IMPRINT[1],  # #C475FD - vermillion
    "Africa": IMPRINT[2],  # #4467A3 - blue
    "Americas": IMPRINT[3],  # #BD8233 - reddish purple
}

# Create interactive HTML with slider control
html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>scatter-animated-controls · pygal · anyplot.ai</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {page_bg};
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
            color: {ink};
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            font-size: 18px;
            color: {ink_soft};
            margin-bottom: 20px;
        }}
        .slider-container {{
            background: {elevated_bg};
            border-radius: 12px;
            padding: 30px 40px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .slider-label {{
            font-size: 24px;
            font-weight: 600;
            color: {ink};
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .year-display {{
            font-size: 48px;
            font-weight: 700;
            color: #009E73;
            background: {page_bg};
            padding: 10px 30px;
            border-radius: 8px;
            border: 3px solid #009E73;
        }}
        .slider-wrapper {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .year-label {{
            font-size: 18px;
            font-weight: 500;
            color: {ink_soft};
            min-width: 50px;
        }}
        input[type="range"] {{
            flex: 1;
            height: 12px;
            -webkit-appearance: none;
            appearance: none;
            background: {ink_muted};
            border-radius: 6px;
            outline: none;
        }}
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 32px;
            height: 32px;
            background: #009E73;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }}
        input[type="range"]::-moz-range-thumb {{
            width: 32px;
            height: 32px;
            background: #009E73;
            border-radius: 50%;
            cursor: pointer;
            border: none;
        }}
        .chart-container {{
            position: relative;
            width: 100%;
            background: {page_bg};
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
            background: {elevated_bg};
            border-radius: 8px;
            display: flex;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 18px;
            color: {ink};
        }}
        .legend-color {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">scatter-animated-controls · pygal · anyplot.ai</div>
        <div class="subtitle">Regional Development Metrics Over Time (Use Slider to Animate)</div>
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
                <div class="legend-color" style="background: #009E73;"></div>
                <span>Asia</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #C475FD;"></div>
                <span>Europe</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #4467A3;"></div>
                <span>Africa</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #BD8233;"></div>
                <span>Americas</span>
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
        dots_size=20,
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
    for region in ["Asia", "Europe", "Africa", "Americas"]:
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
    page_bg=PAGE_BG,
    elevated_bg=ELEVATED_BG,
    ink=INK,
    ink_soft=INK_SOFT,
    ink_muted=INK_MUTED,
)

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(final_html)

# Create PNG showing 2020 (most recent) as the static preview
png_chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-animated-controls · pygal · anyplot.ai",
    x_title="GDP per Capita (thousands USD)",
    y_title="Life Expectancy (years)",
    show_x_guides=True,
    show_y_guides=True,
    dots_size=20,
    stroke=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    margin=120,
    margin_top=180,
    margin_bottom=200,
    truncate_legend=-1,
    range=(45, 90),
    xrange=(0, 50),
    explicit_size=True,
)

# Add data for 2020 (latest year) for PNG preview
for region in ["Asia", "Europe", "Africa", "Americas"]:
    points = data_by_year[2020][region]
    png_chart.add(region, points)

# Render PNG and add year watermark
svg_data = png_chart.render()
png_bytes = cairosvg.svg2png(bytestring=svg_data, output_width=4800, output_height=2700)

# Open as PIL image and add year watermark
img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
draw = ImageDraw.Draw(img)

# Large year watermark in center-right of plot area
year_text = "2020"
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 400)
except OSError:
    font = ImageFont.load_default()

# Position: center-right area, semi-transparent
text_bbox = draw.textbbox((0, 0), year_text, font=font)
text_width = text_bbox[2] - text_bbox[0]
text_height = text_bbox[3] - text_bbox[1]
x_pos = 4800 - text_width - 300
y_pos = (2700 - text_height) // 2 - 100

# Draw semi-transparent year watermark (theme-adaptive)
watermark = Image.new("RGBA", img.size, (255, 255, 255, 0))
watermark_draw = ImageDraw.Draw(watermark)
if THEME == "light":
    watermark_draw.text((x_pos, y_pos), year_text, font=font, fill=(0, 158, 115, 40))
else:
    watermark_draw.text((x_pos, y_pos), year_text, font=font, fill=(240, 239, 232, 40))
img = Image.alpha_composite(img, watermark)

# Save final PNG
img.convert("RGB").save(f"plot-{THEME}.png")
