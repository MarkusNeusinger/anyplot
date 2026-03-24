""" pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_alpha_identity,
    scale_color_identity,
    scale_size_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)


# Data — real star positions (RA in hours, Dec in degrees) for prominent constellations
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

# Constellation edges (pairs of star names)
edges_raw = [
    # Orion
    ("Betelgeuse", "Bellatrix"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Betelgeuse", "Alnilam"),
    ("Rigel", "Alnitak"),
    ("Rigel", "Saiph"),
    ("Saiph", "Alnitak"),
    # Ursa Major
    ("Dubhe", "Merak"),
    ("Merak", "Phecda"),
    ("Phecda", "Megrez"),
    ("Megrez", "Alioth"),
    ("Alioth", "Mizar"),
    ("Mizar", "Alkaid"),
    ("Megrez", "Dubhe"),
    # Cassiopeia
    ("Caph", "Schedar"),
    ("Schedar", "Gamma Cas"),
    ("Gamma Cas", "Ruchbah"),
    ("Ruchbah", "Segin"),
    # Leo
    ("Regulus", "Chertan"),
    ("Chertan", "Denebola"),
    ("Denebola", "Zosma"),
    ("Zosma", "Algieba"),
    ("Algieba", "Regulus"),
    # Cygnus
    ("Deneb", "Sadr"),
    ("Sadr", "Gienah Cyg"),
    ("Sadr", "Delta Cyg"),
    ("Sadr", "Albireo"),
    # Scorpius
    ("Graffias", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Wei"),
    ("Wei", "Shaula"),
    ("Shaula", "Lesath"),
    ("Wei", "Sargas"),
    # Gemini
    ("Castor", "Pollux"),
    ("Castor", "Tejat"),
    ("Pollux", "Alhena"),
    ("Tejat", "Mebsuta"),
    ("Mebsuta", "Castor"),
    # Lyra
    ("Vega", "Sheliak"),
    ("Sheliak", "Sulafat"),
    ("Sulafat", "Vega"),
    # Aquila
    ("Altair", "Tarazed"),
    ("Altair", "Alshain"),
    # Taurus
    ("Aldebaran", "Elnath"),
    ("Aldebaran", "Alcyone"),
    ("Elnath", "Tianguan"),
    # Canis Major
    ("Sirius", "Mirzam"),
    ("Sirius", "Adhara"),
    ("Adhara", "Wezen"),
    ("Wezen", "Aludra"),
    # Perseus
    ("Mirfak", "Delta Per"),
    ("Mirfak", "Epsilon Per"),
    ("Epsilon Per", "Zeta Per"),
    ("Mirfak", "Algol"),
    # Andromeda
    ("Alpheratz", "Mirach"),
    ("Mirach", "Almach"),
    # Bootes
    ("Arcturus", "Izar"),
    ("Arcturus", "Muphrid"),
    ("Izar", "Nekkar"),
    # Sagittarius
    ("Kaus Australis", "Kaus Media"),
    ("Kaus Media", "Kaus Borealis"),
    ("Kaus Borealis", "Nunki"),
    ("Nunki", "Ascella"),
    ("Ascella", "Kaus Australis"),
    # Auriga
    ("Capella", "Menkalinan"),
    ("Menkalinan", "Theta Aur"),
    ("Theta Aur", "Iota Aur"),
    ("Iota Aur", "Capella"),
    # Corona Borealis
    ("Nusakan", "Alphecca"),
    ("Alphecca", "Gamma CrB"),
    # Canis Minor
    ("Procyon", "Gomeisa"),
    # Pegasus
    ("Markab", "Scheat"),
    ("Markab", "Algenib"),
    ("Scheat", "Alpheratz"),
    ("Algenib", "Alpheratz"),
    # Virgo
    ("Spica", "Porrima"),
    ("Porrima", "Vindemiatrix"),
    # Ursa Minor
    ("Polaris", "Kochab"),
    ("Kochab", "Pherkad"),
    # Draco
    ("Eltanin", "Rastaban"),
    ("Rastaban", "Thuban"),
]

# Add fainter background stars
n_bg = 250
bg_ra = np.random.uniform(0, 24, n_bg)
bg_dec = np.random.uniform(-50, 70, n_bg)
bg_mag = np.random.uniform(3.5, 5.5, n_bg)
bg_stars = [(f"BG{i}", bg_ra[i], bg_dec[i], bg_mag[i], "bg") for i in range(n_bg)]

all_stars = stars_raw + bg_stars

# Build star dataframe
star_names = [s[0] for s in all_stars]
ra_hours = np.array([s[1] for s in all_stars])
dec_deg = np.array([s[2] for s in all_stars])
magnitudes = np.array([s[3] for s in all_stars])
constellations = [s[4] for s in all_stars]

# Convert RA hours to degrees, then to radians for projection
ra_deg = ra_hours * 15.0
ra_rad = np.radians(ra_deg)
dec_rad = np.radians(dec_deg)

# Stereographic projection (centered on RA=12h, Dec=30° for northern sky view)
ra0 = np.radians(180.0)
dec0 = np.radians(30.0)

# Stereographic projection formulas
cos_c = np.sin(dec0) * np.sin(dec_rad) + np.cos(dec0) * np.cos(dec_rad) * np.cos(ra_rad - ra0)
k = 2.0 / (1.0 + cos_c)
proj_x = k * np.cos(dec_rad) * np.sin(ra_rad - ra0)
proj_y = k * (np.cos(dec0) * np.sin(dec_rad) - np.sin(dec0) * np.cos(dec_rad) * np.cos(ra_rad - ra0))

# Flip x so RA increases right-to-left (as seen on sky)
proj_x = -proj_x

# Size mapping: brighter stars (lower mag) get larger points
max_mag = 5.5
min_mag = -1.5
star_sizes = np.clip((max_mag - magnitudes) / (max_mag - min_mag), 0.05, 1.0)
star_sizes = star_sizes**1.5 * 10.0 + 0.4

# Star colors based on magnitude (brighter = more yellow-white, dimmer = blueish-white)
star_colors = []
for mag in magnitudes:
    if mag < 0.5:
        star_colors.append("#FFFDE7")
    elif mag < 1.5:
        star_colors.append("#FFF9C4")
    elif mag < 2.5:
        star_colors.append("#E8EAF6")
    else:
        star_colors.append("#B0BEC5")

# Alpha based on magnitude (brighter stars more opaque)
star_alphas = np.clip(0.4 + 0.6 * (max_mag - magnitudes) / (max_mag - min_mag), 0.3, 0.95)

df_stars = pd.DataFrame(
    {
        "x": proj_x,
        "y": proj_y,
        "magnitude": magnitudes,
        "size": star_sizes,
        "color": star_colors,
        "alpha": star_alphas,
        "name": star_names,
        "constellation": constellations,
    }
)

# Filter to visible region (within projection circle)
radius_limit = 3.5
df_stars = df_stars[np.sqrt(df_stars["x"] ** 2 + df_stars["y"] ** 2) < radius_limit].copy()

# Build edges dataframe
star_lookup = {row["name"]: (row["x"], row["y"]) for _, row in df_stars.iterrows()}
edge_data = []
for s1, s2 in edges_raw:
    if s1 in star_lookup and s2 in star_lookup:
        x1, y1 = star_lookup[s1]
        x2, y2 = star_lookup[s2]
        edge_data.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

df_edges = pd.DataFrame(edge_data)

# Constellation labels at centroid of each group with manual nudges
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
# Manual nudges (dx, dy) to prevent label overlap
label_nudge = {
    "Cyg": (0.30, 0.15),
    "Lyr": (-0.30, -0.10),
    "UMa": (0.0, 0.15),
    "Gem": (0.15, -0.10),
    "Aql": (0.25, 0.0),
    "CMi": (-0.30, 0.0),
    "CrB": (0.0, 0.10),
    "And": (0.0, -0.10),
    "Per": (0.20, 0.10),
    "Boo": (-0.20, 0.0),
    "Vir": (0.0, -0.10),
    "Dra": (-0.30, -0.10),
    "UMi": (0.20, 0.10),
    "Peg": (0.0, -0.08),
    "Ori": (0.15, 0.0),
    "Tau": (0.0, 0.10),
    "Aur": (0.20, 0.10),
}
label_data = []
for abbr, full_name in constellation_names.items():
    group = named_stars[named_stars["constellation"] == abbr]
    if len(group) > 0:
        dx, dy = label_nudge.get(abbr, (0.0, 0.0))
        label_data.append({"x": group["x"].mean() + dx, "y": group["y"].min() - 0.18 + dy, "label": full_name})

df_labels = pd.DataFrame(label_data)

# Coordinate grid circles (declination rings)
grid_circles = []
for dec_grid in [0, 20, 40, 60]:
    theta = np.linspace(0, 2 * np.pi, 200)
    dec_g = np.radians(dec_grid)
    cos_c_g = np.sin(dec0) * np.sin(dec_g) + np.cos(dec0) * np.cos(dec_g) * np.cos(theta)
    k_g = 2.0 / (1.0 + cos_c_g)
    gx = -k_g * np.cos(dec_g) * np.sin(theta)
    gy = k_g * (np.cos(dec0) * np.sin(dec_g) - np.sin(dec0) * np.cos(dec_g) * np.cos(theta))
    mask = np.sqrt(gx**2 + gy**2) < radius_limit
    gx[~mask] = np.nan
    gy[~mask] = np.nan
    for i in range(len(theta) - 1):
        if not (np.isnan(gx[i]) or np.isnan(gx[i + 1])):
            grid_circles.append({"x": gx[i], "y": gy[i], "xend": gx[i + 1], "yend": gy[i + 1]})

df_grid = pd.DataFrame(grid_circles) if grid_circles else pd.DataFrame(columns=["x", "y", "xend", "yend"])

# RA grid lines (meridians)
ra_grid_segs = []
for ra_h in range(0, 24, 3):
    ra_g = np.radians(ra_h * 15.0)
    dec_range = np.linspace(np.radians(-50), np.radians(70), 150)
    cos_c_g = np.sin(dec0) * np.sin(dec_range) + np.cos(dec0) * np.cos(dec_range) * np.cos(ra_g - ra0)
    k_g = 2.0 / (1.0 + cos_c_g)
    gx = -k_g * np.cos(dec_range) * np.sin(ra_g - ra0)
    gy = k_g * (np.cos(dec0) * np.sin(dec_range) - np.sin(dec0) * np.cos(dec_range) * np.cos(ra_g - ra0))
    mask = np.sqrt(gx**2 + gy**2) < radius_limit
    gx[~mask] = np.nan
    gy[~mask] = np.nan
    for i in range(len(dec_range) - 1):
        if not (np.isnan(gx[i]) or np.isnan(gx[i + 1])):
            ra_grid_segs.append({"x": gx[i], "y": gy[i], "xend": gx[i + 1], "yend": gy[i + 1]})

df_ra_grid = pd.DataFrame(ra_grid_segs) if ra_grid_segs else pd.DataFrame(columns=["x", "y", "xend", "yend"])

# Combine all grid segments
df_all_grid = pd.concat([df_grid, df_ra_grid], ignore_index=True)

# RA tick labels at Dec=-10° for better separation from constellation names
ra_tick_labels = []
for ra_h in range(0, 24, 3):
    ra_g = np.radians(ra_h * 15.0)
    dec_g = np.radians(-10)
    cos_c_t = np.sin(dec0) * np.sin(dec_g) + np.cos(dec0) * np.cos(dec_g) * np.cos(ra_g - ra0)
    k_t = 2.0 / (1.0 + cos_c_t)
    tx = -k_t * np.cos(dec_g) * np.sin(ra_g - ra0)
    ty = k_t * (np.cos(dec0) * np.sin(dec_g) - np.sin(dec0) * np.cos(dec_g) * np.cos(ra_g - ra0))
    if np.sqrt(tx**2 + ty**2) < radius_limit - 0.15:
        ra_tick_labels.append({"x": tx, "y": ty - 0.15, "label": f"{ra_h}h"})

df_ra_ticks = pd.DataFrame(ra_tick_labels)

# Dec tick labels along RA=3h meridian (offset from 0h to avoid overlaps)
dec_tick_labels = []
for dec_val in [0, 20, 40, 60]:
    ra_g = np.radians(3 * 15.0)
    dec_g = np.radians(dec_val)
    cos_c_t = np.sin(dec0) * np.sin(dec_g) + np.cos(dec0) * np.cos(dec_g) * np.cos(ra_g - ra0)
    k_t = 2.0 / (1.0 + cos_c_t)
    tx = -k_t * np.cos(dec_g) * np.sin(ra_g - ra0)
    ty = k_t * (np.cos(dec0) * np.sin(dec_g) - np.sin(dec0) * np.cos(dec_g) * np.cos(ra_g - ra0))
    if np.sqrt(tx**2 + ty**2) < radius_limit - 0.15:
        dec_tick_labels.append({"x": tx + 0.15, "y": ty, "label": f"{dec_val}°"})

df_dec_ticks = pd.DataFrame(dec_tick_labels)

# Magnitude legend data
legend_mags = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
legend_x_base = radius_limit - 0.5
legend_y_base = -radius_limit + 1.4
legend_stars = []
legend_labels_list = []
for i, lm in enumerate(legend_mags):
    ly = legend_y_base + i * 0.32
    lsize = np.clip((max_mag - lm) / (max_mag - min_mag), 0.05, 1.0) ** 1.5 * 10.0 + 0.4
    lcolor = "#FFFDE7" if lm < 0.5 else "#FFF9C4" if lm < 1.5 else "#E8EAF6" if lm < 2.5 else "#B0BEC5"
    legend_stars.append({"x": legend_x_base, "y": ly, "size": lsize, "color": lcolor})
    legend_labels_list.append({"x": legend_x_base + 0.28, "y": ly, "label": f"mag {lm:.0f}"})

df_legend_stars = pd.DataFrame(legend_stars)
df_legend_labels = pd.DataFrame(legend_labels_list)

# Plot
plot = (
    ggplot()
    # Coordinate grid (very subtle)
    + geom_segment(
        data=df_all_grid, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#1a2744", size=0.3, alpha=0.5
    )
    # Constellation stick-figure lines
    + geom_segment(
        data=df_edges, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#5580b0", size=0.9, alpha=0.65
    )
    # Stars
    + geom_point(data=df_stars, mapping=aes(x="x", y="y", size="size", color="color", alpha="alpha"))
    + scale_size_identity()
    + scale_color_identity()
    + scale_alpha_identity()
    # Constellation names
    + geom_text(
        data=df_labels,
        mapping=aes(x="x", y="y", label="label"),
        color="#7a9cca",
        size=14,
        alpha=0.85,
        fontstyle="italic",
    )
    # RA tick labels
    + geom_text(data=df_ra_ticks, mapping=aes(x="x", y="y", label="label"), color="#5a7a9a", size=12, alpha=0.8)
    # Dec tick labels
    + geom_text(
        data=df_dec_ticks, mapping=aes(x="x", y="y", label="label"), color="#5a7a9a", size=12, alpha=0.8, ha="left"
    )
    # Magnitude legend points
    + geom_point(data=df_legend_stars, mapping=aes(x="x", y="y", size="size", color="color"), alpha=0.9)
    # Magnitude legend labels
    + geom_text(
        data=df_legend_labels, mapping=aes(x="x", y="y", label="label"), color="#8899bb", size=11, ha="left", alpha=0.85
    )
    # Magnitude legend title
    + annotate(
        "text",
        x=legend_x_base,
        y=legend_y_base - 0.28,
        label="Magnitude",
        color="#99aabb",
        size=12,
        ha="center",
        fontweight="bold",
    )
    # Title
    + annotate(
        "text",
        x=0,
        y=-radius_limit + 0.05,
        label="star-chart-constellation · plotnine · pyplots.ai",
        color="#8899aa",
        size=16,
        ha="center",
    )
    + coord_fixed(ratio=1)
    + xlim(-radius_limit - 0.3, radius_limit + 0.6)
    + ylim(-radius_limit - 0.1, radius_limit + 0.3)
    + labs(x="", y="")
    + theme_void()
    + theme(
        figure_size=(12, 12),
        plot_background=element_rect(fill="#060d1f", color="#060d1f"),
        panel_background=element_rect(fill="#060d1f", color="#060d1f"),
        text=element_text(color="#aabbcc", size=16),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
