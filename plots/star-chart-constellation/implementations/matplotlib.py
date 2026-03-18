"""pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-18
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


np.random.seed(42)

# Star catalog: name -> (RA hours, Dec degrees, magnitude, constellation abbrev)
stars = {
    # Orion
    "Betelgeuse": (5.92, 7.41, 0.42, "Ori"),
    "Rigel": (5.24, -8.20, 0.13, "Ori"),
    "Bellatrix": (5.42, 6.35, 1.64, "Ori"),
    "Mintaka": (5.53, -0.30, 2.23, "Ori"),
    "Alnilam": (5.60, -1.20, 1.69, "Ori"),
    "Alnitak": (5.68, -1.94, 1.77, "Ori"),
    "Saiph": (5.80, -9.67, 2.09, "Ori"),
    # Ursa Major
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
    "Denebola": (11.82, 14.57, 2.13, "Leo"),
    "Algieba": (10.33, 19.84, 2.08, "Leo"),
    "Zosma": (11.24, 20.52, 2.56, "Leo"),
    "Chertan": (11.24, 15.43, 3.33, "Leo"),
    "Eta Leo": (10.12, 16.76, 3.52, "Leo"),
    # Scorpius
    "Antares": (16.49, -26.43, 1.09, "Sco"),
    "Shaula": (17.56, -37.10, 1.63, "Sco"),
    "Sargas": (17.62, -42.99, 1.87, "Sco"),
    "Dschubba": (16.01, -22.62, 2.32, "Sco"),
    "Acrab": (16.09, -19.81, 2.62, "Sco"),
    "Wei": (16.84, -34.29, 2.29, "Sco"),
    "Lesath": (17.53, -37.29, 2.69, "Sco"),
    # Cygnus
    "Deneb": (20.69, 45.28, 1.25, "Cyg"),
    "Sadr": (20.37, 40.26, 2.20, "Cyg"),
    "Gienah Cyg": (20.77, 33.97, 2.46, "Cyg"),
    "Delta Cyg": (19.75, 45.13, 2.87, "Cyg"),
    "Albireo": (19.51, 27.96, 3.08, "Cyg"),
    # Lyra
    "Vega": (18.62, 38.78, 0.03, "Lyr"),
    "Sheliak": (18.83, 33.36, 3.45, "Lyr"),
    "Sulafat": (18.98, 32.69, 3.24, "Lyr"),
    "Epsilon1 Lyr": (18.74, 39.67, 4.67, "Lyr"),
    "Epsilon2 Lyr": (18.75, 39.61, 4.59, "Lyr"),
    # Gemini
    "Pollux": (7.76, 28.03, 1.14, "Gem"),
    "Castor": (7.58, 31.89, 1.58, "Gem"),
    "Alhena": (6.63, 16.40, 1.93, "Gem"),
    "Wasat": (7.07, 21.98, 3.53, "Gem"),
    "Mebsuta": (6.73, 25.13, 2.98, "Gem"),
    "Tejat": (6.38, 22.51, 2.88, "Gem"),
    # Taurus
    "Aldebaran": (4.60, 16.51, 0.85, "Tau"),
    "Elnath": (5.44, 28.61, 1.68, "Tau"),
    "Alcyone": (3.79, 24.11, 2.87, "Tau"),
    "Tianguan": (5.63, 21.14, 3.00, "Tau"),
    "Prima Hyadum": (4.33, 15.63, 3.65, "Tau"),
    "Ain": (4.48, 19.18, 3.54, "Tau"),
    # Canis Major
    "Sirius": (6.75, -16.72, -1.46, "CMa"),
    "Adhara": (6.98, -28.97, 1.50, "CMa"),
    "Wezen": (7.14, -26.39, 1.84, "CMa"),
    "Mirzam": (6.38, -17.96, 1.98, "CMa"),
    "Aludra": (7.40, -29.30, 2.45, "CMa"),
    "Furud": (6.34, -30.06, 3.02, "CMa"),
    # Aquila
    "Altair": (19.85, 8.87, 0.76, "Aql"),
    "Tarazed": (19.77, 10.61, 2.72, "Aql"),
    "Alshain": (19.92, 6.41, 3.71, "Aql"),
    "Theta Aql": (20.19, -0.82, 3.23, "Aql"),
    "Delta Aql": (19.42, 3.11, 3.36, "Aql"),
    # Bootes
    "Arcturus": (14.26, 19.18, -0.05, "Boo"),
    "Izar": (14.75, 27.07, 2.37, "Boo"),
    "Muphrid": (13.91, 18.40, 2.68, "Boo"),
    "Nekkar": (15.03, 40.39, 3.58, "Boo"),
    "Seginus": (14.53, 38.31, 3.03, "Boo"),
    # Perseus
    "Mirfak": (3.41, 49.86, 1.80, "Per"),
    "Algol": (3.14, 40.96, 2.12, "Per"),
    "Zeta Per": (3.90, 31.88, 2.85, "Per"),
    "Epsilon Per": (3.96, 40.01, 2.89, "Per"),
    "Delta Per": (3.72, 47.79, 3.01, "Per"),
    # Auriga
    "Capella": (5.27, 45.99, 0.08, "Aur"),
    "Menkalinan": (5.99, 44.95, 1.90, "Aur"),
    "Theta Aur": (5.99, 37.21, 2.62, "Aur"),
    "Hassaleh": (4.95, 33.17, 2.69, "Aur"),
    "Almaaz": (5.03, 43.82, 2.99, "Aur"),
    # Virgo
    "Spica": (13.42, -11.16, 0.97, "Vir"),
    "Porrima": (12.69, -1.45, 2.74, "Vir"),
    "Vindemiatrix": (13.04, 10.96, 2.83, "Vir"),
    "Heze": (13.58, -0.60, 3.37, "Vir"),
    "Zaniah": (12.33, -0.67, 3.89, "Vir"),
    # Corona Borealis
    "Alphecca": (15.58, 26.71, 2.23, "CrB"),
    "Nusakan": (15.46, 29.11, 3.68, "CrB"),
    "Gamma CrB": (15.71, 26.30, 3.84, "CrB"),
    "Delta CrB": (15.83, 26.07, 4.59, "CrB"),
    # Pegasus
    "Enif": (21.74, 9.88, 2.39, "Peg"),
    "Markab": (23.08, 15.21, 2.49, "Peg"),
    "Scheat": (23.06, 28.08, 2.42, "Peg"),
    "Algenib": (0.22, 15.18, 2.83, "Peg"),
    "Matar": (22.72, 30.22, 2.94, "Peg"),
    # Andromeda
    "Alpheratz": (0.14, 29.09, 2.06, "And"),
    "Mirach": (1.16, 35.62, 2.05, "And"),
    "Almach": (2.07, 42.33, 2.17, "And"),
    # Draco
    "Eltanin": (17.94, 51.49, 2.24, "Dra"),
    "Rastaban": (17.51, 52.30, 2.79, "Dra"),
    "Thuban": (14.07, 64.38, 3.65, "Dra"),
    "Grumium": (17.89, 56.87, 3.75, "Dra"),
    "Kuma": (17.53, 55.17, 4.87, "Dra"),
    # Hercules
    "Kornephoros": (16.50, 21.49, 2.77, "Her"),
    "Zeta Her": (16.69, 31.60, 2.81, "Her"),
    "Rasalgethi": (17.24, 14.39, 3.37, "Her"),
    "Sarin": (17.25, 24.84, 3.14, "Her"),
    "Pi Her": (17.25, 36.81, 3.16, "Her"),
    "Eta Her": (16.71, 38.92, 3.53, "Her"),
    # Sagittarius
    "Kaus Australis": (18.40, -34.38, 1.85, "Sgr"),
    "Nunki": (18.92, -26.30, 2.02, "Sgr"),
    "Ascella": (19.04, -29.88, 2.59, "Sgr"),
    "Kaus Media": (18.35, -29.83, 2.70, "Sgr"),
    "Kaus Borealis": (18.47, -25.42, 2.81, "Sgr"),
    "Nash": (18.10, -30.42, 3.11, "Sgr"),
}

# Constellation stick-figure edges
edges = [
    # Orion
    ("Betelgeuse", "Bellatrix"),
    ("Betelgeuse", "Mintaka"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Rigel", "Alnitak"),
    ("Rigel", "Saiph"),
    ("Saiph", "Alnitak"),
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
    ("Regulus", "Eta Leo"),
    ("Eta Leo", "Algieba"),
    ("Algieba", "Zosma"),
    ("Zosma", "Denebola"),
    ("Regulus", "Chertan"),
    ("Chertan", "Denebola"),
    # Scorpius
    ("Acrab", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Wei"),
    ("Wei", "Shaula"),
    ("Shaula", "Lesath"),
    ("Wei", "Sargas"),
    # Cygnus (Northern Cross)
    ("Deneb", "Sadr"),
    ("Sadr", "Albireo"),
    ("Sadr", "Gienah Cyg"),
    ("Sadr", "Delta Cyg"),
    # Lyra
    ("Vega", "Sheliak"),
    ("Vega", "Sulafat"),
    ("Sheliak", "Sulafat"),
    # Gemini
    ("Castor", "Pollux"),
    ("Castor", "Mebsuta"),
    ("Mebsuta", "Tejat"),
    ("Pollux", "Wasat"),
    ("Wasat", "Alhena"),
    # Taurus
    ("Aldebaran", "Ain"),
    ("Ain", "Prima Hyadum"),
    ("Aldebaran", "Elnath"),
    ("Ain", "Alcyone"),
    ("Elnath", "Tianguan"),
    # Canis Major
    ("Sirius", "Mirzam"),
    ("Sirius", "Adhara"),
    ("Adhara", "Wezen"),
    ("Wezen", "Aludra"),
    ("Adhara", "Furud"),
    # Aquila
    ("Altair", "Tarazed"),
    ("Altair", "Alshain"),
    ("Altair", "Theta Aql"),
    ("Altair", "Delta Aql"),
    # Bootes
    ("Arcturus", "Muphrid"),
    ("Arcturus", "Izar"),
    ("Izar", "Seginus"),
    ("Seginus", "Nekkar"),
    # Perseus
    ("Mirfak", "Delta Per"),
    ("Mirfak", "Epsilon Per"),
    ("Epsilon Per", "Algol"),
    ("Algol", "Zeta Per"),
    # Auriga
    ("Capella", "Menkalinan"),
    ("Menkalinan", "Theta Aur"),
    ("Theta Aur", "Hassaleh"),
    ("Hassaleh", "Almaaz"),
    ("Almaaz", "Capella"),
    # Virgo
    ("Spica", "Heze"),
    ("Heze", "Porrima"),
    ("Porrima", "Zaniah"),
    ("Porrima", "Vindemiatrix"),
    # Corona Borealis
    ("Alphecca", "Nusakan"),
    ("Alphecca", "Gamma CrB"),
    ("Gamma CrB", "Delta CrB"),
    # Pegasus (Great Square)
    ("Markab", "Scheat"),
    ("Scheat", "Algenib"),
    ("Markab", "Enif"),
    ("Markab", "Algenib"),
    # Andromeda
    ("Alpheratz", "Mirach"),
    ("Mirach", "Almach"),
    ("Alpheratz", "Scheat"),
    # Draco
    ("Eltanin", "Rastaban"),
    ("Rastaban", "Kuma"),
    ("Kuma", "Grumium"),
    ("Eltanin", "Grumium"),
    # Hercules
    ("Kornephoros", "Zeta Her"),
    ("Zeta Her", "Eta Her"),
    ("Eta Her", "Pi Her"),
    ("Kornephoros", "Rasalgethi"),
    ("Rasalgethi", "Sarin"),
    ("Sarin", "Pi Her"),
    # Sagittarius (Teapot)
    ("Kaus Australis", "Kaus Media"),
    ("Kaus Media", "Kaus Borealis"),
    ("Kaus Borealis", "Nunki"),
    ("Nunki", "Ascella"),
    ("Ascella", "Kaus Australis"),
    ("Nash", "Kaus Media"),
]

# Background stars
n_bg = 300
bg_ra_hours = np.random.uniform(0, 24, n_bg)
bg_dec_deg = np.random.uniform(-45, 70, n_bg)
bg_mag = np.random.uniform(4.0, 6.0, n_bg)

# Extract star data
star_names = list(stars.keys())
star_ra_h = np.array([stars[s][0] for s in star_names])
star_dec_d = np.array([stars[s][1] for s in star_names])
star_mag = np.array([stars[s][2] for s in star_names])

# Convert to radians for Aitoff projection
# Aitoff expects longitude in [-pi, pi] and latitude in [-pi/2, pi/2]
# RA: map 0-24h -> negate and shift so RA increases right-to-left (standard sky chart)
star_lon = -((star_ra_h - 12.0) * np.pi / 12.0)
star_lat = star_dec_d * np.pi / 180.0
bg_lon = -((bg_ra_hours - 12.0) * np.pi / 12.0)
bg_lat = bg_dec_deg * np.pi / 180.0

# Size mapping: brighter stars (lower mag) get larger points
max_mag = 6.5
min_mag = -1.5
min_size = 10
max_size = 420
star_sizes = max_size * ((max_mag - star_mag) / (max_mag - min_mag)) ** 1.5 + min_size
bg_sizes = max_size * ((max_mag - bg_mag) / (max_mag - min_mag)) ** 1.5 + min_size

# Color mapping by magnitude using a custom colormap (warm white to cool blue-gray)
star_cmap = LinearSegmentedColormap.from_list(
    "star_temp", ["#FFFFFF", "#E8E8FF", "#C8C8F0", "#A0A0D0", "#8888B8"], N=256
)
# Normalize magnitude to [0, 1] range for colormap (bright=0, dim=1)
star_color_norm = np.clip((star_mag - min_mag) / (max_mag - min_mag), 0, 1)
star_colors = star_cmap(star_color_norm)

# Create figure using matplotlib's Aitoff projection
fig = plt.figure(figsize=(16, 9), facecolor="#0A0A2A")
ax = fig.add_subplot(111, projection="aitoff", facecolor="#0A0A2A")

# Plot background stars
ax.scatter(bg_lon, bg_lat, s=bg_sizes, c="#707090", alpha=0.35, edgecolors="none", zorder=1)

# Draw constellation lines
for s1, s2 in edges:
    if s1 in stars and s2 in stars:
        lon1 = -((stars[s1][0] - 12.0) * np.pi / 12.0)
        lat1 = stars[s1][1] * np.pi / 180.0
        lon2 = -((stars[s2][0] - 12.0) * np.pi / 12.0)
        lat2 = stars[s2][1] * np.pi / 180.0
        # Skip lines that wrap around the projection boundary
        if abs(lon1 - lon2) > np.pi:
            continue
        ax.plot([lon1, lon2], [lat1, lat2], color="#3A5A8C", linewidth=1.4, alpha=0.55, zorder=2)

# Plot named stars with subtle glow effect using PathEffects
ax.scatter(
    star_lon,
    star_lat,
    s=star_sizes,
    c=star_colors,
    alpha=0.92,
    edgecolors="white",
    linewidth=0.3,
    zorder=3,
    path_effects=[pe.withSimplePatchShadow(offset=(0, 0), shadow_rgbFace="#4060A0", alpha=0.25, rho=0.4)],
)
# Extra glow layer for brightest stars (mag < 1.0)
bright_mask = star_mag < 1.0
ax.scatter(
    star_lon[bright_mask],
    star_lat[bright_mask],
    s=star_sizes[bright_mask] * 2.5,
    c="#4060B0",
    alpha=0.08,
    edgecolors="none",
    zorder=2,
)

# Draw ecliptic (obliquity ~23.44 degrees)
ecl_lon_range = np.linspace(-np.pi, np.pi, 500)
# Ecliptic in equatorial coords: Dec = arcsin(sin(obliquity) * sin(ecliptic_lon))
# Simplified: Dec = obliquity * sin(RA), mapping ecliptic longitude to RA
ecl_lat = 23.44 * np.sin(-ecl_lon_range) * np.pi / 180.0
ax.plot(
    ecl_lon_range, ecl_lat, color="#8B6914", linewidth=1.8, alpha=0.5, linestyle=(0, (8, 4)), zorder=1, label="Ecliptic"
)

# Label brightest stars (mag < 1.0) with smart offsets
bright_offsets = {
    "Sirius": (14, 12),
    "Vega": (12, 12),
    "Arcturus": (12, -16),
    "Capella": (-58, 10),
    "Rigel": (12, -16),
    "Betelgeuse": (12, 12),
    "Altair": (12, -16),
    "Aldebaran": (-62, -12),
    "Spica": (-50, -14),
    "Pollux": (12, 12),
}
for name, (ra, dec, mag, _) in stars.items():
    if mag < 1.0:
        lon = -((ra - 12.0) * np.pi / 12.0)
        lat = dec * np.pi / 180.0
        offset = bright_offsets.get(name, (12, 10))
        ax.annotate(
            name,
            (lon, lat),
            fontsize=14,
            color="#C8C8E0",
            alpha=0.88,
            xytext=offset,
            textcoords="offset points",
            fontweight="light",
            zorder=5,
            path_effects=[pe.withStroke(linewidth=3, foreground="#0A0A2A", alpha=0.7)],
        )

# Constellation name labels at centroid with overlap avoidance
constellation_names = {
    "Ori": "Orion",
    "UMa": "Ursa Major",
    "Cas": "Cassiopeia",
    "Leo": "Leo",
    "Sco": "Scorpius",
    "Cyg": "Cygnus",
    "Lyr": "Lyra",
    "Gem": "Gemini",
    "Tau": "Taurus",
    "CMa": "Canis Major",
    "Aql": "Aquila",
    "Boo": "Bo\u00f6tes",
    "Per": "Perseus",
    "Aur": "Auriga",
    "Vir": "Virgo",
    "CrB": "Corona Bor.",
    "Peg": "Pegasus",
    "And": "Andromeda",
    "Dra": "Draco",
    "Her": "Hercules",
    "Sgr": "Sagittarius",
}

# Manual offsets (in radians) for crowded regions — tuned to avoid overlap
label_offsets_rad = {
    "CrB": (0.0, -0.18),
    "Her": (0.15, 0.15),
    "Boo": (-0.15, -0.18),
    "Lyr": (-0.12, -0.15),
    "Tau": (0.18, 0.12),
    "Gem": (-0.08, 0.15),
    "CMa": (-0.15, 0.18),
    "Dra": (0.0, 0.10),
    "Cyg": (0.10, 0.12),
    "Aql": (0.0, -0.15),
    "Sco": (-0.28, 0.10),
    "Sgr": (0.28, 0.0),
    "Vir": (0.15, -0.20),
    "And": (0.0, 0.12),
    "Per": (0.0, -0.12),
    "Ori": (0.08, -0.22),
    "Leo": (0.0, -0.10),
}

placed_labels = []
for abbr, full_name in constellation_names.items():
    members = [(s, stars[s]) for s in star_names if stars[s][3] == abbr]
    if not members:
        continue
    member_lons = [-((d[0] - 12.0) * np.pi / 12.0) for _, d in members]
    member_lats = [d[1] * np.pi / 180.0 for _, d in members]
    cx = np.mean(member_lons)
    cy = np.mean(member_lats) - 0.06

    dx, dy = label_offsets_rad.get(abbr, (0.0, 0.0))
    cx += dx
    cy += dy

    # Iterative nudge away from previously placed labels
    for _ in range(3):
        for px, py in placed_labels:
            if abs(cx - px) < 0.22 and abs(cy - py) < 0.12:
                cy -= 0.13
                break
        else:
            break

    placed_labels.append((cx, cy))
    ax.text(
        cx,
        cy,
        full_name,
        fontsize=13,
        color="#6A7A9A",
        alpha=0.75,
        ha="center",
        va="top",
        fontstyle="italic",
        fontweight="medium",
        zorder=4,
        path_effects=[pe.withStroke(linewidth=4, foreground="#0A0A2A", alpha=0.6)],
    )

# Style the Aitoff grid
ax.grid(True, color="#152040", linewidth=0.4, alpha=0.35, linestyle=(0, (5, 8)))
ax.tick_params(axis="both", colors="#4A5A7A", labelsize=16, length=0, labelcolor="#6A7A9A")

# Customize RA tick labels to show hours
# Aitoff default x-ticks are in degrees; replace with hour labels
xtick_locs = np.array([-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150])
xtick_rads = xtick_locs * np.pi / 180.0
# Convert projected longitude back to RA hours: RA = 12 - lon*12/pi
xtick_hours = 12.0 - xtick_locs / 15.0
xtick_labels = [f"{int(h) % 24}h" for h in xtick_hours]
ax.set_xticklabels(xtick_labels, fontsize=16, color="#6A7A9A")

# Title
ax.set_title(
    "star-chart-constellation \u00b7 matplotlib \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="medium",
    color="#C0C8E0",
    pad=24,
)

# Add projection and coordinate info as text annotations
fig.text(
    0.5,
    0.02,
    "Right Ascension (hours) \u2014 Aitoff Projection  |  Declination (\u00b0)",
    ha="center",
    fontsize=20,
    color="#8A9ABB",
)

# Ecliptic legend
ax.legend(
    loc="lower right", fontsize=16, facecolor="#0A0A2A", edgecolor="#2A3A5A", labelcolor="#8B6914", framealpha=0.8
)

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
