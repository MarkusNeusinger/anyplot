""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: pygal 3.1.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-13
"""

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
eras = [
    ("1990s early", 0, 8, "#a8d8ea"),  # Lightest blue
    ("1990s late", 8, 14, "#72b5d4"),  # Light blue
    ("2000s", 14, 20, "#4a90b8"),  # Medium blue
    ("2010s", 20, 26, "#2e6a8e"),  # Medium-dark blue
    ("Recovery", 26, 30, "#1d4f6e"),  # Dark blue
    ("2020s", 30, 34, "#0e2f44"),  # Darkest blue
]

# Select key years to annotate
annotate_years = [1990, 1998, 2008, 2015, 2020, 2023]

# Style — refined with no-spine look via subtle foreground
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="white",
    plot_background="#f7f9fb",
    foreground="#3a3a3a",
    foreground_strong="#2a2a2a",
    foreground_subtle="#e2e2e2",
    guide_stroke_color="#e8e8e8",
    guide_stroke_dasharray="2,4",
    colors=("#a8d8ea", "#72b5d4", "#4a90b8", "#2e6a8e", "#1d4f6e", "#0e2f44", "#e8a838", "#c0392b", "#1a3a5c"),
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=34,
    legend_font_family=font,
    value_font_size=26,
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

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Life Expectancy vs GDP · scatter-connected-temporal · pygal · pyplots.ai",
    x_title="GDP per Capita (USD)",
    y_title="Life Expectancy (years)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=24,
    stroke=True,
    dots_size=10,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"${x:,.0f}",
    value_formatter=lambda y: f"{y:.1f} yrs",
    margin_bottom=110,
    margin_left=70,
    margin_right=60,
    margin_top=55,
    range=(y_min, y_max),
    xrange=(x_min, x_max),
    x_labels_major_count=7,
    y_labels_major_count=8,
    print_values=False,
    js=[],
    show_x_labels=True,
    show_y_labels=True,
)

# Add temporal path as gradient-colored era segments
# Each segment overlaps by 1 point for visual continuity
for _era_name, start, end, color in eras:
    end_idx = min(end + 1, n_years)  # overlap by 1 for continuity
    segment_points = [
        {
            "value": (float(gdp_per_capita[i]), float(life_expectancy[i])),
            "label": f"{years[i]}: GDP ${gdp_per_capita[i]:,.0f}, LE {life_expectancy[i]:.1f}",
            "color": color,
        }
        for i in range(start, end_idx)
    ]
    yr_start = years[start]
    yr_end = years[min(end, n_years - 1)]
    chart.add(
        f"{yr_start}-{yr_end}",
        segment_points,
        stroke=True,
        show_dots=True,
        dots_size=10,
        stroke_style={"width": 6, "linecap": "round", "linejoin": "round"},
    )

# Highlight annotated key years with larger, distinct amber dots
annotated_points = []
for yr in annotate_years:
    i = yr - 1990
    annotated_points.append(
        {
            "value": (float(gdp_per_capita[i]), float(life_expectancy[i])),
            "label": f"{yr}: GDP ${gdp_per_capita[i]:,.0f}, LE {life_expectancy[i]:.1f}",
            "color": "#e8a838",
        }
    )
chart.add("Key years", annotated_points, stroke=False, dots_size=16)

# Highlight start and end with distinct large markers
chart.add(
    f"Start ({years[0]})",
    [
        {
            "value": (float(gdp_per_capita[0]), float(life_expectancy[0])),
            "label": f"{years[0]}: Beginning",
            "color": "#c0392b",
        }
    ],
    stroke=False,
    dots_size=22,
)
chart.add(
    f"End ({years[-1]})",
    [
        {
            "value": (float(gdp_per_capita[-1]), float(life_expectancy[-1])),
            "label": f"{years[-1]}: Present",
            "color": "#1a3a5c",
        }
    ],
    stroke=False,
    dots_size=22,
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
