"""anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 77/100 | Updated: 2026-05-23
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    geom_text,
    gggrid,
    ggplot,
    labs,
    layer_tooltips,
    scale_fill_gradient,
    scale_size,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
CONTINENT_FILL = "#E0DDD6" if THEME == "light" else "#2E2E2A"
CONTINENT_BORDER = "#C4C0B8" if THEME == "light" else "#4A4A44"
STROKE_DRILLABLE = "#9418DB"

np.random.seed(42)

# ── Level 1: Country bubbles (16 countries across all continents) ─────────────
countries = [
    {"id": "usa", "name": "USA", "value": 4850, "lat": 39.8, "lon": -98.5, "drillable": True},
    {"id": "canada", "name": "Canada", "value": 1420, "lat": 56.1, "lon": -106.3, "drillable": True},
    {"id": "mexico", "name": "Mexico", "value": 980, "lat": 23.6, "lon": -102.5, "drillable": False},
    {"id": "brazil", "name": "Brazil", "value": 1650, "lat": -14.2, "lon": -51.9, "drillable": False},
    {"id": "argentina", "name": "Argentina", "value": 720, "lat": -34.6, "lon": -64.2, "drillable": False},
    {"id": "uk", "name": "UK", "value": 2100, "lat": 55.0, "lon": -3.4, "drillable": False},
    {"id": "germany", "name": "Germany", "value": 2350, "lat": 51.2, "lon": 10.5, "drillable": False},
    {"id": "france", "name": "France", "value": 1890, "lat": 46.2, "lon": 2.2, "drillable": False},
    {"id": "italy", "name": "Italy", "value": 1230, "lat": 42.5, "lon": 14.0, "drillable": False},
    {"id": "spain", "name": "Spain", "value": 1050, "lat": 40.4, "lon": -3.7, "drillable": False},
    {"id": "china", "name": "China", "value": 3600, "lat": 35.9, "lon": 104.2, "drillable": False},
    {"id": "japan", "name": "Japan", "value": 2800, "lat": 36.2, "lon": 138.3, "drillable": False},
    {"id": "india", "name": "India", "value": 1950, "lat": 20.6, "lon": 78.9, "drillable": False},
    {"id": "southafrica", "name": "S. Africa", "value": 890, "lat": -30.6, "lon": 25.1, "drillable": False},
    {"id": "nigeria", "name": "Nigeria", "value": 640, "lat": 9.1, "lon": 8.7, "drillable": False},
    {"id": "australia", "name": "Australia", "value": 1280, "lat": -25.3, "lon": 133.8, "drillable": False},
]

# ── Level 2: US state drill-down ──────────────────────────────────────────────
us_states = [
    {"name": "California", "abbr": "CA", "value": 920, "lat": 36.7, "lon": -119.4},
    {"name": "Texas", "abbr": "TX", "value": 810, "lat": 31.0, "lon": -99.9},
    {"name": "New York", "abbr": "NY", "value": 680, "lat": 43.0, "lon": -75.5},
    {"name": "Florida", "abbr": "FL", "value": 560, "lat": 27.7, "lon": -81.5},
    {"name": "Illinois", "abbr": "IL", "value": 430, "lat": 40.0, "lon": -89.2},
    {"name": "Washington", "abbr": "WA", "value": 380, "lat": 47.5, "lon": -120.5},
    {"name": "Georgia", "abbr": "GA", "value": 320, "lat": 32.7, "lon": -83.4},
    {"name": "Colorado", "abbr": "CO", "value": 290, "lat": 39.1, "lon": -105.4},
    {"name": "Ohio", "abbr": "OH", "value": 270, "lat": 40.4, "lon": -82.8},
    {"name": "Arizona", "abbr": "AZ", "value": 210, "lat": 34.3, "lon": -111.6},
]

# ── Continent outlines ────────────────────────────────────────────────────────
continent_rows = []

na_coords = [
    (-170, 66),
    (-140, 60),
    (-125, 48),
    (-118, 34),
    (-105, 25),
    (-97, 26),
    (-82, 23),
    (-80, 25),
    (-83, 30),
    (-92, 29),
    (-97, 28),
    (-87, 15),
    (-78, 9),
    (-62, 10),
    (-60, 14),
    (-67, 18),
    (-72, 21),
    (-80, 25),
    (-76, 35),
    (-72, 41),
    (-67, 45),
    (-60, 47),
    (-55, 50),
    (-63, 58),
    (-85, 65),
    (-110, 70),
    (-145, 68),
    (-165, 65),
    (-170, 66),
]
sa_coords = [
    (-80, 10),
    (-62, 10),
    (-52, 4),
    (-48, -2),
    (-35, -8),
    (-35, -18),
    (-43, -23),
    (-52, -33),
    (-65, -42),
    (-72, -52),
    (-64, -55),
    (-65, -45),
    (-72, -30),
    (-75, -15),
    (-81, -5),
    (-78, 2),
    (-80, 10),
]
europe_coords = [
    (-10, 36),
    (-8, 43),
    (0, 43),
    (3, 42),
    (13, 45),
    (14, 42),
    (25, 37),
    (40, 41),
    (50, 45),
    (60, 55),
    (50, 60),
    (60, 70),
    (25, 71),
    (15, 68),
    (5, 62),
    (10, 55),
    (8, 52),
    (-5, 50),
    (-10, 44),
    (-10, 36),
]
asia_coords = [
    (26, 41),
    (40, 41),
    (50, 45),
    (60, 55),
    (80, 72),
    (100, 70),
    (130, 60),
    (140, 55),
    (145, 45),
    (140, 40),
    (145, 35),
    (155, 20),
    (145, 10),
    (130, 0),
    (125, -8),
    (120, -10),
    (105, -5),
    (100, 2),
    (90, 12),
    (80, 10),
    (65, 25),
    (57, 22),
    (50, 30),
    (40, 36),
    (28, 41),
    (26, 41),
]
africa_coords = [
    (-10, 36),
    (0, 37),
    (10, 37),
    (25, 37),
    (35, 35),
    (42, 20),
    (50, 12),
    (50, 5),
    (42, -12),
    (38, -20),
    (35, -24),
    (26, -34),
    (20, -35),
    (18, -35),
    (12, -30),
    (10, -22),
    (8, -12),
    (5, -4),
    (2, 0),
    (-8, 5),
    (-10, 8),
    (-15, 12),
    (-18, 16),
    (-18, 22),
    (-10, 36),
]
aus_coords = [
    (115, -20),
    (128, -15),
    (137, -16),
    (142, -11),
    (145, -15),
    (153, -25),
    (153, -30),
    (151, -34),
    (147, -38),
    (138, -35),
    (125, -35),
    (114, -32),
    (114, -26),
    (115, -20),
]

for coords, cname in [
    (na_coords, "North America"),
    (sa_coords, "South America"),
    (europe_coords, "Europe"),
    (asia_coords, "Asia"),
    (africa_coords, "Africa"),
    (aus_coords, "Australia"),
]:
    for lon, lat in coords:
        continent_rows.append({"lon": lon, "lat": lat, "continent": cname})

continents = pd.DataFrame(continent_rows)

# ── USA outline for drilldown panel ──────────────────────────────────────────
usa_outline_coords = [
    (-124, 49),
    (-117, 49),
    (-109, 49),
    (-97, 49),
    (-88, 48),
    (-83, 46),
    (-80, 43),
    (-75, 45),
    (-68, 47),
    (-67, 45),
    (-70, 42),
    (-72, 41),
    (-75, 38),
    (-76, 34),
    (-80, 30),
    (-80, 25),
    (-82, 24),
    (-85, 29),
    (-88, 30),
    (-89, 29),
    (-97, 26),
    (-105, 25),
    (-117, 32),
    (-118, 34),
    (-124, 40),
    (-124, 46),
    (-124, 49),
]
usa_outline = pd.DataFrame([{"lon": lon, "lat": lat, "region": "USA"} for lon, lat in usa_outline_coords])

# ── Label offsets for world map ───────────────────────────────────────────────
label_offsets = {
    "usa": (0, -9),
    "canada": (22, 3),
    "mexico": (0, -8),
    "brazil": (0, -10),
    "argentina": (0, -9),
    "uk": (-18, 8),
    "germany": (18, 7),
    "france": (-18, -9),
    "italy": (12, -9),
    "spain": (-15, -10),
    "china": (0, -9),
    "japan": (12, 5),
    "india": (0, -9),
    "southafrica": (0, -9),
    "nigeria": (-18, 5),
    "australia": (-35, 0),
}

# ── Prepare DataFrames ────────────────────────────────────────────────────────
records = []
for c in countries:
    nx, ny = label_offsets.get(c["id"], (0, -8))
    records.append(
        {
            "name": c["name"],
            "lon": c["lon"],
            "lat": c["lat"],
            "value": c["value"],
            "drillable": c["drillable"],
            "label_lon": c["lon"] + nx,
            "label_lat": c["lat"] + ny,
            "sales": f"${c['value'] / 1000:.2f}B",
            "type": "▼ Drillable" if c["drillable"] else "Leaf node",
        }
    )
df = pd.DataFrame(records)
df_drill = df[df["drillable"]]
df_leaf = df[~df["drillable"]]

df_states = pd.DataFrame(us_states)
df_states["sales"] = df_states["value"].apply(lambda v: f"${v}M")

# ── World map — Level 1 ───────────────────────────────────────────────────────
world_plot = (
    ggplot()
    + geom_polygon(
        data=continents,
        mapping=aes(x="lon", y="lat", group="continent"),
        fill=CONTINENT_FILL,
        color=CONTINENT_BORDER,
        alpha=0.7,
        size=0.4,
        tooltips="none",
    )
    + geom_point(
        data=df_leaf,
        mapping=aes(x="lon", y="lat", size="value", fill="value"),
        color=INK_SOFT,
        alpha=0.85,
        shape=21,
        stroke=1.5,
        tooltips=layer_tooltips().title("@name").line("Sales|@sales").line("@type"),
    )
    # Purple stroke flags drillable countries
    + geom_point(
        data=df_drill,
        mapping=aes(x="lon", y="lat", size="value", fill="value"),
        color=STROKE_DRILLABLE,
        alpha=0.85,
        shape=21,
        stroke=2.5,
        tooltips=layer_tooltips().title("@name").line("Sales|@sales").line("@type"),
    )
    + geom_text(
        data=df,
        mapping=aes(x="label_lon", y="label_lat", label="name"),
        size=9,
        color=INK,
        fontface="bold",
        tooltips="none",
    )
    + scale_size(range=[5, 18], guide="none")
    + scale_fill_gradient(low="#009E73", high="#003D94", name="Sales ($M)")
    + coord_fixed(ratio=1.3, xlim=[-180, 200], ylim=[-60, 75])
    + labs(
        title="map-drilldown-geographic · python · letsplot · anyplot.ai",
        subtitle="World → Country Level  ·  Purple border = click to drill into states",
    )
    + theme_void()
    + theme(
        plot_title=element_text(size=14, face="bold", hjust=0.5, color=INK),
        plot_subtitle=element_text(size=10, hjust=0.5, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_position=[0.92, 0.18],
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
)

# ── US States — Level 2 drill-down ────────────────────────────────────────────
us_plot = (
    ggplot()
    + geom_polygon(
        data=usa_outline,
        mapping=aes(x="lon", y="lat", group="region"),
        fill=CONTINENT_FILL,
        color=CONTINENT_BORDER,
        alpha=0.7,
        size=0.4,
        tooltips="none",
    )
    + geom_point(
        data=df_states,
        mapping=aes(x="lon", y="lat", size="value", fill="value"),
        color=INK_SOFT,
        alpha=0.85,
        shape=21,
        stroke=1.5,
        tooltips=layer_tooltips().title("@name").line("Sales|@sales"),
    )
    + geom_text(
        data=df_states,
        mapping=aes(x="lon", y="lat", label="abbr"),
        size=8,
        color=INK,
        fontface="bold",
        nudge_y=-2.5,
        tooltips="none",
    )
    + scale_size(range=[5, 16], guide="none")
    + scale_fill_gradient(low="#009E73", high="#003D94", name="Sales ($M)")
    + coord_fixed(ratio=1.3, xlim=[-128, -65], ylim=[23, 52])
    + labs(title="USA → State Level  (drill-down)", subtitle="Breadcrumb: World > United States")
    + theme_void()
    + theme(
        plot_title=element_text(size=11, face="bold", hjust=0.5, color=INK),
        plot_subtitle=element_text(size=9, hjust=0.5, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position=[0.85, 0.15],
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
)

# ── Combine panels and save ───────────────────────────────────────────────────
grid = gggrid([world_plot, us_plot], ncol=2, widths=[2, 1])

ggsave(grid, f"plot-{THEME}.png", path=".", w=3200, h=1800, unit="px")
ggsave(grid, f"plot-{THEME}.html", path=".", w=800, h=450, unit="px")
