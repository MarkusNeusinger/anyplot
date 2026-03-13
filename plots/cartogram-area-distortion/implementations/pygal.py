"""pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: pygal 3.1.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-13
"""

import pygal
from pygal.style import Style


# Countries grouped by continent with realistic population values (millions, 2024 est.)
# Only countries >= 40M to ensure all labels are legible on treemap rectangles
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
        "Thailand": 72,
        "Myanmar": 55,
        "South Korea": 52,
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
    "Europe": {"Russia": 144, "Germany": 84, "UK": 68, "France": 68, "Italy": 59, "Spain": 48},
    "Americas": {"United States": 340, "Brazil": 216, "Mexico": 130, "Colombia": 52, "Argentina": 46},
    "Oceania": {"Australia": 27},
}

# Colorblind-safe palette: one distinct color per continent
continent_colors = (
    "#2b6ca3",  # Asia - Deep steel blue
    "#d4951a",  # Africa - Rich amber
    "#2a8c2a",  # Europe - Forest green
    "#c74040",  # Americas - Warm coral
    "#7b5ea7",  # Oceania - Plum purple
)

# Style with refined typography and strong visual hierarchy
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#1a1a1a",
    foreground_strong="#000000",
    foreground_subtle="#cccccc",
    colors=continent_colors,
    title_font_size=76,
    label_font_size=38,
    legend_font_size=48,
    major_label_font_size=38,
    value_font_size=32,
    tooltip_font_size=32,
    no_data_font_size=32,
    font_family="Helvetica Neue, Helvetica, Arial, sans-serif",
    opacity=0.92,
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
    legend_box_size=40,
    print_labels=True,
    print_values=True,
    value_formatter=lambda x: f"{x:,.0f}M" if x else "",
    margin=30,
    margin_bottom=70,
    margin_top=10,
    truncate_label=-1,
    truncate_legend=-1,
    spacing=4,
)

# Add each continent as a series with country labels
for continent, countries in regions.items():
    treemap.add(continent, [{"value": pop, "label": name} for name, pop in countries.items()])

# Save
treemap.render_to_png("plot.png")
