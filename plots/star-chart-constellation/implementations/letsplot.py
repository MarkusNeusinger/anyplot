""" pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Notable stars with real approximate coordinates (RA in hours, Dec in degrees)
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

# Add some fainter background stars
n_bg = 150
bg_ra = np.random.uniform(0, 24, n_bg)
bg_dec = np.random.uniform(-45, 70, n_bg)
bg_mag = np.random.uniform(3.5, 5.0, n_bg)

star_ids = [s[0] for s in stars_data] + [f"BG{i}" for i in range(n_bg)]
ra_vals = [s[1] for s in stars_data] + list(bg_ra)
dec_vals = [s[2] for s in stars_data] + list(bg_dec)
mag_vals = [s[3] for s in stars_data] + list(bg_mag)
const_vals = [s[4] for s in stars_data] + ["" for _ in range(n_bg)]

# Convert RA from hours to degrees for plotting
ra_deg = [r * 15.0 for r in ra_vals]

# Invert magnitude for point sizing: brighter = larger
max_mag = 5.5
star_sizes = [(max_mag - m + 0.5) * 1.8 for m in mag_vals]

# Star colors based on magnitude (brighter stars more yellowish)
star_colors = []
for m in mag_vals:
    if m < 0.5:
        star_colors.append("#FFFDE0")
    elif m < 1.5:
        star_colors.append("#FFF8C4")
    elif m < 2.5:
        star_colors.append("#E8E4D0")
    else:
        star_colors.append("#C8C8C8")

df = pd.DataFrame(
    {
        "star_id": star_ids,
        "ra": ra_deg,
        "dec": dec_vals,
        "magnitude": mag_vals,
        "constellation": const_vals,
        "size": star_sizes,
        "color": star_colors,
    }
)

# Constellation edges (pairs of star names)
edges = [
    # Orion
    ("Betelgeuse", "Bellatrix"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Betelgeuse", "Alnitak"),
    ("Bellatrix", "Rigel"),
    ("Betelgeuse", "Saiph"),
    ("Rigel", "Saiph"),
    # Ursa Major (Big Dipper)
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
    ("Chertan", "Zosma"),
    ("Zosma", "Denebola"),
    ("Regulus", "Algieba"),
    ("Algieba", "Zosma"),
    # Cygnus
    ("Deneb", "Sadr"),
    ("Sadr", "Albireo"),
    ("Sadr", "Gienah Cyg"),
    ("Sadr", "Fawaris"),
    # Scorpius
    ("Graffias", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Shaula"),
    ("Shaula", "Lesath"),
    ("Shaula", "Sargas"),
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
    # Canis Major
    ("Sirius", "Mirzam"),
    ("Sirius", "Adhara"),
    ("Adhara", "Wezen"),
    ("Wezen", "Aludra"),
    # Taurus
    ("Aldebaran", "Elnath"),
    ("Aldebaran", "Alcyone"),
    ("Elnath", "Tianguan"),
    # Bootes
    ("Arcturus", "Izar"),
    ("Arcturus", "Muphrid"),
    # Perseus
    ("Mirfak", "Algol"),
    ("Algol", "Atik"),
]

# Build edge dataframe for constellation lines
star_lookup = {row["star_id"]: row for _, row in df.iterrows()}
edge_rows = []
for s1, s2 in edges:
    if s1 in star_lookup and s2 in star_lookup:
        r1, r2 = star_lookup[s1], star_lookup[s2]
        edge_rows.append(
            {"x": r1["ra"], "y": r1["dec"], "xend": r2["ra"], "yend": r2["dec"], "constellation": r1["constellation"]}
        )

df_edges = pd.DataFrame(edge_rows)

# Constellation label positions (centroid with vertical offset to avoid overlap)
named_stars = df[df["constellation"] != ""]
const_labels = (
    named_stars.groupby("constellation").agg(ra_center=("ra", "mean"), dec_center=("dec", "mean")).reset_index()
)
# Per-constellation offsets to avoid overlap with stars and lines
label_offsets = {
    "Aql": (5, 5),
    "Boo": (0, 5),
    "Cas": (0, 5),
    "CMa": (10, 3),
    "Cyg": (15, 5),
    "Gem": (0, 5),
    "Leo": (-10, 5),
    "Lyr": (-15, 3),
    "Ori": (-5, 5),
    "Per": (0, 5),
    "Sco": (-15, 5),
    "Tau": (0, 5),
    "UMa": (0, 5),
}
const_labels["ra_center"] = const_labels.apply(
    lambda r: r["ra_center"] + label_offsets.get(r["constellation"], (0, 0))[0], axis=1
)
const_labels["dec_center"] = const_labels.apply(
    lambda r: r["dec_center"] + label_offsets.get(r["constellation"], (0, 0))[1], axis=1
)

const_full_names = {
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
const_labels["name"] = const_labels["constellation"].map(const_full_names)

# RA grid lines
ra_grid_vals = list(range(0, 360, 30))
ra_grid_rows = []
for ra_val in ra_grid_vals:
    for d in np.linspace(-45, 70, 50):
        ra_grid_rows.append({"ra": ra_val, "dec": d, "group": f"ra_{ra_val}"})
df_ra_grid = pd.DataFrame(ra_grid_rows)

# Dec grid lines
dec_grid_vals = list(range(-30, 70, 15))
dec_grid_rows = []
for dec_val in dec_grid_vals:
    for r in np.linspace(0, 360, 100):
        dec_grid_rows.append({"ra": r, "dec": dec_val, "group": f"dec_{dec_val}"})
df_dec_grid = pd.DataFrame(dec_grid_rows)

# Magnitude legend data (positioned in lower-right area)
legend_mags = [0, 1, 2, 3, 4, 5]
legend_x = 340
legend_y_start = -38
legend_spacing = 6
df_legend = pd.DataFrame(
    {
        "ra": [legend_x] * len(legend_mags),
        "dec": [legend_y_start + i * legend_spacing for i in range(len(legend_mags))],
        "size": [(max_mag - m + 0.5) * 1.8 for m in legend_mags],
        "label": [f"mag {m}" for m in legend_mags],
    }
)

# Plot
plot = (
    ggplot()
    # Coordinate grid (visible but subtle)
    + geom_line(aes(x="ra", y="dec", group="group"), data=df_ra_grid, color="#1e4a6e", size=0.4, alpha=0.55)
    + geom_line(aes(x="ra", y="dec", group="group"), data=df_dec_grid, color="#1e4a6e", size=0.4, alpha=0.55)
    # Constellation lines
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_edges, color="#4a7fb5", size=0.8, alpha=0.45)
    # Background/faint stars
    + geom_point(
        aes(x="ra", y="dec", size="size"), data=df[df["constellation"] == ""], color="#888888", alpha=0.5, shape=16
    )
    # Constellation stars with tooltips (lets-plot interactive feature)
    + geom_point(
        aes(x="ra", y="dec", size="size", color="color"),
        data=df[df["constellation"] != ""],
        alpha=0.95,
        shape=16,
        tooltips=layer_tooltips().line("@star_id").line("Magnitude: @magnitude").line("RA: @{ra} | Dec: @{dec}°"),
    )
    + scale_color_identity()
    + scale_size_identity()
    # Constellation labels
    + geom_text(
        aes(x="ra_center", y="dec_center", label="name"),
        data=const_labels,
        color="#6BAED6",
        size=12,
        fontface="italic",
        alpha=0.9,
    )
    # Axis labels and title
    + scale_x_continuous(
        name="Right Ascension (hours)", breaks=ra_grid_vals, labels=[f"{int(v / 15)}h" for v in ra_grid_vals]
    )
    + scale_y_continuous(
        name="Declination (degrees)", breaks=list(range(-30, 75, 15)), labels=[f"{v}°" for v in range(-30, 75, 15)]
    )
    # Magnitude legend key
    + geom_point(aes(x="ra", y="dec", size="size"), data=df_legend, color="#FFFDE0", alpha=0.9, shape=16)
    + geom_text(aes(x="ra", y="dec", label="label"), data=df_legend, color="#8899aa", size=10, nudge_x=12)
    + labs(
        title="star-chart-constellation · lets-plot · pyplots.ai",
        caption="Star size ∝ brightness (lower magnitude = brighter)",
    )
    + theme(
        plot_background=element_rect(fill="#0a0e1a"),
        panel_background=element_rect(fill="#0a0e1a"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=24, face="bold", color="#c8d8e8"),
        plot_caption=element_text(size=14, color="#667788"),
        axis_title=element_text(size=20, color="#8899aa"),
        axis_text=element_text(size=16, color="#667788"),
        axis_ticks=element_line(color="#334455"),
        axis_line=element_line(color="#334455"),
        legend_position="none",
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
