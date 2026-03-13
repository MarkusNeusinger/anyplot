""" pyplots.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-13
"""

import pygal
from pygal.style import Style


# Countries grouped by continent with population (millions, 2024 est.)
# and land area (thousand km²) for computing distortion ratios.
# Distortion ratio = (pop share) / (area share): >1 means region GROWS
# in the cartogram vs. a geographic map, <1 means it SHRINKS.
regions = {
    "Asia": {
        "India": (1441, 3287),
        "China": (1425, 9597),
        "Indonesia": (278, 1905),
        "Pakistan": (240, 882),
        "Bangladesh": (173, 148),
        "Japan": (124, 378),
        "Philippines": (117, 300),
        "Vietnam": (99, 331),
        "S. Korea": (52, 100),
    },
    "Africa": {
        "Nigeria": (224, 924),
        "Ethiopia": (126, 1104),
        "Egypt": (113, 1001),
        "DR Congo": (102, 2345),
        "S. Africa": (60, 1221),
        "Kenya": (55, 580),
    },
    "Europe": {"Russia": (144, 17098), "Germany": (84, 357), "UK": (68, 244), "France": (68, 640), "Italy": (59, 301)},
    "Americas": {"USA": (340, 9834), "Brazil": (216, 8516), "Mexico": (130, 1964), "Colombia": (52, 1139)},
    "Oceania": {"Australia": (27, 7692)},
}

# Colorblind-safe palette with high saturation for strong continent identity
continent_colors = (
    "#1a6ca3",  # Asia - Deep ocean blue
    "#d48c0a",  # Africa - Rich golden amber
    "#1a7a3a",  # Europe - Forest green
    "#c22828",  # Americas - Bold vermilion
    "#6b3fa0",  # Oceania - Deep violet
)

# Publication-quality style with refined typographic hierarchy
custom_style = Style(
    background="white",
    plot_background="#fcfcfc",
    foreground="#1a1a1a",
    foreground_strong="#000000",
    foreground_subtle="#e8e8e8",
    colors=continent_colors,
    title_font_size=68,
    label_font_size=44,
    legend_font_size=52,
    major_label_font_size=44,
    value_font_size=40,
    tooltip_font_size=38,
    no_data_font_size=38,
    font_family="Helvetica Neue, Helvetica, Arial, sans-serif",
    opacity=0.90,
    opacity_hover=1.0,
)

# Compute totals for distortion ratio calculation
total_pop = sum(pop for cont in regions.values() for pop, _ in cont.values())
total_area = sum(area for cont in regions.values() for _, area in cont.values())

# Treemap — pygal's best cartogram approximation (no geographic chart types).
# Rectangle area = population, showing how regions expand or shrink vs a standard map.
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
    legend_box_size=46,
    print_labels=False,
    print_values=True,
    value_formatter=lambda x: f"{x:,.0f}M" if x else "",
    margin=50,
    margin_bottom=90,
    margin_top=25,
    margin_left=50,
    margin_right=50,
    truncate_label=-1,
    truncate_legend=-1,
    spacing=8,
    rounded_corners=4,
)

# Add each continent as a series. Per-node formatter (a distinctive pygal feature)
# overrides the chart-level value_formatter to display country name, population,
# and distortion ratio — providing geographic reference comparison context.
for continent, countries in regions.items():
    series_data = []
    for name, (pop, area) in countries.items():
        pop_share = pop / total_pop
        area_share = area / total_area
        ratio = pop_share / area_share
        series_data.append(
            {
                "value": pop,
                "label": f"{name} ({ratio:.1f}x)",
                "formatter": lambda x, n=name, r=ratio: f"{n} {x:,.0f}M \u00d7{r:.1f}",
            }
        )
    treemap.add(continent, series_data)

# Save
treemap.render_to_png("plot.png")
