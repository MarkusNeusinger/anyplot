""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: pygal 3.1.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-13
"""

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data — Life expectancy vs GDP per capita for a fictional country (1990-2023)
np.random.seed(42)
years = list(range(1990, 2024))
n_years = len(years)

# GDP per capita starts ~8000, grows with occasional dips (recessions)
gdp_base = 8000
gdp_growth = np.cumsum(np.random.normal(450, 300, n_years))
gdp_growth[8:10] -= 1500  # 1998-1999 recession dip
gdp_growth[18:20] -= 2000  # 2008-2009 financial crisis
gdp_growth[30:32] -= 800  # 2020-2021 pandemic dip
gdp_per_capita = gdp_base + gdp_growth
gdp_per_capita = np.maximum(gdp_per_capita, 5000)

# Life expectancy starts ~68, rises gradually with dips during crises
le_base = 68.0
le_growth = np.cumsum(np.random.normal(0.25, 0.12, n_years))
le_growth[18:20] -= 0.4  # Financial crisis stress
le_growth[30:32] -= 1.2  # Pandemic drop
life_expectancy = le_base + le_growth
life_expectancy = np.clip(life_expectancy, 64, 82)

# Define temporal eras for color gradient segments (light → dark blue)
# Darkened lightest shades for better contrast against light background
eras = [
    ("1990-1997", 0, 8, "#4da6c9"),
    ("1998-2003", 8, 14, "#3d8fb5"),
    ("2004-2009", 14, 20, "#2e78a0"),
    ("2010-2015", 20, 26, "#22618a"),
    ("2016-2019", 26, 30, "#1a4d70"),
    ("2020-2023", 30, 34, "#0e2f44"),
]

# Select key years to annotate
annotate_years = {1998, 2005, 2008, 2015, 2020}

# Style — refined with subtle grid and cohesive blue palette
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="white",
    plot_background="#f4f7fa",
    foreground="#3a3a3a",
    foreground_strong="#2a2a2a",
    foreground_subtle="#d8d8d8",
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="3,5",
    colors=("#4da6c9", "#3d8fb5", "#2e78a0", "#22618a", "#1a4d70", "#0e2f44", "#e8a838", "#c0392b", "#1a3a5c"),
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=34,
    legend_font_family=font,
    value_font_size=32,
    value_label_font_size=36,
    tooltip_font_size=26,
    tooltip_font_family=font,
    opacity=0.92,
    opacity_hover=1.0,
    stroke_opacity=0.9,
    stroke_opacity_hover=1.0,
)

# Axis ranges
x_min = float(np.floor(gdp_per_capita.min() / 1000) * 1000)
x_max = float(np.ceil(gdp_per_capita.max() / 1000) * 1000)
y_min = float(np.floor(life_expectancy.min()))
y_max = float(np.ceil(life_expectancy.max()) + 1)

# Create XY chart with native print_labels for year annotations
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Life Expectancy vs GDP · scatter-connected-temporal · pygal · pyplots.ai",
    x_title="GDP per Capita (USD)",
    y_title="Life Expectancy (years)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=24,
    stroke=True,
    dots_size=10,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"${x:,.0f}",
    value_formatter=lambda y: f"{y:.1f} yrs",
    print_labels=True,
    print_values=False,
    margin_bottom=120,
    margin_left=70,
    margin_right=70,
    margin_top=55,
    range=(y_min, y_max),
    xrange=(x_min, x_max),
    x_labels_major_count=7,
    y_labels_major_count=8,
    js=[],
    show_x_labels=True,
    show_y_labels=True,
)

# Add temporal path as gradient-colored era segments
# Each segment overlaps by 1 point for visual continuity
for era_name, start, end, color in eras:
    end_idx = min(end + 1, n_years)
    segment_points = [
        {"value": (float(gdp_per_capita[i]), float(life_expectancy[i])), "color": color} for i in range(start, end_idx)
    ]
    chart.add(
        era_name,
        segment_points,
        stroke=True,
        show_dots=True,
        dots_size=10,
        stroke_style={"width": 6, "linecap": "round", "linejoin": "round"},
    )

# Highlight annotated key years with larger amber dots and native year labels
annotated_points = []
for yr in sorted(annotate_years):
    i = yr - 1990
    annotated_points.append(
        {"value": (float(gdp_per_capita[i]), float(life_expectancy[i])), "label": str(yr), "color": "#e8a838"}
    )
chart.add("Key years", annotated_points, stroke=False, dots_size=16)

# Highlight start and end with distinct large markers
chart.add(
    f"Start ({years[0]})",
    [{"value": (float(gdp_per_capita[0]), float(life_expectancy[0])), "label": "\u25b6 1990", "color": "#c0392b"}],
    stroke=False,
    dots_size=22,
)
chart.add(
    f"End ({years[-1]})",
    [{"value": (float(gdp_per_capita[-1]), float(life_expectancy[-1])), "label": "\u25cf 2023", "color": "#1a3a5c"}],
    stroke=False,
    dots_size=22,
)

# Save PNG via cairosvg and HTML
svg_data = chart.render()
cairosvg.svg2png(bytestring=svg_data, write_to="plot.png")
chart.render_to_file("plot.html")
