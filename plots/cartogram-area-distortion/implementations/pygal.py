""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: pygal 3.1.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-13
"""

import pygal
from pygal.style import Style


# Countries grouped by continent with realistic population values (millions, 2024 est.)
# India listed first to highlight it surpassing China as most populous
regions = {
    "Asia": {
        "India": 1441,
        "China": 1425,
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

# Colorblind-safe palette: one distinct color per continent
continent_colors = (
    "#306998",  # Asia - Steel blue
    "#e6a532",  # Africa - Amber
    "#2ca02c",  # Europe - Green
    "#d64e4e",  # Americas - Coral
    "#8c6bb1",  # Oceania - Purple
)

# Style with refined typography
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2d2d2d",
    foreground_strong="#111111",
    foreground_subtle="#bbbbbb",
    colors=continent_colors,
    title_font_size=72,
    label_font_size=36,
    legend_font_size=44,
    major_label_font_size=36,
    value_font_size=30,
    tooltip_font_size=30,
    no_data_font_size=30,
    font_family="Helvetica, Arial, sans-serif",
    opacity=0.88,
    opacity_hover=1.0,
)

# Chart: treemap as best cartogram approximation in pygal (no geographic chart types)
treemap = pygal.Treemap(
    style=custom_style,
    width=4800,
    height=2700,
    title=(
        "World Population Cartogram \u2014 Area Proportional to Population (millions)"
        " \u00b7 cartogram-area-distortion \u00b7 pygal \u00b7 pyplots.ai"
    ),
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=36,
    print_labels=True,
    print_values=True,
    value_formatter=lambda x: f"{x:,.0f}M" if x else "",
    margin=20,
    margin_bottom=60,
    truncate_label=-1,
    truncate_legend=-1,
)

# Add each continent as a series with country labels
for continent, countries in regions.items():
    treemap.add(continent, [{"value": pop, "label": name} for name, pop in countries.items()])

# Save
treemap.render_to_png("plot.png")
