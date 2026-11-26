"""anyplot.ai
star-chart-constellation: Star Chart with Constellations
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = INK  # used with low alpha for the RA/Dec coordinate grid

# Imprint palette position 1 — brand green, the single primary star series.
# A constant green reads on both the cream and near-black surfaces, unlike the
# pale-yellow of a literal night sky which would vanish on the light theme.
BRAND = "#009E73"

# Constants

HALO_MAGS = (0.6, 1.2)  # stars brighter than these get a strong / soft glow halo
DEC_RINGS = (60, 30, 0, -30)  # declination circles of the grid, in degrees
DEC_LABEL_BEARING = np.radians(9 * 15.0)  # Dec labels sit on the 9h meridian, a sparse stretch of sky
RA_STEP_H = 2  # one meridian and one rim label every 2 hours of right ascension
SKY_EDGE_DEC = -48.0  # declination of the circular sky boundary
RIM_LABEL_GAP = 11.0  # distance of the RA hour labels beyond the sky boundary
MERIDIAN_START = 22.0  # meridians start this far from the pole, clear of the Dec labels
CHAR_HALF_WIDTH = 1.2  # half the width of one letter of a constellation name, in projected degrees
LABEL_GAP = 16.0  # constellation names sit this far beyond the outermost star of their figure
PLOT_LIMIT = 160  # half-width of the square plot window in projected degrees
LEGEND_MAGS = [0, 2, 4]  # breaks of the magnitude key
MAG_LIMIT = 5.5  # faint end of the size scale
SIZE_RANGE = (1.0, 8.0)  # point size of the faintest and the brightest star
# Stars: brand green on the light page; pale yellow on the dark sky, as a night sky shows them
STAR = BRAND if THEME == "light" else "#FFF1B8"
CONSTELLATION_NAMES = {
    "Ori": "Orion",
    "UMa": "Ursa Major",
    "Cas": "Cassiopeia",
    "Leo": "Leo",
    "Cyg": "Cygnus",
    "Sco": "Scorpius",
    "Gem": "Gemini",
    "Lyr": "Lyra",
    "Aql": "Aquila",
    "CMa": "Canis Major",
    "Tau": "Taurus",
    "Boo": "Bootes",
    "Per": "Perseus",
}

# Columns: set these to your table's column names
STAR_ID = "star_id"  # role: star_id
RA = "ra"  # role: ra
DEC = "dec"  # role: dec
MAGNITUDE = "magnitude"  # role: magnitude
CONSTELLATION = "constellation"  # role: constellation
EDGES = "edges"  # role: edges

# Data: replace this block with your own table, for example df = pd.read_csv("stars.csv")
# One row per star: RA in hours, Dec in degrees, apparent magnitude, constellation
# abbreviation (empty for background stars) and the stars it is joined to, "|" separated.
stars_data = [
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
    ("Merak", 11.03, 56.38, 2.37, "UMa"),
    ("Phecda", 11.90, 53.69, 2.44, "UMa"),
    ("Megrez", 12.26, 57.03, 3.31, "UMa"),
    ("Alioth", 12.90, 55.96, 1.77, "UMa"),
    ("Mizar", 13.40, 54.93, 2.27, "UMa"),
    ("Alkaid", 13.79, 49.31, 1.86, "UMa"),
    # Cassiopeia
    ("Schedar", 0.68, 56.54, 2.23, "Cas"),
    ("Caph", 0.15, 59.15, 2.27, "Cas"),
    ("Gamma Cas", 0.95, 60.72, 2.47, "Cas"),
    ("Ruchbah", 1.43, 60.24, 2.68, "Cas"),
    ("Segin", 1.91, 63.67, 3.37, "Cas"),
    # Leo
    ("Regulus", 10.14, 11.97, 1.35, "Leo"),
    ("Denebola", 11.82, 14.57, 2.14, "Leo"),
    ("Algieba", 10.33, 19.84, 2.28, "Leo"),
    ("Zosma", 11.24, 20.52, 2.56, "Leo"),
    ("Chertan", 11.24, 15.43, 3.33, "Leo"),
    # Cygnus
    ("Deneb", 20.69, 45.28, 1.25, "Cyg"),
    ("Sadr", 20.37, 40.26, 2.23, "Cyg"),
    ("Gienah Cyg", 20.77, 33.97, 2.48, "Cyg"),
    ("Albireo", 19.51, 27.96, 3.08, "Cyg"),
    ("Fawaris", 19.75, 45.13, 2.87, "Cyg"),
    # Scorpius
    ("Antares", 16.49, -26.43, 1.09, "Sco"),
    ("Shaula", 17.56, -37.10, 1.63, "Sco"),
    ("Sargas", 17.62, -42.99, 1.87, "Sco"),
    ("Dschubba", 16.01, -22.62, 2.32, "Sco"),
    ("Graffias", 16.09, -19.81, 2.62, "Sco"),
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
    # Canis Major
    ("Sirius", 6.75, -16.72, -1.46, "CMa"),
    ("Adhara", 6.98, -28.97, 1.50, "CMa"),
    ("Wezen", 7.14, -26.39, 1.84, "CMa"),
    ("Mirzam", 6.38, -17.96, 1.98, "CMa"),
    ("Aludra", 7.40, -29.30, 2.45, "CMa"),
    # Taurus
    ("Aldebaran", 4.60, 16.51, 0.85, "Tau"),
    ("Elnath", 5.44, 28.61, 1.65, "Tau"),
    ("Alcyone", 3.79, 24.11, 2.87, "Tau"),
    ("Tianguan", 5.63, 21.14, 3.00, "Tau"),
    # Bootes
    ("Arcturus", 14.26, 19.18, -0.05, "Boo"),
    ("Izar", 14.75, 27.07, 2.37, "Boo"),
    ("Muphrid", 13.91, 18.40, 2.68, "Boo"),
    # Perseus
    ("Mirfak", 3.41, 49.86, 1.79, "Per"),
    ("Algol", 3.14, 40.96, 2.12, "Per"),
    ("Atik", 3.96, 31.88, 2.85, "Per"),
]

# Constellation stick-figure edges (pairs of star names)
edges = [
    ("Betelgeuse", "Bellatrix"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Betelgeuse", "Alnitak"),
    ("Bellatrix", "Rigel"),
    ("Betelgeuse", "Saiph"),
    ("Rigel", "Saiph"),
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
    ("Chertan", "Zosma"),
    ("Zosma", "Denebola"),
    ("Regulus", "Algieba"),
    ("Algieba", "Zosma"),
    ("Deneb", "Sadr"),
    ("Sadr", "Albireo"),
    ("Sadr", "Gienah Cyg"),
    ("Sadr", "Fawaris"),
    ("Graffias", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Shaula"),
    ("Shaula", "Lesath"),
    ("Shaula", "Sargas"),
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
    ("Sirius", "Mirzam"),
    ("Sirius", "Adhara"),
    ("Adhara", "Wezen"),
    ("Wezen", "Aludra"),
    ("Aldebaran", "Elnath"),
    ("Aldebaran", "Alcyone"),
    ("Elnath", "Tianguan"),
    ("Arcturus", "Izar"),
    ("Arcturus", "Muphrid"),
    ("Mirfak", "Algol"),
    ("Algol", "Atik"),
]
links = {}
for a, b in edges:
    links.setdefault(a, []).append(b)

# Further real catalogue stars (mag <= 5) that belong to no drawn stick figure
field_data = [
    ("Polaris", 2.53, 89.26, 1.98),
    ("Capella", 5.28, 46.00, 0.08),
    ("Procyon", 7.66, 5.22, 0.34),
    ("Spica", 13.42, -11.16, 0.97),
    ("Fomalhaut", 22.96, -29.62, 1.16),
    ("Hamal", 2.12, 23.46, 2.00),
    ("Alpheratz", 0.14, 29.09, 2.06),
    ("Mirach", 1.16, 35.62, 2.05),
    ("Diphda", 0.73, -17.99, 2.04),
    ("Menkar", 3.04, 4.09, 2.53),
    ("Almach", 2.07, 42.33, 2.26),
    ("Alphard", 9.46, -8.66, 1.98),
    ("Kochab", 14.85, 74.16, 2.08),
    ("Pherkad", 15.35, 71.83, 3.00),
    ("Alphecca", 15.58, 26.71, 2.23),
    ("Enif", 21.74, 9.88, 2.39),
    ("Markab", 23.08, 15.21, 2.49),
    ("Scheat", 23.06, 28.08, 2.42),
    ("Algenib", 0.22, 15.18, 2.83),
    ("Cor Caroli", 12.56, 38.32, 2.89),
    ("Eltanin", 17.94, 51.49, 2.23),
    ("Rasalhague", 17.58, 12.56, 2.08),
    ("Kaus Australis", 18.40, -34.38, 1.85),
    ("Nunki", 18.92, -26.30, 2.05),
    ("Rasalgethi", 17.24, 14.39, 3.50),
    ("Kornephoros", 16.50, 21.49, 2.77),
    ("Zeta Her", 16.69, 31.60, 2.81),
    ("Unukalhai", 15.74, 6.43, 2.65),
    ("Zubenelgenubi", 14.85, -16.04, 2.75),
    ("Zubeneschamali", 15.28, -9.38, 2.61),
    ("Vindemiatrix", 13.04, 10.96, 2.83),
    ("Alcor", 13.42, 54.99, 4.00),
    ("Thuban", 14.07, 64.38, 3.65),
    ("Sadalsuud", 21.53, -5.57, 2.91),
    ("Sadalmelik", 22.10, -0.32, 2.96),
    ("Deneb Algedi", 21.78, -16.13, 2.87),
    ("Algenubi", 9.76, 23.77, 2.98),
    ("Tania Australis", 10.37, 41.50, 3.05),
    ("Talitha", 8.99, 48.04, 3.14),
    ("Muscida", 8.50, 60.72, 3.36),
    ("Eta Cas", 0.82, 57.82, 3.44),
    ("Menkalinan", 5.99, 44.95, 1.90),
    ("Mahasim", 5.99, 37.21, 2.65),
    ("Hassaleh", 4.95, 33.17, 2.69),
    ("Ain", 4.48, 19.18, 3.50),
    ("Hatysa", 5.59, -5.91, 2.75),
    ("Meissa", 5.59, 9.93, 3.39),
    ("Cursa", 5.13, -5.09, 2.79),
    ("Arneb", 5.55, -17.82, 2.58),
    ("Nihal", 5.47, -20.76, 2.84),
    ("Phact", 5.66, -34.07, 2.64),
    ("Furud", 6.34, -30.06, 3.02),
    ("Menkent", 14.11, -36.37, 2.06),
    ("Mu Sco", 16.86, -38.05, 3.04),
    ("Epsilon Sco", 16.84, -34.29, 2.29),
    ("Kappa Sco", 17.71, -39.03, 2.41),
    ("Psi UMa", 11.16, 44.50, 3.01),
    ("Theta UMa", 9.55, 51.68, 3.17),
    ("Rastaban", 17.51, 52.30, 2.79),
    ("Alfirk", 21.48, 70.56, 3.23),
    ("Alderamin", 21.31, 62.59, 2.51),
    ("Errai", 23.66, 77.63, 3.21),
    ("Alpha Lac", 22.52, 50.28, 3.77),
    ("Algedi", 20.30, -12.54, 3.57),
    ("Dabih", 20.35, -14.78, 3.05),
    ("Zeta Cyg", 21.22, 30.23, 3.20),
    ("Delta And", 0.66, 30.86, 3.27),
    ("Beta Tri", 2.16, 34.99, 3.00),
    ("Alpha Tri", 1.88, 29.58, 3.40),
    ("Matar", 22.72, 30.22, 2.94),
    ("Homam", 22.69, 10.83, 3.40),
    ("Theta Peg", 22.17, 6.20, 3.53),
    ("Sheratan", 1.91, 20.81, 2.64),
    ("Mesarthim", 1.89, 19.29, 3.90),
    ("Gamma Cet", 2.72, 3.24, 3.47),
    ("Baten Kaitos", 1.86, -10.34, 3.73),
    ("Eta Cet", 1.14, -10.18, 3.45),
    ("Zaurak", 3.97, -13.51, 2.95),
    ("Delta Eri", 3.72, -9.76, 3.54),
    ("Epsilon Hya", 8.78, 6.42, 3.38),
    ("Zeta Hya", 8.92, 5.95, 3.11),
    ("Gienah Crv", 12.26, -17.54, 2.59),
    ("Kraz", 12.57, -23.40, 2.65),
    ("Algorab", 12.50, -16.52, 2.95),
    ("Minkar", 12.17, -22.62, 3.02),
    ("Porrima", 12.69, -1.45, 2.74),
    ("Zeta Vir", 13.58, -0.60, 3.37),
    ("Zavijava", 11.84, 1.76, 3.59),
    ("Tarf", 8.28, 9.19, 3.52),
    ("Iota Leo", 11.40, 10.53, 3.94),
    ("Gomeisa", 7.45, 8.29, 2.89),
    ("Eta Aur", 5.11, 41.23, 3.17),
    ("Almaaz", 5.03, 43.82, 2.99),
    ("Xi Gem", 6.75, 12.90, 3.35),
    ("Wasat", 7.34, 21.98, 3.53),
    ("Mekbuda", 7.07, 20.57, 3.79),
    ("Omicron CMa", 7.05, -23.83, 3.00),
    ("Seginus", 14.53, 38.31, 3.03),
    ("Nekkar", 15.03, 40.39, 3.50),
    ("Rho Boo", 14.53, 30.37, 3.58),
    ("Delta Boo", 15.26, 33.31, 3.47),
    ("Nusakan", 15.46, 29.11, 3.68),
    ("Gamma CrB", 15.71, 26.30, 3.84),
    ("Sarin", 17.25, 24.84, 3.14),
    ("Pi Her", 17.25, 36.81, 3.16),
    ("Eta Her", 16.71, 38.92, 3.53),
    ("Cebalrai", 17.72, 4.57, 2.77),
    ("Yed Prior", 16.24, -3.69, 2.74),
    ("Yed Posterior", 16.30, -4.69, 3.24),
    ("Zeta Oph", 16.62, -10.57, 2.56),
    ("Sabik", 17.17, -15.73, 2.43),
    ("Kappa Oph", 16.96, 9.38, 3.20),
    ("Gamma Sgr", 18.10, -30.42, 2.99),
    ("Kaus Media", 18.35, -29.83, 2.70),
    ("Kaus Borealis", 18.47, -25.42, 2.81),
    ("Ascella", 19.04, -29.88, 2.60),
    ("Pi Sgr", 19.16, -21.02, 2.89),
    ("Epsilon Lyr", 18.74, 39.67, 4.00),
    ("Zeta Aql", 19.09, 13.86, 2.99),
    ("Delta Aql", 19.42, 3.11, 3.36),
    ("Theta Aql", 20.19, -0.82, 3.23),
    ("Rotanev", 20.63, 14.60, 3.63),
    ("Sualocin", 20.66, 15.91, 3.77),
]

df = pd.DataFrame(
    {
        STAR_ID: [s[0] for s in stars_data] + [s[0] for s in field_data],
        RA: [s[1] for s in stars_data] + [s[1] for s in field_data],
        DEC: [s[2] for s in stars_data] + [s[2] for s in field_data],
        MAGNITUDE: [s[3] for s in stars_data] + [s[3] for s in field_data],
        CONSTELLATION: [s[4] for s in stars_data] + [""] * len(field_data),
        EDGES: ["|".join(links.get(s[0], [])) for s in stars_data] + [""] * len(field_data),
    }
)

# Plot: reads only df and the constants above
# Column names of the derived tables below
PX, PY, PX_END, PY_END = "x", "y", "xend", "yend"
LABEL, RING, NAME = "label", "ring", "name"
BRIGHT = "brightness"

# Azimuthal equidistant projection centred on the North Celestial Pole:
# angular distance from the pole becomes the radius, RA becomes the bearing.
# RA meridians map to straight radials, Dec parallels to concentric circles —
# the natural circular sky boundary the spec asks for. Seen from inside the sky
# (looking up), right ascension grows counterclockwise, so x carries a minus sign.
stars = df.dropna(subset=[RA, DEC, MAGNITUDE]).copy()
rho = 90.0 - stars[DEC]
phi = np.radians(stars[RA] * 15.0)
stars[PX] = -rho * np.sin(phi)
stars[PY] = rho * np.cos(phi)
stars[BRIGHT] = MAG_LIMIT - stars[MAGNITUDE]  # inverted magnitude drives the point size

# Tooltip values are rounded here, after projection, so they read cleanly
stars[MAGNITUDE] = stars[MAGNITUDE].round(2)
stars[RA] = stars[RA].round(2)
stars[DEC] = stars[DEC].round(1)

named = stars[stars[CONSTELLATION].fillna("") != ""]
background = stars[stars[CONSTELLATION].fillna("") == ""]
bright_1 = stars[stars[MAGNITUDE] < HALO_MAGS[0]]
bright_2 = stars[stars[MAGNITUDE] < HALO_MAGS[1]]

# Stick figures: one segment per listed link whose two stars are both drawn
pos = {sid: (px, py) for sid, px, py in zip(stars[STAR_ID], stars[PX], stars[PY], strict=True)}
segments = [
    (pos[a], pos[b])
    for a, targets in zip(stars[STAR_ID], stars[EDGES].fillna(""), strict=True)
    for b in targets.split("|")
    if a in pos and b in pos
]
df_edges = pd.DataFrame(
    {
        PX: [s[0][0] for s in segments],
        PY: [s[0][1] for s in segments],
        PX_END: [s[1][0] for s in segments],
        PY_END: [s[1][1] for s in segments],
    }
)

# RA/Dec coordinate grid — concentric Dec circles + radial RA meridians
angle = np.linspace(0, 2 * np.pi, 240)
df_circles = pd.DataFrame(
    [{PX: -(90.0 - d) * np.sin(a), PY: (90.0 - d) * np.cos(a), RING: f"d{d}"} for d in DEC_RINGS for a in angle]
)
r_bound = 90.0 - SKY_EDGE_DEC
df_boundary = pd.DataFrame({PX: -r_bound * np.sin(angle), PY: r_bound * np.cos(angle)})

ra_hours = list(range(0, 24, RA_STEP_H))
bearings = np.radians(np.array(ra_hours) * 15.0)
df_merid = pd.DataFrame(
    {
        PX: -MERIDIAN_START * np.sin(bearings),
        PY: MERIDIAN_START * np.cos(bearings),
        PX_END: -r_bound * np.sin(bearings),
        PY_END: r_bound * np.cos(bearings),
    }
)

# Grid tick labels: Dec rings along the RA=0 meridian, RA hours around the rim
df_declab = pd.DataFrame(
    {
        PX: [-(90.0 - d) * np.sin(DEC_LABEL_BEARING) for d in DEC_RINGS],
        PY: [(90.0 - d) * np.cos(DEC_LABEL_BEARING) for d in DEC_RINGS],
        LABEL: [f"{d}°" for d in DEC_RINGS],
    }
)
df_ralab = pd.DataFrame(
    {
        PX: -(r_bound + RIM_LABEL_GAP) * np.sin(bearings),
        PY: (r_bound + RIM_LABEL_GAP) * np.cos(bearings),
        LABEL: [f"{h}h" for h in ra_hours],
    }
)

# Constellation labels — projected centroid pushed radially outward to clear stars
centroids = named.groupby(CONSTELLATION)[[PX, PY]].mean().reset_index()
norm = np.hypot(centroids[PX], centroids[PY]).replace(0, 1)
centroids["ux"] = centroids[PX] / norm
centroids["uy"] = centroids[PY] / norm
# Push each name outward past the farthest star of its figure (along the radial direction)
extent = {
    c: ((g[PX] - cx) * ux + (g[PY] - cy) * uy).max()
    for (c, g), cx, cy, ux, uy in zip(
        named.groupby(CONSTELLATION), centroids[PX], centroids[PY], centroids["ux"], centroids["uy"], strict=True
    )
}
centroids[NAME] = centroids[CONSTELLATION].map(CONSTELLATION_NAMES).fillna(centroids[CONSTELLATION])
# A name is centred on its anchor, so half its width (in projected degrees) is added horizontally
half_width = centroids[NAME].str.len() * CHAR_HALF_WIDTH * centroids["ux"].abs()
push = centroids[CONSTELLATION].map(extent).clip(lower=0) + LABEL_GAP + half_width
centroids[PX] = centroids[PX] + centroids["ux"] * push
centroids[PY] = centroids[PY] + centroids["uy"] * push

plot = (
    ggplot()
    # Coordinate grid
    + geom_path(aes(x=PX, y=PY, group=RING), data=df_circles, color=GRID, size=0.4, alpha=0.13)
    + geom_segment(aes(x=PX, y=PY, xend=PX_END, yend=PY_END), data=df_merid, color=GRID, size=0.4, alpha=0.13)
    + geom_path(aes(x=PX, y=PY), data=df_boundary, color=GRID, size=0.8, alpha=0.30)
    # Constellation stick-figure lines
    + geom_segment(aes(x=PX, y=PY, xend=PX_END, yend=PY_END), data=df_edges, color=BRAND, size=0.7, alpha=0.45)
    # Faint background stars
    + geom_point(aes(x=PX, y=PY, size=BRIGHT), data=background, color=INK_MUTED, alpha=0.7, shape=16, show_legend=False)
    # Glow halo beneath the brightest stars
    + geom_point(aes(x=PX, y=PY), data=bright_2, color=STAR, alpha=0.07, size=13, shape=16)
    + geom_point(aes(x=PX, y=PY), data=bright_1, color=STAR, alpha=0.10, size=19, shape=16)
    # Constellation stars (with interactive tooltips — a lets-plot feature)
    + geom_point(
        aes(x=PX, y=PY, size=BRIGHT),
        data=named,
        color=STAR,
        alpha=0.95,
        shape=16,
        tooltips=layer_tooltips()
        .title(f"@{{{STAR_ID}}}")
        .line(f"Constellation|@{{{CONSTELLATION}}}")
        .line(f"Magnitude|@{{{MAGNITUDE}}}")
        .line(f"RA|@{{{RA}}}h")
        .line(f"Dec|@{{{DEC}}}°"),
    )
    # Brighter (lower magnitude) = larger: a reversed size scale gives the native magnitude key
    + scale_size(
        range=SIZE_RANGE,
        breaks=[MAG_LIMIT - m for m in LEGEND_MAGS],
        labels=[str(m) for m in LEGEND_MAGS],
        name="Magnitude",
    )
    # Constellation name labels
    + geom_text(aes(x=PX, y=PY, label=NAME), data=centroids, color=INK_SOFT, size=7, fontface="italic")
    # Grid tick labels
    + geom_text(aes(x=PX, y=PY, label=LABEL), data=df_declab, color=INK_MUTED, size=6.5)
    + geom_text(aes(x=PX, y=PY, label=LABEL), data=df_ralab, color=INK_MUTED, size=6.5)
    + labs(
        title="star-chart-constellation · python · letsplot · anyplot.ai",
        caption="Azimuthal equidistant projection · point size ∝ brightness (lower magnitude = brighter)",
    )
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=[-PLOT_LIMIT, PLOT_LIMIT])
    + scale_y_continuous(limits=[-PLOT_LIMIT, PLOT_LIMIT])
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid=element_blank(),
        axis_line=element_blank(),
        axis_ticks=element_blank(),
        axis_text=element_blank(),
        axis_title=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_caption=element_text(size=11, color=INK_MUTED),
        legend_position=[0.02, 0.97],
        legend_justification=[0, 1],
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
        legend_title=element_text(size=12, face="bold", color=INK),
        legend_text=element_text(size=11, color=INK_SOFT),
    )
)

# The fixed aspect narrows the plot box; a one-panel grid paints the whole square canvas
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save (square → 2400 × 2400 px at scale 4)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
