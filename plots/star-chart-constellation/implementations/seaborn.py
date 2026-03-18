"""pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-18
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Major stars with approximate RA (hours) and Dec (degrees)
np.random.seed(42)

stars = {
    # Orion
    "Betelgeuse": (5.92, 7.41, 0.42, "Ori"),
    "Rigel": (5.24, -8.20, 0.13, "Ori"),
    "Bellatrix": (5.42, 6.35, 1.64, "Ori"),
    "Mintaka": (5.53, -0.30, 2.23, "Ori"),
    "Alnilam": (5.60, -1.20, 1.69, "Ori"),
    "Alnitak": (5.68, -1.94, 1.77, "Ori"),
    "Saiph": (5.80, -9.67, 2.09, "Ori"),
    # Ursa Major (Big Dipper)
    "Dubhe": (11.06, 61.75, 1.79, "UMa"),
    "Merak": (11.03, 56.38, 2.37, "UMa"),
    "Phecda": (11.90, 53.69, 2.44, "UMa"),
    "Megrez": (12.26, 57.03, 3.31, "UMa"),
    "Alioth": (12.90, 55.96, 1.77, "UMa"),
    "Mizar": (13.40, 54.93, 2.27, "UMa"),
    "Alkaid": (13.79, 49.31, 1.86, "UMa"),
    # Cassiopeia
    "Schedar": (0.68, 56.54, 2.23, "Cas"),
    "Caph": (0.15, 59.15, 2.27, "Cas"),
    "Gamma Cas": (0.95, 60.72, 2.47, "Cas"),
    "Ruchbah": (1.36, 60.24, 2.68, "Cas"),
    "Segin": (1.91, 63.67, 3.37, "Cas"),
    # Leo
    "Regulus": (10.14, 11.97, 1.35, "Leo"),
    "Denebola": (11.82, 14.57, 2.14, "Leo"),
    "Algieba": (10.33, 19.84, 2.28, "Leo"),
    "Zosma": (11.24, 20.52, 2.56, "Leo"),
    "Chertan": (11.24, 15.43, 3.34, "Leo"),
    "Eta Leo": (10.12, 16.76, 3.52, "Leo"),
    # Cygnus
    "Deneb": (20.69, 45.28, 1.25, "Cyg"),
    "Sadr": (20.37, 40.26, 2.23, "Cyg"),
    "Gienah Cyg": (20.77, 33.97, 2.46, "Cyg"),
    "Delta Cyg": (19.75, 45.13, 2.87, "Cyg"),
    "Albireo": (19.51, 27.96, 3.08, "Cyg"),
    # Gemini
    "Pollux": (7.76, 28.03, 1.14, "Gem"),
    "Castor": (7.58, 31.89, 1.58, "Gem"),
    "Alhena": (6.63, 16.40, 1.93, "Gem"),
    "Wasat": (7.07, 21.98, 3.53, "Gem"),
    "Mebsuta": (6.73, 25.13, 2.98, "Gem"),
    "Tejat": (6.38, 22.51, 2.88, "Gem"),
    # Taurus
    "Aldebaran": (4.60, 16.51, 0.85, "Tau"),
    "Elnath": (5.44, 28.61, 1.65, "Tau"),
    "Alcyone": (3.79, 24.11, 2.87, "Tau"),
    "Tianguan": (5.63, 21.14, 3.00, "Tau"),
    "Lambda Tau": (4.01, 12.49, 3.47, "Tau"),
    # Lyra
    "Vega": (18.62, 38.78, 0.03, "Lyr"),
    "Sheliak": (18.83, 33.36, 3.45, "Lyr"),
    "Sulafat": (18.98, 32.69, 3.24, "Lyr"),
    "Delta2 Lyr": (18.91, 36.90, 4.30, "Lyr"),
    # Aquila
    "Altair": (19.85, 8.87, 0.77, "Aql"),
    "Tarazed": (19.77, 10.61, 2.72, "Aql"),
    "Alshain": (19.92, 6.41, 3.71, "Aql"),
    # Scorpius
    "Antares": (16.49, -26.43, 0.96, "Sco"),
    "Shaula": (17.56, -37.10, 1.63, "Sco"),
    "Sargas": (17.62, -43.00, 1.87, "Sco"),
    "Dschubba": (16.01, -22.62, 2.32, "Sco"),
    "Graffias": (16.09, -19.81, 2.62, "Sco"),
    "Epsilon Sco": (16.84, -34.29, 2.29, "Sco"),
    "Mu1 Sco": (16.86, -38.05, 3.04, "Sco"),
    # Bootes
    "Arcturus": (14.26, 19.18, -0.05, "Boo"),
    "Izar": (14.75, 27.07, 2.37, "Boo"),
    "Muphrid": (13.91, 18.40, 2.68, "Boo"),
    "Nekkar": (15.03, 40.39, 3.50, "Boo"),
    # Perseus
    "Mirfak": (3.41, 49.86, 1.79, "Per"),
    "Algol": (3.14, 40.96, 2.12, "Per"),
    "Zeta Per": (3.90, 31.88, 2.85, "Per"),
    "Epsilon Per": (3.96, 40.01, 2.89, "Per"),
    "Delta Per": (3.72, 47.79, 3.01, "Per"),
    # Auriga
    "Capella": (5.28, 46.00, 0.08, "Aur"),
    "Menkalinan": (5.99, 44.95, 1.90, "Aur"),
    "Theta Aur": (5.99, 37.21, 2.62, "Aur"),
    "Iota Aur": (4.95, 33.17, 2.69, "Aur"),
    # Canis Major
    "Sirius": (6.75, -16.72, -1.46, "CMa"),
    "Adhara": (6.98, -28.97, 1.50, "CMa"),
    "Wezen": (7.14, -26.39, 1.84, "CMa"),
    "Mirzam": (6.38, -17.96, 1.98, "CMa"),
    "Aludra": (7.40, -29.30, 2.45, "CMa"),
    # Andromeda
    "Alpheratz": (0.14, 29.09, 2.06, "And"),
    "Mirach": (1.16, 35.62, 2.05, "And"),
    "Almach": (2.06, 42.33, 2.17, "And"),
}

# Convert to DataFrame
star_names = list(stars.keys())
ra_hours = [stars[s][0] for s in star_names]
dec_deg = [stars[s][1] for s in star_names]
magnitudes = [stars[s][2] for s in star_names]
constellations = [stars[s][3] for s in star_names]

df = pd.DataFrame(
    {"name": star_names, "ra": ra_hours, "dec": dec_deg, "mag": magnitudes, "constellation": constellations}
)

# Add ~200 fainter background stars
n_bg = 200
bg_ra = np.random.uniform(0, 24, n_bg)
bg_dec = np.random.uniform(-45, 70, n_bg)
bg_mag = np.random.uniform(3.5, 5.5, n_bg)
bg_df = pd.DataFrame(
    {"name": [f"BG{i}" for i in range(n_bg)], "ra": bg_ra, "dec": bg_dec, "mag": bg_mag, "constellation": "---"}
)
df = pd.concat([df, bg_df], ignore_index=True)

# Constellation edges (pairs of star names)
edges = [
    # Orion
    ("Betelgeuse", "Bellatrix"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Betelgeuse", "Alnitak"),
    ("Bellatrix", "Rigel"),
    ("Alnitak", "Saiph"),
    ("Saiph", "Rigel"),
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
    ("Regulus", "Eta Leo"),
    ("Eta Leo", "Algieba"),
    ("Algieba", "Zosma"),
    ("Zosma", "Denebola"),
    ("Regulus", "Chertan"),
    ("Chertan", "Denebola"),
    # Cygnus
    ("Deneb", "Sadr"),
    ("Sadr", "Gienah Cyg"),
    ("Sadr", "Delta Cyg"),
    ("Sadr", "Albireo"),
    # Gemini
    ("Castor", "Pollux"),
    ("Castor", "Mebsuta"),
    ("Mebsuta", "Tejat"),
    ("Pollux", "Wasat"),
    ("Wasat", "Alhena"),
    ("Tejat", "Alhena"),
    # Taurus
    ("Aldebaran", "Lambda Tau"),
    ("Aldebaran", "Elnath"),
    ("Aldebaran", "Alcyone"),
    ("Elnath", "Tianguan"),
    # Lyra
    ("Vega", "Sheliak"),
    ("Vega", "Sulafat"),
    ("Sheliak", "Sulafat"),
    ("Vega", "Delta2 Lyr"),
    # Aquila
    ("Altair", "Tarazed"),
    ("Altair", "Alshain"),
    # Scorpius
    ("Graffias", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Epsilon Sco"),
    ("Epsilon Sco", "Mu1 Sco"),
    ("Mu1 Sco", "Shaula"),
    ("Shaula", "Sargas"),
    # Bootes
    ("Arcturus", "Izar"),
    ("Arcturus", "Muphrid"),
    ("Izar", "Nekkar"),
    # Perseus
    ("Mirfak", "Delta Per"),
    ("Mirfak", "Epsilon Per"),
    ("Epsilon Per", "Zeta Per"),
    ("Mirfak", "Algol"),
    # Auriga
    ("Capella", "Menkalinan"),
    ("Menkalinan", "Theta Aur"),
    ("Theta Aur", "Iota Aur"),
    ("Iota Aur", "Capella"),
    # Canis Major
    ("Sirius", "Mirzam"),
    ("Sirius", "Adhara"),
    ("Adhara", "Wezen"),
    ("Wezen", "Aludra"),
    # Andromeda
    ("Alpheratz", "Mirach"),
    ("Mirach", "Almach"),
]

# Convert RA (hours) to degrees for plotting
df["ra_deg"] = df["ra"] * 15.0

# Invert magnitude for sizing: brighter stars (lower mag) get larger markers
mag_min, mag_max = df["mag"].min(), df["mag"].max()
df["size"] = np.interp(df["mag"], [mag_min, mag_max], [500, 15])

# Bin magnitudes for legend-friendly seaborn hue mapping
mag_bins = [-2, 1.0, 2.0, 3.0, 6.0]
mag_labels = ["< 1.0 (brightest)", "1.0 – 2.0", "2.0 – 3.0", "> 3.0 (faintest)"]
df["mag_class"] = pd.cut(df["mag"], bins=mag_bins, labels=mag_labels)

# Build star lookup for edges
star_lookup = df.set_index("name")[["ra_deg", "dec"]].to_dict("index")

# Constellation label positions (centroid of each constellation's stars)
constellation_names = {
    "Ori": "Orion",
    "UMa": "Ursa Major",
    "Cas": "Cassiopeia",
    "Leo": "Leo",
    "Cyg": "Cygnus",
    "Gem": "Gemini",
    "Tau": "Taurus",
    "Lyr": "Lyra",
    "Aql": "Aquila",
    "Sco": "Scorpius",
    "Boo": "Boötes",
    "Per": "Perseus",
    "Aur": "Auriga",
    "CMa": "Canis Major",
    "And": "Andromeda",
}
named_stars = df[df["constellation"] != "---"]
centroids = named_stars.groupby("constellation")[["ra_deg", "dec"]].mean()

# Plot setup - use seaborn's context scaling for consistent sizing
sns.set_theme(
    style="dark",
    context="talk",
    font_scale=1.0,
    rc={
        "axes.facecolor": "#070b22",
        "figure.facecolor": "#070b22",
        "grid.color": "#151e48",
        "text.color": "#d0d8f0",
        "axes.edgecolor": "#2a3570",
        "axes.labelcolor": "#d0d8f0",
        "xtick.color": "#8090c0",
        "ytick.color": "#8090c0",
        "font.family": "sans-serif",
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

# Draw Milky Way band as a faint filled region (approximate galactic plane)
# The Milky Way crosses the sky roughly through Cygnus, Cassiopeia, and Canis Major
mw_ra = np.linspace(0, 360, 200)
mw_center_dec = 25 * np.sin(np.radians(mw_ra * 1.0 - 80)) + 5
mw_width = 18
ax.fill_between(
    mw_ra, mw_center_dec - mw_width, mw_center_dec + mw_width, color="#1a2244", alpha=0.35, zorder=0, label="_nolegend_"
)

# Draw ecliptic line as dashed curve (approximate)
ecl_ra = np.linspace(0, 360, 300)
ecl_dec = 23.44 * np.sin(np.radians(ecl_ra - 90))
ax.plot(ecl_ra, ecl_dec, color="#665533", linewidth=1.2, linestyle="--", alpha=0.5, zorder=1, label="_nolegend_")

# Draw RA/Dec grid with subtle styling
for ra_line in range(0, 360, 30):
    ax.axvline(x=ra_line, color="#151e48", linewidth=0.4, alpha=0.7, zorder=0)
for dec_line in range(-60, 90, 15):
    ax.axhline(y=dec_line, color="#151e48", linewidth=0.4, alpha=0.7, zorder=0)

# Constellation stick-figure lines with glow effect
for s1, s2 in edges:
    if s1 in star_lookup and s2 in star_lookup:
        x1, y1 = star_lookup[s1]["ra_deg"], star_lookup[s1]["dec"]
        x2, y2 = star_lookup[s2]["ra_deg"], star_lookup[s2]["dec"]
        # Outer glow
        ax.plot([x1, x2], [y1, y2], color="#3a5f9f", linewidth=2.5, alpha=0.15, zorder=1)
        # Inner line
        ax.plot([x1, x2], [y1, y2], color="#5580bb", linewidth=0.9, alpha=0.55, zorder=1)

# Background stars using seaborn scatterplot
bg_mask = df["constellation"] == "---"
sns.scatterplot(
    data=df[bg_mask],
    x="ra_deg",
    y="dec",
    size="size",
    sizes=(4, 22),
    color="#7788aa",
    alpha=0.35,
    edgecolor="none",
    legend=False,
    ax=ax,
    zorder=2,
)

# Named constellation stars with seaborn hue-based categorical color mapping
mag_palette = {
    "< 1.0 (brightest)": "#fffce0",
    "1.0 – 2.0": "#f0d060",
    "2.0 – 3.0": "#c87830",
    "> 3.0 (faintest)": "#804020",
}
named_df = df[~bg_mask].copy()

sns.scatterplot(
    data=named_df,
    x="ra_deg",
    y="dec",
    hue="mag_class",
    hue_order=mag_labels,
    size="size",
    sizes=(30, 500),
    palette=mag_palette,
    edgecolor="white",
    linewidth=0.5,
    alpha=0.95,
    ax=ax,
    zorder=3,
)

# Style the legend - filter to only show magnitude class entries
handles, labels = ax.get_legend_handles_labels()
hue_handles = []
hue_labels = []
for handle, label_text in zip(handles, labels, strict=False):
    if label_text in mag_palette:
        hue_handles.append(handle)
        hue_labels.append(label_text)
legend = ax.legend(
    hue_handles,
    hue_labels,
    title="Apparent Magnitude",
    loc="lower left",
    fontsize=12,
    title_fontsize=14,
    framealpha=0.4,
    facecolor="#0a0e2a",
    edgecolor="#2a3570",
    labelcolor="#d0d8f0",
    borderpad=1.0,
    handletextpad=0.8,
)
legend.get_title().set_color("#d0d8f0")

# Constellation labels with carefully tuned offsets to avoid all overlaps
text_stroke = [pe.withStroke(linewidth=3, foreground="#070b22")]
label_offsets = {
    "CMa": (0, -10),
    "Lyr": (-15, 5),
    "Aql": (0, -8),
    "Sco": (0, -9),
    "Aur": (-10, 7),
    "Per": (0, 8),
    "Ori": (0, -8),
    "Tau": (-10, -6),
    "Gem": (0, 6),
    "And": (0, 6),
    "Boo": (0, 7),
}
for abbr, row in centroids.iterrows():
    label = constellation_names.get(abbr, abbr)
    dx, dy = label_offsets.get(abbr, (0, 4))
    ax.text(
        row["ra_deg"] + dx,
        row["dec"] + dy,
        label,
        fontsize=13,
        color="#7a9acc",
        alpha=0.9,
        ha="center",
        va="bottom",
        fontweight="bold",
        fontstyle="italic",
        path_effects=text_stroke,
        zorder=4,
    )

# Label brightest stars (mag < 1.0) with carefully adjusted offsets to avoid overlaps
brightest = df[(df["mag"] < 1.0) & (df["constellation"] != "---")]
star_label_offsets = {
    "Sirius": (7, 4),
    "Vega": (6, 4),
    "Capella": (6, 4),
    "Arcturus": (6, -3),
    "Altair": (6, 4),
    "Aldebaran": (6, -5),
    "Rigel": (6, 4),
    "Betelgeuse": (-5, -5),
}
for _, star in brightest.iterrows():
    dx, dy = star_label_offsets.get(star["name"], (4, -3))
    ax.text(
        star["ra_deg"] + dx,
        star["dec"] + dy,
        star["name"],
        fontsize=11,
        color="#d0daf0",
        alpha=0.85,
        ha="left",
        va="top",
        fontweight="medium",
        path_effects=text_stroke,
        zorder=4,
    )

# Axes styling
ax.set_xlim(360, 0)
ax.set_ylim(-50, 72)
ax.set_xlabel("Right Ascension (°)", fontsize=20)
ax.set_ylabel("Declination (°)", fontsize=20)
ax.set_title("star-chart-constellation · seaborn · pyplots.ai", fontsize=24, fontweight="bold", color="#e0e8ff", pad=20)
ax.text(
    0.5,
    1.01,
    "Azimuthal Equidistant Projection  ·  North Celestial Pole at Center  ·  Ecliptic (dashed) & Milky Way (shaded)",
    transform=ax.transAxes,
    fontsize=12,
    color="#7080a0",
    ha="center",
    va="bottom",
)
ax.tick_params(axis="both", labelsize=16)

ra_ticks = np.arange(0, 361, 30)
ra_labels_text = [f"{int(h)}h" for h in ra_ticks / 15]
ax.set_xticks(ra_ticks)
ax.set_xticklabels(ra_labels_text)

dec_ticks = np.arange(-45, 76, 15)
dec_labels_text = [f"{d:+d}°" for d in dec_ticks]
ax.set_yticks(dec_ticks)
ax.set_yticklabels(dec_labels_text)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_linewidth(0.5)
ax.spines["left"].set_linewidth(0.5)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
