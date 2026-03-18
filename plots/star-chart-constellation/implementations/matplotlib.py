"""pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-18
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Star catalog with RA (hours), Dec (degrees), magnitude, constellation
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

# Add faint background stars
n_bg = 300
bg_ra = np.random.uniform(0, 24, n_bg)
bg_dec = np.random.uniform(-45, 70, n_bg)
bg_mag = np.random.uniform(4.0, 6.0, n_bg)

# Extract star data arrays
star_names = list(stars.keys())
star_ra = np.array([stars[s][0] for s in star_names])
star_dec = np.array([stars[s][1] for s in star_names])
star_mag = np.array([stars[s][2] for s in star_names])
star_const = [stars[s][3] for s in star_names]

# Convert RA from hours to degrees for projection
ra_deg = star_ra * 15.0
bg_ra_deg = bg_ra * 15.0

# Size mapping: brighter stars (lower mag) get larger points
max_mag = 6.5
min_size = 8
max_size = 350
star_sizes = max_size * ((max_mag - star_mag) / (max_mag - (-1.5))) ** 1.5 + min_size
bg_sizes = max_size * ((max_mag - bg_mag) / (max_mag - (-1.5))) ** 1.5 + min_size

# Color mapping by magnitude: bright stars are warmer/whiter
star_colors = []
for m in star_mag:
    if m < 0.5:
        star_colors.append("#FFFFFF")
    elif m < 1.5:
        star_colors.append("#F0F0FF")
    elif m < 2.5:
        star_colors.append("#D8D8F0")
    elif m < 3.5:
        star_colors.append("#B8B8D8")
    else:
        star_colors.append("#9898C0")

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="#0A0A2A")
ax.set_facecolor("#0A0A2A")

# Plot background stars
ax.scatter(bg_ra_deg, bg_dec, s=bg_sizes, c="#707090", alpha=0.4, edgecolors="none", zorder=1)

# Draw constellation lines
for s1, s2 in edges:
    if s1 in stars and s2 in stars:
        ra1, dec1 = stars[s1][0] * 15.0, stars[s1][1]
        ra2, dec2 = stars[s2][0] * 15.0, stars[s2][1]
        ra_diff = abs(ra1 - ra2)
        if ra_diff > 180:
            continue
        ax.plot([ra1, ra2], [dec1, dec2], color="#3A5A8C", linewidth=1.2, alpha=0.55, zorder=2)

# Plot named stars
ax.scatter(ra_deg, star_dec, s=star_sizes, c=star_colors, alpha=0.9, edgecolors="white", linewidth=0.3, zorder=3)

# Label brightest stars (mag < 1.0)
for name, (ra, dec, mag, _) in stars.items():
    if mag < 1.0:
        ax.annotate(
            name,
            (ra * 15.0, dec),
            fontsize=9,
            color="#C8C8E0",
            alpha=0.8,
            xytext=(8, 8),
            textcoords="offset points",
            fontweight="light",
            zorder=5,
        )

# Constellation name labels at centroid
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
    "Boo": "Bootes",
    "Per": "Perseus",
    "Aur": "Auriga",
    "Vir": "Virgo",
    "CrB": "Corona Borealis",
    "Peg": "Pegasus",
    "And": "Andromeda",
    "Dra": "Draco",
    "Her": "Hercules",
    "Sgr": "Sagittarius",
}

for abbr, full_name in constellation_names.items():
    member_ra = [stars[s][0] * 15.0 for s in star_names if stars[s][3] == abbr]
    member_dec = [stars[s][1] for s in star_names if stars[s][3] == abbr]
    if member_ra:
        centroid_ra = np.mean(member_ra)
        centroid_dec = np.mean(member_dec) - 4.5
        ax.text(
            centroid_ra,
            centroid_dec,
            full_name,
            fontsize=10,
            color="#6A7A9A",
            alpha=0.7,
            ha="center",
            va="top",
            fontstyle="italic",
            fontweight="medium",
            zorder=4,
        )

# Style - coordinate grid
ax.set_xlim(360, 0)
ax.set_ylim(-50, 72)

ra_ticks = np.arange(0, 361, 30)
ra_labels = [f"{int(r / 15)}h" for r in ra_ticks]
ax.set_xticks(ra_ticks)
ax.set_xticklabels(ra_labels, fontsize=14, color="#6A7A9A")

dec_ticks = np.arange(-40, 71, 20)
dec_labels = [f"{d:+d}\u00b0" for d in dec_ticks]
ax.set_yticks(dec_ticks)
ax.set_yticklabels(dec_labels, fontsize=14, color="#6A7A9A")

ax.grid(True, color="#1A2A4A", linewidth=0.5, alpha=0.5, linestyle="--")
ax.tick_params(axis="both", colors="#4A5A7A", length=0)

for spine in ax.spines.values():
    spine.set_color("#1A2A4A")
    spine.set_linewidth(0.5)

ax.set_xlabel("Right Ascension", fontsize=18, color="#8A9ABB", labelpad=12)
ax.set_ylabel("Declination", fontsize=18, color="#8A9ABB", labelpad=12)
ax.set_title(
    "star-chart-constellation \u00b7 matplotlib \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="medium",
    color="#C0C8E0",
    pad=20,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
