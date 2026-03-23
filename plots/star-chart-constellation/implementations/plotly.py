""" pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: plotly 6.6.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-18
"""

from collections import defaultdict

import numpy as np
import plotly.graph_objects as go


# Data - Notable stars with RA (hours), Dec (degrees), magnitude
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
    # Scorpius
    "Antares": (16.49, -26.43, 1.09, "Sco"),
    "Shaula": (17.56, -37.10, 1.63, "Sco"),
    "Sargas": (17.62, -42.99, 1.87, "Sco"),
    "Dschubba": (16.01, -22.62, 2.32, "Sco"),
    "Graffias": (16.09, -19.81, 2.64, "Sco"),
    "Epsilon Sco": (16.84, -34.29, 2.29, "Sco"),
    "Kappa Sco": (17.71, -39.03, 2.41, "Sco"),
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
    "Delta1 Lyr": (18.91, 36.90, 4.22, "Lyr"),
    # Gemini
    "Castor": (7.58, 31.89, 1.58, "Gem"),
    "Pollux": (7.76, 28.03, 1.14, "Gem"),
    "Alhena": (6.63, 16.40, 1.93, "Gem"),
    "Tejat": (6.38, 22.51, 2.88, "Gem"),
    "Mebsuta": (6.73, 25.13, 3.06, "Gem"),
    # Taurus
    "Aldebaran": (4.60, 16.51, 0.85, "Tau"),
    "Elnath": (5.44, 28.61, 1.65, "Tau"),
    "Alcyone": (3.79, 24.11, 2.87, "Tau"),
    "Zeta Tau": (5.63, 21.14, 3.03, "Tau"),
    "Tau Epsilon": (4.48, 19.18, 3.53, "Tau"),
    # Canis Major
    "Sirius": (6.75, -16.72, -1.46, "CMa"),
    "Adhara": (6.98, -28.97, 1.50, "CMa"),
    "Wezen": (7.14, -26.39, 1.84, "CMa"),
    "Mirzam": (6.38, -17.96, 1.98, "CMa"),
    "Aludra": (7.40, -29.30, 2.45, "CMa"),
    # Aquila
    "Altair": (19.85, 8.87, 0.77, "Aql"),
    "Tarazed": (19.77, 10.61, 2.72, "Aql"),
    "Alshain": (19.92, 6.41, 3.71, "Aql"),
    # Boötes
    "Arcturus": (14.26, 19.18, -0.05, "Boo"),
    "Izar": (14.75, 27.07, 2.37, "Boo"),
    "Muphrid": (13.91, 18.40, 2.68, "Boo"),
    "Eta Boo": (13.85, 18.40, 2.68, "Boo"),
    # Auriga
    "Capella": (5.28, 46.00, 0.08, "Aur"),
    "Menkalinan": (5.99, 44.95, 1.90, "Aur"),
    "Theta Aur": (5.99, 37.21, 2.62, "Aur"),
    "Iota Aur": (4.95, 33.17, 2.69, "Aur"),
    # Perseus
    "Mirfak": (3.41, 49.86, 1.80, "Per"),
    "Algol": (3.14, 40.96, 2.12, "Per"),
    "Zeta Per": (3.90, 31.88, 2.85, "Per"),
    "Epsilon Per": (3.96, 40.01, 2.89, "Per"),
    # Virgo
    "Spica": (13.42, -11.16, 1.04, "Vir"),
    "Vindemiatrix": (13.04, 10.96, 2.83, "Vir"),
    "Porrima": (12.69, -1.45, 2.74, "Vir"),
    # Sagittarius
    "Kaus Australis": (18.40, -34.38, 1.85, "Sgr"),
    "Nunki": (18.92, -26.30, 2.02, "Sgr"),
    "Ascella": (19.04, -29.88, 2.59, "Sgr"),
    "Kaus Media": (18.35, -29.83, 2.70, "Sgr"),
    "Kaus Borealis": (18.47, -25.42, 2.81, "Sgr"),
    # Pegasus
    "Enif": (21.74, 9.88, 2.39, "Peg"),
    "Scheat": (23.06, 28.08, 2.42, "Peg"),
    "Markab": (23.08, 15.21, 2.49, "Peg"),
    "Algenib": (0.22, 15.18, 2.83, "Peg"),
    # Andromeda
    "Alpheratz": (0.14, 29.09, 2.06, "And"),
    "Mirach": (1.16, 35.62, 2.05, "And"),
    "Almach": (2.07, 42.33, 2.17, "And"),
    # Corona Borealis
    "Alphecca": (15.58, 26.71, 2.23, "CrB"),
    # Libra
    "Zubeneschamali": (15.28, -9.38, 2.61, "Lib"),
    "Zubenelgenubi": (14.85, -16.04, 2.75, "Lib"),
    # Aries
    "Hamal": (2.12, 23.46, 2.00, "Ari"),
    "Sheratan": (1.91, 20.81, 2.64, "Ari"),
    # Draco
    "Eltanin": (17.94, 51.49, 2.23, "Dra"),
    "Rastaban": (17.51, 52.30, 2.79, "Dra"),
    "Thuban": (14.07, 64.38, 3.65, "Dra"),
    "Eta Dra": (16.40, 61.51, 2.74, "Dra"),
    # Canis Minor
    "Procyon": (7.66, 5.22, 0.34, "CMi"),
    "Gomeisa": (7.45, 8.29, 2.90, "CMi"),
    # Pisces Austrinus
    "Fomalhaut": (22.96, -29.62, 1.16, "PsA"),
    # Centaurus
    "Rigil Kentaurus": (14.66, -60.83, -0.01, "Cen"),
    "Hadar": (14.06, -60.37, 0.61, "Cen"),
    # Crux
    "Acrux": (12.44, -63.10, 0.76, "Cru"),
    "Mimosa": (12.80, -59.69, 1.25, "Cru"),
    "Gacrux": (12.52, -57.11, 1.64, "Cru"),
    "Delta Cru": (12.25, -58.75, 2.80, "Cru"),
}

# Add dimmer background stars
bg_ra = np.random.uniform(0, 24, 200)
bg_dec = np.random.uniform(-70, 70, 200)
bg_mag = np.random.uniform(3.5, 5.0, 200)

# Constellation line connections (pairs of star names)
edges = [
    # Orion
    ("Betelgeuse", "Bellatrix"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Alnitak", "Saiph"),
    ("Saiph", "Rigel"),
    ("Rigel", "Mintaka"),
    ("Betelgeuse", "Alnitak"),
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
    ("Chertan", "Denebola"),
    ("Denebola", "Zosma"),
    ("Zosma", "Algieba"),
    ("Algieba", "Regulus"),
    # Scorpius
    ("Graffias", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Epsilon Sco"),
    ("Epsilon Sco", "Shaula"),
    ("Shaula", "Kappa Sco"),
    ("Kappa Sco", "Sargas"),
    # Cygnus
    ("Deneb", "Sadr"),
    ("Sadr", "Gienah Cyg"),
    ("Sadr", "Delta Cyg"),
    ("Sadr", "Albireo"),
    # Lyra
    ("Vega", "Sheliak"),
    ("Vega", "Sulafat"),
    ("Sheliak", "Sulafat"),
    # Gemini
    ("Castor", "Pollux"),
    ("Pollux", "Mebsuta"),
    ("Mebsuta", "Tejat"),
    ("Castor", "Mebsuta"),
    ("Pollux", "Alhena"),
    # Taurus
    ("Aldebaran", "Tau Epsilon"),
    ("Tau Epsilon", "Alcyone"),
    ("Aldebaran", "Zeta Tau"),
    ("Zeta Tau", "Elnath"),
    # Canis Major
    ("Sirius", "Mirzam"),
    ("Sirius", "Adhara"),
    ("Adhara", "Wezen"),
    ("Wezen", "Aludra"),
    # Aquila
    ("Altair", "Tarazed"),
    ("Altair", "Alshain"),
    # Boötes
    ("Arcturus", "Izar"),
    ("Arcturus", "Muphrid"),
    # Auriga
    ("Capella", "Menkalinan"),
    ("Menkalinan", "Theta Aur"),
    ("Theta Aur", "Iota Aur"),
    ("Iota Aur", "Capella"),
    # Perseus
    ("Mirfak", "Algol"),
    ("Mirfak", "Epsilon Per"),
    ("Epsilon Per", "Zeta Per"),
    # Andromeda
    ("Alpheratz", "Mirach"),
    ("Mirach", "Almach"),
    # Pegasus (Great Square)
    ("Alpheratz", "Scheat"),
    ("Scheat", "Markab"),
    ("Markab", "Algenib"),
    ("Algenib", "Alpheratz"),
    # Sagittarius (Teapot)
    ("Kaus Australis", "Kaus Media"),
    ("Kaus Media", "Kaus Borealis"),
    ("Kaus Borealis", "Nunki"),
    ("Nunki", "Ascella"),
    ("Ascella", "Kaus Australis"),
    # Aries
    ("Hamal", "Sheratan"),
    # Draco
    ("Eltanin", "Rastaban"),
    ("Rastaban", "Eta Dra"),
    ("Eta Dra", "Thuban"),
    # Canis Minor
    ("Procyon", "Gomeisa"),
    # Centaurus
    ("Rigil Kentaurus", "Hadar"),
    # Crux
    ("Acrux", "Gacrux"),
    ("Mimosa", "Delta Cru"),
    # Libra
    ("Zubeneschamali", "Zubenelgenubi"),
]

# Constellation full names for labels
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
    "Boo": "Boötes",
    "Aur": "Auriga",
    "Per": "Perseus",
    "Vir": "Virgo",
    "Sgr": "Sagittarius",
    "Peg": "Pegasus",
    "And": "Andromeda",
    "CrB": "Corona Borealis",
    "Lib": "Libra",
    "Ari": "Aries",
    "Dra": "Draco",
    "CMi": "Canis Minor",
    "PsA": "Piscis Austrinus",
    "Cen": "Centaurus",
    "Cru": "Crux",
}

# Convert RA (hours) to degrees for plotting
star_names = list(stars.keys())
ra_deg = np.array([stars[s][0] * 15 for s in star_names])
dec = np.array([stars[s][1] for s in star_names])
mag = np.array([stars[s][2] for s in star_names])

# Map magnitude to marker size (brighter = larger)
max_size = 24
min_size = 4
mag_min, mag_max = mag.min(), mag.max()
sizes = max_size - (mag - mag_min) / (mag_max - mag_min) * (max_size - min_size)

# Star color based on rough spectral type (magnitude as proxy)
star_colors = []
for m in mag:
    if m < 0.5:
        star_colors.append("#FFFDE8")
    elif m < 1.5:
        star_colors.append("#FFF8DC")
    elif m < 2.5:
        star_colors.append("#E8E4D4")
    else:
        star_colors.append("#C8C4B8")

# Background star sizes
bg_ra_deg = bg_ra * 15
bg_sizes = 2.0 * np.ones(len(bg_ra))

# Plot
fig = go.Figure()

# Background stars
fig.add_trace(
    go.Scattergl(
        x=bg_ra_deg,
        y=bg_dec,
        mode="markers",
        marker={"size": bg_sizes, "color": "rgba(180,180,200,0.4)", "symbol": "circle"},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Constellation lines - consolidated into single trace with None separators
line_x = []
line_y = []
for s1, s2 in edges:
    if s1 in stars and s2 in stars:
        x1, x2 = stars[s1][0] * 15, stars[s2][0] * 15
        y1, y2 = stars[s1][1], stars[s2][1]
        if abs(x2 - x1) > 180:
            continue
        line_x.extend([x1, x2, None])
        line_y.extend([y1, y2, None])

fig.add_trace(
    go.Scattergl(
        x=line_x,
        y=line_y,
        mode="lines",
        line={"color": "rgba(100,149,237,0.6)", "width": 1.8},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Named stars
fig.add_trace(
    go.Scattergl(
        x=ra_deg,
        y=dec,
        mode="markers",
        marker={"size": sizes, "color": star_colors, "line": {"width": 0}, "opacity": 0.95},
        text=[
            f"{name}<br>Mag: {stars[name][2]:.2f}<br>{constellation_names.get(stars[name][3], stars[name][3])}"
            for name in star_names
        ],
        hoverinfo="text",
        showlegend=False,
    )
)

# Constellation labels at centroid of each group - using annotations for reliable rendering
groups = defaultdict(list)
for name in star_names:
    c = stars[name][3]
    groups[c].append((stars[name][0] * 15, stars[name][1]))

constellation_annotations = []
for abbr, positions in groups.items():
    cx = np.mean([p[0] for p in positions])
    cy = np.mean([p[1] for p in positions]) + 4.0
    constellation_annotations.append(
        {
            "x": cx,
            "y": cy,
            "text": constellation_names.get(abbr, abbr),
            "showarrow": False,
            "font": {"size": 14, "color": "rgba(160,195,255,0.92)", "family": "Arial"},
            "yanchor": "bottom",
        }
    )

# Bright star name annotations (mag < 0.5)
for i, name in enumerate(star_names):
    if mag[i] < 0.5:
        constellation_annotations.append(
            {
                "x": ra_deg[i],
                "y": dec[i] + 2.0,
                "text": name,
                "showarrow": False,
                "font": {"size": 11, "color": "rgba(200,215,240,0.75)", "family": "Arial"},
                "yanchor": "bottom",
            }
        )

# Ecliptic line (approximate) as dashed curve
ecliptic_ra = np.linspace(0, 360, 360)
obliquity = 23.44
ecliptic_dec = obliquity * np.sin(np.radians(ecliptic_ra))
fig.add_trace(
    go.Scattergl(
        x=ecliptic_ra,
        y=ecliptic_dec,
        mode="lines",
        line={"color": "rgba(220,160,60,0.3)", "width": 1.2, "dash": "dash"},
        hoverinfo="skip",
        showlegend=False,
        name="Ecliptic",
    )
)

# Style
fig.update_layout(
    title={
        "text": "star-chart-constellation · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#C0D0E8", "family": "Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    plot_bgcolor="#0A0E1A",
    paper_bgcolor="#060A14",
    xaxis={
        "title": {"text": "Right Ascension", "font": {"size": 22, "color": "#7890A8"}},
        "tickfont": {"size": 16, "color": "#5A7090"},
        "range": [360, 0],
        "dtick": 30,
        "gridcolor": "rgba(60,80,120,0.18)",
        "gridwidth": 1,
        "showgrid": True,
        "zeroline": False,
        "tickvals": [h * 15 for h in range(0, 25, 2)],
        "ticktext": [f"{h}h" for h in range(0, 25, 2)],
        "linecolor": "rgba(60,80,120,0.3)",
    },
    yaxis={
        "title": {"text": "Declination (°)", "font": {"size": 22, "color": "#7890A8"}},
        "tickfont": {"size": 16, "color": "#5A7090"},
        "range": [-75, 75],
        "dtick": 15,
        "gridcolor": "rgba(60,80,120,0.18)",
        "gridwidth": 1,
        "showgrid": True,
        "zeroline": False,
        "linecolor": "rgba(60,80,120,0.3)",
        "ticksuffix": "°",
    },
    margin={"l": 80, "r": 40, "t": 70, "b": 70},
    width=1600,
    height=900,
    annotations=constellation_annotations,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
