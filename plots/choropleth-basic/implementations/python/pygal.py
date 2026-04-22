""" pyplots.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
from pygal.style import Style
from pygal_maps_world.maps import World


# Data: GDP per capita (synthetic but realistic ranges)
np.random.seed(42)

# Select a diverse set of countries from different regions
country_codes = [
    # Americas
    "us",
    "ca",
    "mx",
    "br",
    "ar",
    "cl",
    "co",
    "pe",
    # Europe
    "de",
    "fr",
    "gb",
    "it",
    "es",
    "nl",
    "se",
    "no",
    "pl",
    "pt",
    # Asia
    "cn",
    "jp",
    "in",
    "kr",
    "id",
    "th",
    "vn",
    "my",
    # Africa
    "za",
    "eg",
    "ng",
    "ke",
    "ma",
    "gh",
    # Oceania
    "au",
    "nz",
]

# Generate realistic GDP per capita values (in thousands USD)
high_income = ["us", "ca", "de", "fr", "gb", "nl", "se", "no", "jp", "kr", "au", "nz"]
upper_middle = ["mx", "br", "ar", "cl", "cn", "my", "za", "pl", "pt", "it", "es"]

gdp_data = {}
for code in country_codes:
    if code in high_income:
        gdp_data[code] = np.random.uniform(40, 85)
    elif code in upper_middle:
        gdp_data[code] = np.random.uniform(10, 40)
    else:
        gdp_data[code] = np.random.uniform(1, 15)

# Bin data into ranges for legend clarity
bins = [
    ("GDP < $10k", {k: v for k, v in gdp_data.items() if v < 10}),
    ("GDP $10k-$25k", {k: v for k, v in gdp_data.items() if 10 <= v < 25}),
    ("GDP $25k-$50k", {k: v for k, v in gdp_data.items() if 25 <= v < 50}),
    ("GDP > $50k", {k: v for k, v in gdp_data.items() if v >= 50}),
]

# Sequential blue palette for choropleth (light to dark)
colors = ["#a6cee3", "#6baed6", "#3182bd", "#08519c"]

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#666666",
    colors=tuple(colors),
    title_font_size=80,
    label_font_size=48,
    legend_font_size=48,
    major_label_font_size=40,
    value_font_size=40,
    tooltip_font_size=36,
    no_data_font_size=36,
)

# Create world map
worldmap = World(
    style=custom_style,
    width=4800,
    height=2700,
    title="choropleth-basic \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=40,
)

# Add each bin as a separate series
for label, data in bins:
    worldmap.add(label, data)

# Save outputs
worldmap.render_to_file("plot.html")
worldmap.render_to_png("plot.png")
