""" anyplot.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-08
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    guide_legend,
    guides,
    labs,
    layer_tooltips,
    scale_color_identity,
    scale_fill_gradient,
    scale_size_area,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential colormap: brand green (#009E73) → blue (#4467A3)
CMAP_LOW = "#009E73"
CMAP_HIGH = "#4467A3"

# Constants
POPULATION_KEYS = [5, 20, 40, 80]  # population (millions) shown in the size legend
LARGE_POP = 30  # millions: bold large labels above this
SMALL_POP = 12  # millions: bubbles at or below this are too small for two letters; their label sits beside them

# Data: 20 European countries — population (millions) and GDP per capita (thousands USD)
# NL/BE positions spread further apart to reduce label crowding in Central Europe
countries_data = {
    "country": [
        "Germany",
        "France",
        "United Kingdom",
        "Italy",
        "Spain",
        "Poland",
        "Netherlands",
        "Belgium",
        "Sweden",
        "Austria",
        "Switzerland",
        "Norway",
        "Denmark",
        "Finland",
        "Ireland",
        "Portugal",
        "Czech Republic",
        "Greece",
        "Hungary",
        "Romania",
    ],
    "population": [
        83.2,
        67.8,
        67.0,
        59.0,
        47.4,
        37.7,
        17.5,
        11.6,
        10.4,
        9.1,
        8.8,
        5.4,
        5.9,
        5.5,
        5.1,
        10.3,
        10.8,
        10.4,
        9.7,
        19.0,
    ],
    "gdp_per_capita": [
        48.7,
        42.3,
        46.1,
        34.5,
        30.1,
        17.8,
        57.0,
        51.2,
        55.7,
        53.3,
        92.4,
        89.2,
        67.8,
        53.2,
        100.2,
        24.5,
        27.0,
        20.2,
        18.8,
        15.1,
    ],
    # Adjusted centroids: NL moved east, BE moved west/south for visual separation
    "lon": [
        10.4,
        2.2,
        -1.2,
        12.6,
        -3.7,
        19.1,
        6.5,
        2.0,
        15.0,
        14.6,
        8.5,
        8.5,
        9.5,
        25.7,
        -8.2,
        -8.2,
        16.5,
        23.7,
        18.5,
        25.0,
    ],
    "lat": [
        51.2,
        46.2,
        52.5,
        41.9,
        40.5,
        51.9,
        53.0,
        49.5,
        60.1,
        47.0,
        45.5,
        60.5,
        56.3,
        61.9,
        53.4,
        39.4,
        49.5,
        39.1,
        47.5,
        45.9,
    ],
    "abbr": [
        "DE",
        "FR",
        "UK",
        "IT",
        "ES",
        "PL",
        "NL",
        "BE",
        "SE",
        "AT",
        "CH",
        "NO",
        "DK",
        "FI",
        "IE",
        "PT",
        "CZ",
        "GR",
        "HU",
        "RO",
    ],
}
df = pd.DataFrame(countries_data)
df["highlight"] = (df["population"] < 15) & (df["gdp_per_capita"] > 50)
df["size_key"] = np.sqrt(df["population"])

# Stars shifted +1.8° north so they sit above their bubbles
df_stars = df[df["highlight"]].copy()
df_stars["lat"] = df_stars["lat"] + 1.8

# Label color per bubble: ink or page color, whichever contrasts more with the bubble's
# fill on the green-to-blue gradient, so every abbreviation reads in both themes
DARK_TEXT, LIGHT_TEXT = "#1A1A17", "#FAF8F1"
low_rgb, high_rgb, dark_rgb, light_rgb = (
    np.array([int(color[i : i + 2], 16) for i in (1, 3, 5)]) / 255
    for color in (CMAP_LOW, CMAP_HIGH, DARK_TEXT, LIGHT_TEXT)
)
gdp = df["gdp_per_capita"].to_numpy()
share = (gdp - gdp.min()) / (gdp.max() - gdp.min())
rgb = np.vstack([low_rgb + share[:, None] * (high_rgb - low_rgb), dark_rgb, light_rgb])
# WCAG relative luminance of every fill and of the two text colors
luminance = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4) @ [0.2126, 0.7152, 0.0722]
fill_lum, dark_lum, light_lum = luminance[:-2], luminance[-2], luminance[-1]
dark_contrast = (fill_lum + 0.05) / (dark_lum + 0.05)
light_contrast = (light_lum + 0.05) / (fill_lum + 0.05)
df["label_color"] = np.where(dark_contrast >= light_contrast, DARK_TEXT, LIGHT_TEXT)

# Simplified country outlines as closed "lon lat" rings (last point = first point).
# Neighbours share their border vertices exactly, so outlines meet along real borders
# instead of overlapping; gaps are countries outside the sample (Luxembourg, Slovakia, ...)
_borders = {
    "PT": (
        "-8.9 41.9, -8.1 42, -6.5 41.9, -6.2 41.6, -6.9 41, -7 39.6, -7 38.9, -7.4 37.2, -8.9 37, "
        "-8.8 38.5, -9.5 38.8, -8.8 40.5, -8.9 41.9"
    ),
    "ES": (
        "-8.9 41.9, -8.1 42, -6.5 41.9, -6.2 41.6, -6.9 41, -7 39.6, -7 38.9, -7.4 37.2, -6 36.2, -5.4 36, "
        "-2 36.7, -0.7 37.6, 0.2 38.8, -0.3 39.5, 0.9 41, 3.2 41.9, 3.2 42.4, 1.4 42.6, -0.7 42.9, "
        "-1.8 43.4, -3.8 43.5, -8 43.7, -9.3 43, -8.9 41.9"
    ),
    "FR": (
        "3.2 42.4, 1.4 42.6, -0.7 42.9, -1.8 43.4, -1.2 46, -2.2 47.1, -4.8 48.3, -1.6 48.7, -1.3 49.7, "
        "0.2 49.5, 1.6 50.9, 2.5 51.1, 4.2 49.95, 4.8 50.15, 5.8 49.5, 6.4 49.5, 6.7 49.2, 8.2 49, "
        "7.6 48.4, 7.6 47.6, 6.9 47.3, 6.4 46.5, 6.1 46.2, 7 45.9, 7 45.2, 6.9 44.4, 7.5 43.8, 6.2 43.1, "
        "4.8 43.4, 3.1 43.1, 3.2 42.4"
    ),
    "BE": (
        "2.5 51.1, 3.4 51.4, 4.3 51.4, 5 51.5, 5.8 51.2, 5.7 50.75, 6 50.75, 6.4 50.3, 5.8 49.5, "
        "4.8 50.15, 4.2 49.95, 2.5 51.1"
    ),
    "NL": (
        "3.4 51.4, 4.3 51.4, 5 51.5, 5.8 51.2, 5.7 50.75, 6 50.75, 6.2 51.4, 5.95 51.8, 6.8 51.95, "
        "7.05 52.4, 7.2 53.25, 6.2 53.45, 4.8 53, 4.5 52.2, 3.4 51.4"
    ),
    "DE": (
        "6 50.75, 6.2 51.4, 5.95 51.8, 6.8 51.95, 7.05 52.4, 7.2 53.25, 8.6 53.9, 8.6 54.9, 9.9 54.8, "
        "11 54, 12.5 54.5, 14.2 53.9, 14.4 53.2, 14.6 52.6, 14.7 52.1, 15 51.1, 14.3 51, 12.1 50.3, "
        "12.5 49.8, 13.8 48.8, 13.4 48.6, 12.9 48.2, 13 47.5, 12.2 47.6, 10.5 47.5, 9.6 47.5, 8.6 47.8, "
        "7.6 47.6, 7.6 48.4, 8.2 49, 6.7 49.2, 6.4 49.5, 6.4 50.3, 6 50.75"
    ),
    "DK": ("8.6 54.9, 9.9 54.8, 12.6 54.9, 12.6 56, 10.6 56.4, 10.6 57.7, 8.6 57.1, 8.1 56, 8.6 55.4, 8.6 54.9"),
    "PL": (
        "14.2 53.9, 14.4 53.2, 14.6 52.6, 14.7 52.1, 15 51.1, 16.3 50.7, 16.9 50.2, 18 50, 18.8 49.5, "
        "20 49.2, 22.6 49.1, 24 50.5, 23.5 51.6, 23.9 52.7, 23.5 53.9, 22.8 54.4, 19.6 54.4, 18.6 54.8, "
        "16.5 54.5, 14.2 53.9"
    ),
    "CZ": (
        "15 51.1, 16.3 50.7, 16.9 50.2, 18 50, 18.8 49.5, 17.7 48.9, 16.9 48.6, 15 48.8, 14.9 49, "
        "13.8 48.8, 12.5 49.8, 12.1 50.3, 14.3 51, 15 51.1"
    ),
    "AT": (
        "13.8 48.8, 14.9 49, 15 48.8, 16.9 48.6, 17.1 48, 16.5 47.4, 16.1 46.85, 14.6 46.4, 13.7 46.5, "
        "12.4 46.7, 11 46.8, 10.45 46.9, 9.5 47.1, 9.6 47.5, 10.5 47.5, 12.2 47.6, 13 47.5, 12.9 48.2, "
        "13.4 48.6, 13.8 48.8"
    ),
    "CH": (
        "7.6 47.6, 8.6 47.8, 9.6 47.5, 9.5 47.1, 10.45 46.9, 10.1 46.2, 9 45.8, 8.4 46.3, 7 45.9, "
        "6.1 46.2, 6.4 46.5, 6.9 47.3, 7.6 47.6"
    ),
    "IT": (
        "7 45.9, 8.4 46.3, 9 45.8, 10.1 46.2, 10.45 46.9, 11 46.8, 12.4 46.7, 13.7 46.5, 13.7 45.6, "
        "12.3 45.3, 12.4 44.2, 13.6 43.5, 14.7 42.1, 16 41.9, 18.5 40.1, 17.2 39, 16.5 38, 15.6 38, "
        "15.7 40, 14 41.1, 12.4 41.7, 10.5 42.9, 10.2 43.9, 8.8 44.4, 7.5 43.8, 6.9 44.4, 7 45.2, 7 45.9"
    ),
    "HU": (
        "17.1 48, 16.5 47.4, 16.1 46.85, 16.6 46.5, 17.6 45.9, 18.8 45.9, 20.3 46.15, 21.2 46.4, 21.6 47, "
        "22.1 47.7, 22.9 48, 22.1 48.4, 20.8 48.6, 19 48.1, 17.8 47.75, 17.1 48"
    ),
    "RO": (
        "20.3 46.15, 21.2 46.4, 21.6 47, 22.1 47.7, 22.9 48, 24.9 47.7, 26.6 48.25, 28.2 46.5, 28.2 45.5, "
        "29.6 45.4, 28.6 43.75, 25.4 43.6, 22.9 43.9, 22.7 44.5, 21.4 44.8, 21.4 45.2, 20.3 46.15"
    ),
    "GR": (
        "20.2 39.6, 21 40.8, 22.9 41.3, 24 41.5, 26.3 41.7, 26 40.8, 24 40.8, 23 40.3, 22.6 40, 23.3 39, "
        "24 38.2, 23 37.5, 23.2 36.5, 22.5 36.4, 21.7 36.8, 21.1 37.8, 21.6 38.3, 20.7 38.8, 20.2 39.6"
    ),
    "UK": (
        "-5.7 50, -3 50.7, 1.4 51.2, 1.7 52.7, 0.2 53.5, -1.5 55, -2 56, -1.8 57.6, -3 58.6, -5 58.6, "
        "-6.2 56.8, -5 55, -3 54.9, -3.2 54, -3 53.4, -4.6 53.3, -4.2 52.3, -5.2 51.7, -3 51.5, -4.5 51.1, "
        "-5.7 50"
    ),
    "UK-NI": (
        "-7.25 55.05, -7.6 54.7, -8.1 54.5, -7.2 54.2, -6.6 54.05, -6.2 54, -5.5 54.4, -5.8 54.9, "
        "-6.2 55.25, -7.25 55.05"
    ),
    "IE": (
        "-7.25 55.05, -7.6 54.7, -8.1 54.5, -7.2 54.2, -6.6 54.05, -6.2 54, -6 53, -6.4 52.2, -8.5 51.6, "
        "-10.2 51.8, -9.5 53, -10.1 54.2, -8.3 54.6, -8 55.25, -7.25 55.05"
    ),
    "NO": (
        "11.4 58.9, 12.5 60, 12.2 61, 12.9 61.8, 12.1 63.4, 14 64.5, 14.5 65.5, 16.5 67.5, 18 68.5, "
        "20.55 69.06, 21.6 69.3, 24 68.6, 25.8 69.6, 27 70, 28.9 69.05, 31 70.3, 28 71, 25.8 71.1, 19 70, "
        "15 68.3, 13.5 67, 12.5 65.5, 10.5 64.4, 8 63.4, 5.1 62, 5 60, 5.6 58.9, 7 58, 9 58.7, 10.5 59.2, "
        "11.4 58.9"
    ),
    "SE": (
        "11.4 58.9, 12.5 60, 12.2 61, 12.9 61.8, 12.1 63.4, 14 64.5, 14.5 65.5, 16.5 67.5, 18 68.5, "
        "20.55 69.06, 23 68.2, 23.9 66.8, 24.1 65.8, 21.5 64.5, 19 63.2, 17.3 61.5, 18.5 60.2, 19 59.7, "
        "16.5 58.5, 16.5 57, 16 56.2, 14.5 56, 12.9 55.4, 12.5 56.3, 11.7 57.7, 11.4 58.9"
    ),
    "FI": (
        "20.55 69.06, 21.6 69.3, 24 68.6, 25.8 69.6, 27 70, 28.9 69.05, 28.5 68.2, 30 67.7, 29.1 66.9, "
        "30.1 65.7, 29.7 64, 31.5 62.9, 27.8 60.5, 25.5 60.3, 22.9 59.8, 21.3 60.8, 21.5 62.6, 25.4 65.1, "
        "24.1 65.8, 23.9 66.8, 23 68.2, 20.55 69.06"
    ),
}
country_borders = pd.DataFrame(
    [
        {"group": group, "lon": float(lon_v), "lat": float(lat_v)}
        for group, ring in _borders.items()
        for lon_v, lat_v in (point.split() for point in ring.split(", "))
    ]
)

# Title with fontsize scaled for total character count (default 16px, floor 11px)
title = "European Population Cartogram · cartogram-area-distortion · python · letsplot · anyplot.ai"
n = len(title)
title_size = max(11, round(16 * 67 / n))

# Map frame from the data: every bubble and the full reference outlines, with a margin
lat_min = min(country_borders["lat"].min(), df["lat"].min()) - 1
lat_max = max(country_borders["lat"].max(), df_stars["lat"].max()) + 1

plot = (
    ggplot()
    # Individual country border outlines — makes area distortion legible vs actual footprints
    + geom_path(aes(x="lon", y="lat", group="group"), data=country_borders, color=INK_MUTED, size=0.35, alpha=0.5)
    # Bubble area ∝ population, fill color = GDP per capita. lets-plot sizes a marker by its
    # diameter, so the size scale reads the square root of population and maps zero to zero.
    # Every bubble has the same thin page-colored rim, so no outline adds to its drawn area
    + geom_point(
        aes(x="lon", y="lat", size="size_key", fill="gdp_per_capita"),
        data=df,
        shape=21,
        color=PAGE_BG,
        stroke=0.3,
        tooltips=layer_tooltips()
        .title("@country")
        .line("Population|@population M")
        .line("GDP/capita|$@gdp_per_capita K"),
    )
    # Small-but-wealthy nations marked with a star above their bubbles, the same glyph as the key
    + geom_text(aes(x="lon", y="lat"), data=df_stars, label="★", size=7, color=INK)
    + scale_size_area(max_size=26, name="Population (M)", breaks={f"{p}": np.sqrt(p) for p in POPULATION_KEYS})
    + guides(size=guide_legend(override_aes={"fill": INK_MUTED, "color": PAGE_BG}))
    + scale_fill_gradient(low=CMAP_LOW, high=CMAP_HIGH, name="GDP/capita (USD K)")
    # Three-tier label hierarchy: large and medium labels inside their bubbles, each in the
    # text color that contrasts most with the bubble's fill; the smallest bubbles cannot hold
    # two letters, so their labels sit just right of them in ink
    + geom_text(
        aes(x="lon", y="lat", label="abbr", color="label_color"),
        data=df[df["population"] > LARGE_POP],
        size=12,
        fontface="bold",
    )
    + geom_text(
        aes(x="lon", y="lat", label="abbr", color="label_color"),
        data=df[(df["population"] > SMALL_POP) & (df["population"] <= LARGE_POP)],
        size=7,
        fontface="bold",
    )
    + geom_text(
        aes(x="lon", y="lat", label="abbr"),
        data=df[df["population"] <= SMALL_POP],
        size=7,
        fontface="bold",
        color=INK,
        hjust=0,
        nudge_x=1.0,
    )
    + scale_color_identity()
    # Annotation near Atlantic/Nordic highlighted cluster (IE/NO/DK area)
    + geom_text(
        aes(x="x", y="y"),
        data=pd.DataFrame({"x": [-9.0], "y": [61.5]}),
        label="Small nations,\nhighest wealth",
        size=8,
        color=INK_MUTED,
        fontface="italic",
        hjust=0,
    )
    + labs(title=title, subtitle="Bubble size = population  |  Color = GDP per capita  |  ★ = small but wealthy")
    + coord_cartesian(xlim=[-16, 33], ylim=[lat_min, lat_max])
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=title_size, face="bold", color=INK),
        plot_subtitle=element_text(size=10, color=INK_MUTED),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        panel_border=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# Save PNG (3200×1800 px via scale=4) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
