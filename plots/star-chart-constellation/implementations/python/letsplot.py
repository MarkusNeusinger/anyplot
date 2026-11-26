"""anyplot.ai
star-chart-constellation: Star Chart with Constellations
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 92/100 | Updated: 2026-06-17
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
MAG_LIMIT = 5.5  # faintest magnitude the size scale covers
HALO_MAGS = (0.6, 1.2)  # stars brighter than these get a strong / soft glow halo
DEC_RINGS = (60, 30, 0, -30)  # declination circles of the grid, in degrees
DEC_LABEL_BEARING = np.radians(9 * 15.0)  # Dec labels sit on the 9h meridian, a sparse stretch of sky
RA_STEP_H = 2  # one meridian and one rim label every 2 hours of right ascension
SKY_EDGE_DEC = -48.0  # declination of the circular sky boundary
RIM_LABEL_GAP = 11.0  # distance of the RA hour labels beyond the sky boundary
MERIDIAN_START = 22.0  # meridians start this far from the pole, clear of the Dec labels
LABEL_PUSH = 15.0  # constellation names sit this far outward of their centroid
PLOT_LIMIT = 160  # half-width of the square plot window in projected degrees
LEGEND_MAGS = (0, 1, 2, 3, 4, 5)
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
np.random.seed(42)

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

# Fainter background stars to fill out the sky (mag <= 5.0 threshold per spec)
n_bg = 150
bg_ra = np.random.uniform(0, 24, n_bg)
bg_dec = np.random.uniform(-45, 70, n_bg)
bg_mag = np.random.uniform(3.5, 5.0, n_bg)

df = pd.DataFrame(
    {
        STAR_ID: [s[0] for s in stars_data] + [f"BG{i}" for i in range(n_bg)],
        RA: [s[1] for s in stars_data] + list(bg_ra),
        DEC: [s[2] for s in stars_data] + list(bg_dec),
        MAGNITUDE: [s[3] for s in stars_data] + list(bg_mag),
        CONSTELLATION: [s[4] for s in stars_data] + [""] * n_bg,
        EDGES: ["|".join(links.get(s[0], [])) for s in stars_data] + [""] * n_bg,
    }
)

# Plot: reads only df and the constants above
# Column names of the derived tables below
PX, PY, PX_END, PY_END = "x", "y", "xend", "yend"
SIZE, LABEL, RING, NAME = "size", "label", "ring", "name"
BOX_X0, BOX_X1, BOX_Y0, BOX_Y1 = "xmin", "xmax", "ymin", "ymax"

# Azimuthal equidistant projection centred on the North Celestial Pole:
# angular distance from the pole becomes the radius, RA becomes the bearing.
# RA meridians map to straight radials, Dec parallels to concentric circles —
# the natural circular sky boundary the spec asks for.
stars = df.dropna(subset=[RA, DEC, MAGNITUDE]).copy()
rho = 90.0 - stars[DEC]
phi = np.radians(stars[RA] * 15.0)
stars[PX] = rho * np.sin(phi)
stars[PY] = rho * np.cos(phi)

# Invert magnitude for point sizing: brighter (lower magnitude) = larger
stars[SIZE] = (MAG_LIMIT - stars[MAGNITUDE] + 0.6) * 1.5

# Tooltip values are rounded here, after projection and sizing, so they read cleanly
stars[MAGNITUDE] = stars[MAGNITUDE].round(2)
stars[RA] = stars[RA].round(2)
stars[DEC] = stars[DEC].round(1)

named = stars[stars[CONSTELLATION].fillna("") != ""]
background = stars[stars[CONSTELLATION].fillna("") == ""]
bright_1 = named[named[MAGNITUDE] < HALO_MAGS[0]]
bright_2 = named[named[MAGNITUDE] < HALO_MAGS[1]]

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
    [{PX: (90.0 - d) * np.sin(a), PY: (90.0 - d) * np.cos(a), RING: f"d{d}"} for d in DEC_RINGS for a in angle]
)
r_bound = 90.0 - SKY_EDGE_DEC
df_boundary = pd.DataFrame({PX: r_bound * np.sin(angle), PY: r_bound * np.cos(angle)})

ra_hours = list(range(0, 24, RA_STEP_H))
bearings = np.radians(np.array(ra_hours) * 15.0)
df_merid = pd.DataFrame(
    {
        PX: MERIDIAN_START * np.sin(bearings),
        PY: MERIDIAN_START * np.cos(bearings),
        PX_END: r_bound * np.sin(bearings),
        PY_END: r_bound * np.cos(bearings),
    }
)

# Grid tick labels: Dec rings along the RA=0 meridian, RA hours around the rim
df_declab = pd.DataFrame(
    {
        PX: [(90.0 - d) * np.sin(DEC_LABEL_BEARING) for d in DEC_RINGS],
        PY: [(90.0 - d) * np.cos(DEC_LABEL_BEARING) for d in DEC_RINGS],
        LABEL: [f"{d}°" for d in DEC_RINGS],
    }
)
df_ralab = pd.DataFrame(
    {
        PX: (r_bound + RIM_LABEL_GAP) * np.sin(bearings),
        PY: (r_bound + RIM_LABEL_GAP) * np.cos(bearings),
        LABEL: [f"{h}h" for h in ra_hours],
    }
)

# Constellation labels — projected centroid pushed radially outward to clear stars
centroids = named.groupby(CONSTELLATION)[[PX, PY]].mean().reset_index()
norm = np.hypot(centroids[PX], centroids[PY]).replace(0, 1)
centroids[PX] = centroids[PX] + centroids[PX] / norm * LABEL_PUSH
centroids[PY] = centroids[PY] + centroids[PY] / norm * LABEL_PUSH
centroids[NAME] = centroids[CONSTELLATION].map(CONSTELLATION_NAMES).fillna(centroids[CONSTELLATION])

# Magnitude legend — compact panel tucked into the empty top-left corner (outside the sky disc)
legend_x = -(r_bound - 10)
legend_y0 = r_bound - 46
legend_step = 9
df_legend = pd.DataFrame(
    {
        PX: [legend_x] * len(LEGEND_MAGS),
        PY: [legend_y0 + i * legend_step for i in range(len(LEGEND_MAGS))],
        SIZE: [(MAG_LIMIT - m + 0.6) * 1.5 for m in LEGEND_MAGS],
        LABEL: [f"mag {m}" for m in LEGEND_MAGS],
    }
)
df_legend_title = pd.DataFrame({PX: [legend_x - 16], PY: [legend_y0 + len(LEGEND_MAGS) * legend_step]})
df_legend_bg = pd.DataFrame(
    {
        BOX_X0: [legend_x - 20],
        BOX_X1: [legend_x + 37],
        BOX_Y0: [legend_y0 - 7],
        BOX_Y1: [legend_y0 + len(LEGEND_MAGS) * legend_step + 11],
    }
)

plot = (
    ggplot()
    # Coordinate grid
    + geom_path(aes(x=PX, y=PY, group=RING), data=df_circles, color=GRID, size=0.4, alpha=0.13)
    + geom_segment(aes(x=PX, y=PY, xend=PX_END, yend=PY_END), data=df_merid, color=GRID, size=0.4, alpha=0.13)
    + geom_path(aes(x=PX, y=PY), data=df_boundary, color=GRID, size=0.8, alpha=0.30)
    # Constellation stick-figure lines
    + geom_segment(aes(x=PX, y=PY, xend=PX_END, yend=PY_END), data=df_edges, color=BRAND, size=0.7, alpha=0.45)
    # Faint background stars
    + geom_point(aes(x=PX, y=PY, size=SIZE), data=background, color=INK_MUTED, alpha=0.55, shape=16)
    # Glow halo beneath the brightest stars
    + geom_point(aes(x=PX, y=PY), data=bright_2, color=BRAND, alpha=0.07, size=13, shape=16)
    + geom_point(aes(x=PX, y=PY), data=bright_1, color=BRAND, alpha=0.10, size=19, shape=16)
    # Named constellation stars (with interactive tooltips — a lets-plot feature)
    + geom_point(
        aes(x=PX, y=PY, size=SIZE),
        data=named,
        color=BRAND,
        alpha=0.95,
        shape=16,
        tooltips=layer_tooltips()
        .title(f"@{{{STAR_ID}}}")
        .line(f"Constellation|@{{{CONSTELLATION}}}")
        .line(f"Magnitude|@{{{MAGNITUDE}}}")
        .line(f"RA|@{{{RA}}}h")
        .line(f"Dec|@{{{DEC}}}°"),
    )
    + scale_size_identity()
    # Constellation name labels
    + geom_text(aes(x=PX, y=PY, label=NAME), data=centroids, color=INK_SOFT, size=7, fontface="italic")
    # Grid tick labels
    + geom_text(aes(x=PX, y=PY, label=LABEL), data=df_declab, color=INK_MUTED, size=6.5)
    + geom_text(aes(x=PX, y=PY, label=LABEL), data=df_ralab, color=INK_MUTED, size=6.5)
    # Magnitude legend panel
    + geom_rect(
        aes(xmin=BOX_X0, xmax=BOX_X1, ymin=BOX_Y0, ymax=BOX_Y1),
        data=df_legend_bg,
        fill=ELEVATED_BG,
        color=INK_SOFT,
        alpha=0.9,
        size=0.4,
    )
    + geom_point(aes(x=PX, y=PY, size=SIZE), data=df_legend, color=BRAND, alpha=0.95, shape=16)
    + geom_text(aes(x=PX, y=PY, label=LABEL), data=df_legend, color=INK_SOFT, size=5, nudge_x=10, hjust=0)
    + geom_text(aes(x=PX, y=PY), data=df_legend_title, label="Magnitude", color=INK, size=6, fontface="bold", hjust=0)
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
        legend_position="none",
    )
)

# The fixed aspect narrows the plot box; a one-panel grid paints the whole square canvas
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save (square → 2400 × 2400 px at scale 4)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
