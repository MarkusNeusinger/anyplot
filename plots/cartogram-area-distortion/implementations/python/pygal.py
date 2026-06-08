""" anyplot.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: pygal 3.1.0 | Python 3.13.13
Quality: 77/100 | Updated: 2026-06-08
"""

import os
import sys


# Remove the script's own directory from sys.path so that `import pygal` finds
# the installed package rather than this file (which shares the package name).
_here = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
sys.path[:] = [p for p in sys.path if p and os.path.abspath(p) != _here]
del _here

import pygal
from pygal.style import Style


# Theme tokens — theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette (hybrid-v3 order) — 5 used for 5 continent series
IMPRINT_PALETTE = (
    "#009E73",  # 1 brand green — Asia (first series, always)
    "#C475FD",  # 2 lavender — Africa
    "#4467A3",  # 3 blue — Europe
    "#BD8233",  # 4 ochre — Americas
    "#AE3030",  # 5 matte red — Oceania
    "#2ABCCD",
    "#954477",
    "#99B314",
)

# 2-letter display labels for small-tile countries to stay legible at thumbnail widths
SHORT_LABELS = {
    "S. Korea": "KR",
    "Colombia": "CO",
    "Australia": "AU",
    "Vietnam": "VN",
    "Kenya": "KE",
    "S. Africa": "ZA",
    "Italy": "IT",
    "UK": "GB",
    "Germany": "DE",
    "France": "FR",
    "Japan": "JP",
}
ABBREV_THRESHOLD = 100  # million — tiles smaller than this get 2-letter codes

# Countries grouped by continent: (population millions, land area thousand km², 2024 est.)
# Distortion ratio = pop_share / area_share: >1 means the region GROWS in the
# cartogram relative to a standard geographic map, <1 means it SHRINKS.
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

total_pop = sum(pop for cont in regions.values() for pop, _ in cont.values())
total_area = sum(area for cont in regions.values() for _, area in cont.values())

# Title with length-adjusted font size (pygal default 66, floor 44)
title = "World Population Cartogram · cartogram-area-distortion · python · pygal · anyplot.ai"
subtitle = "Tile area ~ population (2024 est.) · hover tiles for distortion ratio vs geographic map"
title_fontsize = max(44, round(66 * 67 / len(title)))  # sized on main title, not full string

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_fontsize,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=46,
    stroke_width=2.5,
)

# Treemap — pygal's best cartogram approximation (no geographic chart types).
# Rectangle area is proportional to population; continent color encodes regional grouping.
treemap = pygal.Treemap(
    style=custom_style,
    width=3200,
    height=1800,
    title=f"{title}\n{subtitle}",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=46,
    print_labels=True,
    print_values=False,
    margin=50,
    margin_bottom=90,
    margin_top=25,
    margin_left=50,
    margin_right=50,
    truncate_label=-1,
    truncate_legend=-1,
    spacing=6,
    rounded_corners=4,
)

# Per-node formatter (distinctive pygal feature) provides rich hover tooltips with
# distortion ratio context. Small tiles use 2-letter codes for legibility; the
# tooltip always carries the full country name and "×N.N vs map" narrative.
for continent, countries in regions.items():
    series_data = []
    for name, (pop, area) in countries.items():
        pop_share = pop / total_pop
        area_share = area / total_area
        ratio = pop_share / area_share
        label = SHORT_LABELS.get(name, name) if pop < ABBREV_THRESHOLD else name
        series_data.append(
            {
                "value": pop,
                "label": label,
                "formatter": lambda x, n=name, r=ratio: f"{n}: {x:,.0f}M pop · ×{r:.1f} vs map",
            }
        )
    treemap.add(continent, series_data)

# Save PNG and interactive HTML
treemap.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(treemap.render())
