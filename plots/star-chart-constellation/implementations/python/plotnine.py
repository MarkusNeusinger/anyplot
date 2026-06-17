"""anyplot.ai
star-chart-constellation: Star Chart with Constellations
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-06-16
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_alpha_continuous,
    scale_size_continuous,
    theme,
    theme_void,
)


# ── Theme-adaptive chrome (Imprint palette + tokens) ──────────────────────────
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — brand green is the FIRST (and primary) categorical series.
# Here it draws the constellation stick-figures, the chart's leading data layer.
BRAND = "#009E73"
# Stars themselves are rendered in the theme ink: dark engraving on a cream
# parchment atlas (light), pale warm-white on a night sky (dark). Magnitude is
# encoded by size + opacity, never colour — keeping Imprint identity intact.
STAR_COLOR = INK
GRID_COLOR = INK

# ── Data — real star positions (RA in hours, Dec in degrees) ──────────────────
np.random.seed(42)

stars_raw = [
    # Orion
    ("Betelgeuse", 5.92, 7.41, 0.42, "Ori"),
    ("Rigel", 5.24, -8.20, 0.13, "Ori"),
    ("Bellatrix", 5.42, 6.35, 1.64, "Ori"),
    ("Mintaka", 5.53, -0.30, 2.23, "Ori"),
    ("Alnilam", 5.60, -1.20, 1.69, "Ori"),
    ("Alnitak", 5.68, -1.94, 1.77, "Ori"),
    ("Saiph", 5.80, -9.67, 2.09, "Ori"),
    # Ursa Major (Big Dipper)
    ("Dubhe", 11.06, 61.75, 1.79, "UMa"),
    ("Merak", 11.02, 56.38, 2.37, "UMa"),
    ("Phecda", 11.90, 53.69, 2.44, "UMa"),
    ("Megrez", 12.26, 57.03, 3.31, "UMa"),
    ("Alioth", 12.90, 55.96, 1.77, "UMa"),
    ("Mizar", 13.40, 54.93, 2.27, "UMa"),
    ("Alkaid", 13.79, 49.31, 1.86, "UMa"),
    # Cassiopeia
    ("Schedar", 0.68, 56.54, 2.23, "Cas"),
    ("Caph", 0.15, 59.15, 2.27, "Cas"),
    ("Gamma Cas", 0.95, 60.72, 2.47, "Cas"),
    ("Ruchbah", 1.36, 60.24, 2.68, "Cas"),
    ("Segin", 1.91, 63.67, 3.37, "Cas"),
    # Leo
    ("Regulus", 10.14, 11.97, 1.35, "Leo"),
    ("Denebola", 11.82, 14.57, 2.14, "Leo"),
    ("Algieba", 10.33, 19.84, 2.08, "Leo"),
    ("Zosma", 11.24, 20.52, 2.56, "Leo"),
    ("Chertan", 11.24, 15.43, 3.34, "Leo"),
    # Cygnus
    ("Deneb", 20.69, 45.28, 1.25, "Cyg"),
    ("Sadr", 20.37, 40.26, 2.20, "Cyg"),
    ("Gienah Cyg", 20.77, 33.97, 2.46, "Cyg"),
    ("Albireo", 19.51, 27.96, 3.08, "Cyg"),
    ("Delta Cyg", 19.75, 45.13, 2.87, "Cyg"),
    # Scorpius
    ("Antares", 16.49, -26.43, 0.96, "Sco"),
    ("Shaula", 17.56, -37.10, 1.63, "Sco"),
    ("Sargas", 17.62, -42.99, 1.87, "Sco"),
    ("Dschubba", 16.01, -22.62, 2.32, "Sco"),
    ("Graffias", 16.09, -19.81, 2.62, "Sco"),
    ("Wei", 16.84, -34.29, 2.29, "Sco"),
    ("Lesath", 17.53, -37.29, 2.69, "Sco"),
    # Gemini
    ("Pollux", 7.76, 28.03, 1.14, "Gem"),
    ("Castor", 7.58, 31.89, 1.58, "Gem"),
    ("Alhena", 6.63, 16.40, 1.93, "Gem"),
    ("Tejat", 6.38, 22.51, 2.88, "Gem"),
    ("Mebsuta", 6.73, 25.13, 3.06, "Gem"),
    # Lyra
    ("Vega", 18.62, 38.78, 0.03, "Lyr"),
    ("Sheliak", 18.83, 33.36, 3.45, "Lyr"),
    ("Sulafat", 18.98, 32.69, 3.24, "Lyr"),
    # Aquila
    ("Altair", 19.85, 8.87, 0.77, "Aql"),
    ("Tarazed", 19.77, 10.61, 2.72, "Aql"),
    ("Alshain", 19.92, 6.41, 3.71, "Aql"),
    # Taurus
    ("Aldebaran", 4.60, 16.51, 0.85, "Tau"),
    ("Elnath", 5.44, 28.61, 1.65, "Tau"),
    ("Alcyone", 3.79, 24.11, 2.87, "Tau"),
    ("Tianguan", 5.63, 21.14, 3.00, "Tau"),
    # Canis Major
    ("Sirius", 6.75, -16.72, -1.46, "CMa"),
    ("Adhara", 6.98, -28.97, 1.50, "CMa"),
    ("Wezen", 7.14, -26.39, 1.84, "CMa"),
    ("Mirzam", 6.38, -17.96, 1.98, "CMa"),
    ("Aludra", 7.40, -29.30, 2.45, "CMa"),
    # Perseus
    ("Mirfak", 3.41, 49.86, 1.79, "Per"),
    ("Algol", 3.14, 40.96, 2.12, "Per"),
    ("Zeta Per", 3.90, 31.88, 2.85, "Per"),
    ("Epsilon Per", 3.96, 40.01, 2.89, "Per"),
    ("Delta Per", 3.72, 47.79, 3.01, "Per"),
    # Andromeda
    ("Alpheratz", 0.14, 29.09, 2.06, "And"),
    ("Mirach", 1.16, 35.62, 2.05, "And"),
    ("Almach", 2.06, 42.33, 2.17, "And"),
    # Bootes
    ("Arcturus", 14.26, 19.18, -0.05, "Boo"),
    ("Izar", 14.75, 27.07, 2.70, "Boo"),
    ("Muphrid", 13.91, 18.40, 2.68, "Boo"),
    ("Nekkar", 15.03, 40.39, 3.58, "Boo"),
    # Sagittarius (teapot asterism)
    ("Kaus Australis", 18.40, -34.38, 1.85, "Sgr"),
    ("Nunki", 18.92, -26.30, 2.02, "Sgr"),
    ("Ascella", 19.04, -29.88, 2.59, "Sgr"),
    ("Kaus Media", 18.35, -29.83, 2.70, "Sgr"),
    ("Kaus Borealis", 18.47, -25.42, 2.81, "Sgr"),
    # Auriga
    ("Capella", 5.27, 46.00, 0.08, "Aur"),
    ("Menkalinan", 5.99, 44.95, 1.90, "Aur"),
    ("Theta Aur", 5.99, 37.21, 2.62, "Aur"),
    ("Iota Aur", 4.95, 33.17, 2.69, "Aur"),
    # Corona Borealis
    ("Alphecca", 15.58, 26.71, 2.23, "CrB"),
    ("Nusakan", 15.46, 29.11, 3.68, "CrB"),
    ("Gamma CrB", 15.71, 26.30, 3.84, "CrB"),
    # Canis Minor
    ("Procyon", 7.66, 5.22, 0.34, "CMi"),
    ("Gomeisa", 7.45, 8.29, 2.90, "CMi"),
    # Pegasus (Great Square)
    ("Markab", 23.08, 15.21, 2.49, "Peg"),
    ("Scheat", 23.06, 28.08, 2.42, "Peg"),
    ("Algenib", 0.22, 15.19, 2.83, "Peg"),
    # Virgo
    ("Spica", 13.42, -11.16, 0.97, "Vir"),
    ("Porrima", 12.69, -1.45, 2.74, "Vir"),
    ("Vindemiatrix", 13.04, 10.96, 2.83, "Vir"),
    # Ursa Minor
    ("Polaris", 2.53, 89.26, 1.98, "UMi"),
    ("Kochab", 14.85, 74.16, 2.08, "UMi"),
    ("Pherkad", 15.35, 71.83, 3.00, "UMi"),
    # Draco
    ("Eltanin", 17.94, 51.49, 2.23, "Dra"),
    ("Rastaban", 17.51, 52.30, 2.79, "Dra"),
    ("Thuban", 14.07, 64.38, 3.65, "Dra"),
]

# Constellation edges (pairs of star names) — drawn as stick-figure lines
edges_raw = [
    ("Betelgeuse", "Bellatrix"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Betelgeuse", "Alnilam"),
    ("Rigel", "Alnitak"),
    ("Rigel", "Saiph"),
    ("Saiph", "Alnitak"),
    ("Dubhe", "Merak"),
    ("Merak", "Phecda"),
    ("Phecda", "Megrez"),
    ("Megrez", "Alioth"),
    ("Alioth", "Mizar"),
    ("Mizar", "Alkaid"),
    ("Megrez", "Dubhe"),
    ("Caph", "Schedar"),
    ("Schedar", "Gamma Cas"),
    ("Gamma Cas", "Ruchbah"),
    ("Ruchbah", "Segin"),
    ("Regulus", "Chertan"),
    ("Chertan", "Denebola"),
    ("Denebola", "Zosma"),
    ("Zosma", "Algieba"),
    ("Algieba", "Regulus"),
    ("Deneb", "Sadr"),
    ("Sadr", "Gienah Cyg"),
    ("Sadr", "Delta Cyg"),
    ("Sadr", "Albireo"),
    ("Graffias", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Wei"),
    ("Wei", "Shaula"),
    ("Shaula", "Lesath"),
    ("Wei", "Sargas"),
    ("Castor", "Pollux"),
    ("Castor", "Tejat"),
    ("Pollux", "Alhena"),
    ("Tejat", "Mebsuta"),
    ("Mebsuta", "Castor"),
    ("Vega", "Sheliak"),
    ("Sheliak", "Sulafat"),
    ("Sulafat", "Vega"),
    ("Altair", "Tarazed"),
    ("Altair", "Alshain"),
    ("Aldebaran", "Elnath"),
    ("Aldebaran", "Alcyone"),
    ("Elnath", "Tianguan"),
    ("Sirius", "Mirzam"),
    ("Sirius", "Adhara"),
    ("Adhara", "Wezen"),
    ("Wezen", "Aludra"),
    ("Mirfak", "Delta Per"),
    ("Mirfak", "Epsilon Per"),
    ("Epsilon Per", "Zeta Per"),
    ("Mirfak", "Algol"),
    ("Alpheratz", "Mirach"),
    ("Mirach", "Almach"),
    ("Arcturus", "Izar"),
    ("Arcturus", "Muphrid"),
    ("Izar", "Nekkar"),
    ("Kaus Australis", "Kaus Media"),
    ("Kaus Media", "Kaus Borealis"),
    ("Kaus Borealis", "Nunki"),
    ("Nunki", "Ascella"),
    ("Ascella", "Kaus Australis"),
    ("Capella", "Menkalinan"),
    ("Menkalinan", "Theta Aur"),
    ("Theta Aur", "Iota Aur"),
    ("Iota Aur", "Capella"),
    ("Nusakan", "Alphecca"),
    ("Alphecca", "Gamma CrB"),
    ("Procyon", "Gomeisa"),
    ("Markab", "Scheat"),
    ("Markab", "Algenib"),
    ("Scheat", "Alpheratz"),
    ("Algenib", "Alpheratz"),
    ("Spica", "Porrima"),
    ("Porrima", "Vindemiatrix"),
    ("Polaris", "Kochab"),
    ("Kochab", "Pherkad"),
    ("Eltanin", "Rastaban"),
    ("Rastaban", "Thuban"),
]

# Fainter background stars to give the sky depth (mag 3.5–5.5)
n_bg = 230
bg_ra = np.random.uniform(0, 24, n_bg)
bg_dec = np.random.uniform(-50, 70, n_bg)
bg_mag = np.random.uniform(3.5, 5.5, n_bg)
bg_stars = [(f"BG{i}", bg_ra[i], bg_dec[i], bg_mag[i], "bg") for i in range(n_bg)]

all_stars = stars_raw + bg_stars

star_names = [s[0] for s in all_stars]
ra_hours = np.array([s[1] for s in all_stars])
dec_deg = np.array([s[2] for s in all_stars])
magnitudes = np.array([s[3] for s in all_stars])
constellations = [s[4] for s in all_stars]

# ── Stereographic projection (centred on RA=12h, Dec=30° — northern sky) ──────
ra_rad = np.radians(ra_hours * 15.0)
dec_rad = np.radians(dec_deg)
ra0 = np.radians(180.0)
dec0 = np.radians(30.0)


def project(ra_r, dec_r):
    """Stereographic projection; x flipped so RA increases right-to-left."""
    cos_c = np.sin(dec0) * np.sin(dec_r) + np.cos(dec0) * np.cos(dec_r) * np.cos(ra_r - ra0)
    k = 2.0 / (1.0 + cos_c)
    x = -k * np.cos(dec_r) * np.sin(ra_r - ra0)
    y = k * (np.cos(dec0) * np.sin(dec_r) - np.sin(dec0) * np.cos(dec_r) * np.cos(ra_r - ra0))
    return x, y


proj_x, proj_y = project(ra_rad, dec_rad)

df_stars = pd.DataFrame(
    {"x": proj_x, "y": proj_y, "magnitude": magnitudes, "name": star_names, "constellation": constellations}
)

# Clip to the circular sky boundary
radius_limit = 3.5
df_stars = df_stars[np.hypot(df_stars["x"], df_stars["y"]) < radius_limit].copy()

# ── Constellation stick-figure segments ───────────────────────────────────────
star_lookup = {row["name"]: (row["x"], row["y"]) for _, row in df_stars.iterrows()}
edge_data = [
    {"x": star_lookup[a][0], "y": star_lookup[a][1], "xend": star_lookup[b][0], "yend": star_lookup[b][1]}
    for a, b in edges_raw
    if a in star_lookup and b in star_lookup
]
df_edges = pd.DataFrame(edge_data)

# ── Constellation name labels at group centroids (with manual de-clutter) ─────
named_stars = df_stars[df_stars["constellation"] != "bg"].copy()
constellation_names = {
    "Ori": "ORION",
    "UMa": "URSA MAJOR",
    "Cas": "CASSIOPEIA",
    "Leo": "LEO",
    "Cyg": "CYGNUS",
    "Sco": "SCORPIUS",
    "Gem": "GEMINI",
    "Lyr": "LYRA",
    "Aql": "AQUILA",
    "Tau": "TAURUS",
    "CMa": "CANIS MAJOR",
    "Per": "PERSEUS",
    "And": "ANDROMEDA",
    "Boo": "BOÖTES",
    "Sgr": "SAGITTARIUS",
    "Aur": "AURIGA",
    "CrB": "COR. BOREALIS",
    "CMi": "CANIS MINOR",
    "Peg": "PEGASUS",
    "Vir": "VIRGO",
    "UMi": "URSA MINOR",
    "Dra": "DRACO",
}
# (dx, dy) nudges to keep labels off their stars and away from each other,
# especially the crowded circumpolar core (UMa / UMi / Dra / Cas / Per / Aur).
label_nudge = {
    "Ori": (0.14, -0.34),
    "UMa": (-0.28, 0.52),
    "Cas": (-0.30, 0.46),
    "Leo": (0.05, -0.42),
    "Cyg": (0.48, 0.10),
    "Sco": (0.00, -0.44),
    "Gem": (0.34, -0.36),
    "Lyr": (-0.46, -0.08),
    "Aql": (0.46, 0.00),
    "Tau": (-0.12, -0.44),
    "CMa": (0.00, -0.42),
    "Per": (0.54, 0.06),
    "And": (-0.10, -0.46),
    "Boo": (-0.48, -0.10),
    "Sgr": (0.00, -0.42),
    "Aur": (-0.48, -0.54),
    "CrB": (0.40, 0.12),
    "CMi": (0.36, -0.30),
    "Peg": (-0.32, -0.32),
    "Vir": (0.05, -0.42),
    "UMi": (0.56, 0.46),
    "Dra": (-0.58, 0.36),
}
label_data = []
for abbr, full_name in constellation_names.items():
    group = named_stars[named_stars["constellation"] == abbr]
    if len(group) > 0:
        dx, dy = label_nudge.get(abbr, (0.0, 0.0))
        label_data.append({"x": group["x"].mean() + dx, "y": group["y"].mean() + dy, "label": full_name})
df_labels = pd.DataFrame(label_data)

# ── Coordinate grid: declination rings + RA meridians ─────────────────────────
grid_segs = []
for dec_grid in [0, 20, 40, 60]:
    theta = np.linspace(0, 2 * np.pi, 240)
    gx, gy = project(theta, np.full_like(theta, np.radians(dec_grid)))
    bad = np.hypot(gx, gy) >= radius_limit
    gx[bad] = np.nan
    for i in range(len(theta) - 1):
        if not (np.isnan(gx[i]) or np.isnan(gx[i + 1])):
            grid_segs.append({"x": gx[i], "y": gy[i], "xend": gx[i + 1], "yend": gy[i + 1]})
for ra_h in range(0, 24, 3):
    dec_range = np.linspace(np.radians(-50), np.radians(70), 160)
    gx, gy = project(np.full_like(dec_range, np.radians(ra_h * 15.0)), dec_range)
    bad = np.hypot(gx, gy) >= radius_limit
    gx[bad] = np.nan
    for i in range(len(dec_range) - 1):
        if not (np.isnan(gx[i]) or np.isnan(gx[i + 1])):
            grid_segs.append({"x": gx[i], "y": gy[i], "xend": gx[i + 1], "yend": gy[i + 1]})
df_grid = pd.DataFrame(grid_segs)

# RA tick labels along the Dec=-12° parallel
ra_ticks = []
for ra_h in range(0, 24, 3):
    tx, ty = project(np.radians(ra_h * 15.0), np.radians(-12))
    if np.hypot(tx, ty) < radius_limit - 0.1:
        ra_ticks.append({"x": tx, "y": ty - 0.16, "label": f"{ra_h}h"})
df_ra_ticks = pd.DataFrame(ra_ticks)

# Dec tick labels along the RA=3h meridian
dec_ticks = []
for dec_val in [0, 20, 40, 60]:
    tx, ty = project(np.radians(3 * 15.0), np.radians(dec_val))
    if np.hypot(tx, ty) < radius_limit - 0.1:
        dec_ticks.append({"x": tx + 0.16, "y": ty, "label": f"{dec_val}°"})
df_dec_ticks = pd.DataFrame(dec_ticks)

# ── Title (mandated format; fontsize scales if it ever runs long) ─────────────
TITLE = "star-chart-constellation · python · plotnine · anyplot.ai"
title_size = round(13 * min(1.0, 67 / len(TITLE)))

# ── Plot ──────────────────────────────────────────────────────────────────────
plot = (
    ggplot()
    # Coordinate grid (very subtle structural layer)
    + geom_segment(df_grid, aes(x="x", y="y", xend="xend", yend="yend"), color=GRID_COLOR, size=0.3, alpha=0.14)
    # Constellation stick-figures — Imprint brand green, the leading data series
    + geom_segment(df_edges, aes(x="x", y="y", xend="xend", yend="yend"), color=BRAND, size=0.7, alpha=0.6)
    # Stars — magnitude drives both size and opacity (brighter = bigger, opaque)
    + geom_point(df_stars, aes(x="x", y="y", size="magnitude", alpha="magnitude"), color=STAR_COLOR, stroke=0)
    + scale_size_continuous(name="Apparent\nmagnitude", range=(5.0, 0.4), breaks=[0, 1, 2, 3, 4, 5])
    + scale_alpha_continuous(name="Apparent\nmagnitude", range=(1.0, 0.45), breaks=[0, 1, 2, 3, 4, 5])
    + guides(size=guide_legend(), alpha=guide_legend())
    # Constellation names
    + geom_text(
        df_labels,
        aes(x="x", y="y", label="label"),
        color=INK_SOFT,
        size=7,
        alpha=0.9,
        fontstyle="italic",
        fontweight="bold",
    )
    # RA / Dec tick labels
    + geom_text(df_ra_ticks, aes(x="x", y="y", label="label"), color=INK_MUTED, size=6)
    + geom_text(df_dec_ticks, aes(x="x", y="y", label="label"), color=INK_MUTED, size=6, ha="left")
    + coord_fixed(
        ratio=1, xlim=(-radius_limit - 0.2, radius_limit + 0.2), ylim=(-radius_limit - 0.2, radius_limit + 0.2)
    )
    + labs(title=TITLE)
    + theme_void()
    + theme(
        figure_size=(6, 6),
        dpi=400,
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(color=INK_SOFT, size=title_size, ha="center", va="top", margin={"b": 12}),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_MUTED),
        legend_title=element_text(color=INK, size=9, ha="left"),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_key=element_blank(),
        plot_margin=0.01,
    )
)

# ── Save (square 2400×2400 px) ────────────────────────────────────────────────
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
