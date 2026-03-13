"""pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-13
"""

import numpy as np
import pygal
from pygal.style import Style


# Data: World regions with population (millions) as the area-distortion variable
np.random.seed(42)

# Countries grouped by continent with realistic population values (millions, 2024 est.)
regions = {
    "Asia": {
        "China": 1425,
        "India": 1441,
        "Indonesia": 278,
        "Pakistan": 240,
        "Bangladesh": 173,
        "Japan": 124,
        "Philippines": 117,
        "Vietnam": 99,
    },
    "Africa": {
        "Nigeria": 224,
        "Ethiopia": 126,
        "Egypt": 113,
        "DR Congo": 102,
        "Tanzania": 67,
        "South Africa": 60,
        "Kenya": 55,
    },
    "Europe": {"Russia": 144, "Germany": 84, "UK": 68, "France": 68, "Italy": 59, "Spain": 48, "Poland": 37},
    "Americas": {"United States": 340, "Brazil": 216, "Mexico": 130, "Colombia": 52, "Argentina": 46, "Canada": 41},
    "Oceania": {"Australia": 27, "Papua New Guinea": 10, "New Zealand": 5},
}

# Color palette: one color per continent, colorblind-safe
continent_colors = (
    "#306998",  # Asia - Python Blue
    "#e6a532",  # Africa - Amber
    "#2ca02c",  # Europe - Green
    "#d64e4e",  # Americas - Red
    "#8c6bb1",  # Oceania - Purple
)

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#999999",
    colors=continent_colors,
    title_font_size=80,
    label_font_size=44,
    legend_font_size=48,
    major_label_font_size=40,
    value_font_size=36,
    tooltip_font_size=36,
    no_data_font_size=36,
    opacity=0.85,
    opacity_hover=0.95,
)

# Chart
treemap = pygal.Treemap(
    style=custom_style,
    width=4800,
    height=2700,
    title="World Population Cartogram \u00b7 cartogram-area-distortion \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=40,
    value_formatter=lambda x: f"{x:,.0f}M" if x else "",
    margin=30,
)

# Add each continent as a series (area proportional to population)
for continent, countries in regions.items():
    treemap.add(continent, [{"value": pop, "label": f"{name} ({pop:,}M)"} for name, pop in countries.items()])

# Save
treemap.render_to_file("plot.html")
treemap.render_to_png("plot.png")
