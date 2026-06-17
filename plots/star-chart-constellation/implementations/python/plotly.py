""" anyplot.ai
star-chart-constellation: Star Chart with Constellations
Library: plotly 6.8.0 | Python 3.13.14
Quality: 90/100 | Updated: 2026-06-17
"""

import os
from collections import defaultdict

import numpy as np
import plotly.graph_objects as go


# Theme-adaptive chrome (Imprint tokens)
THEME = os.getenv("ANYPLOT_THEME", "light")
if THEME == "light":
    PAGE_BG = "#FAF8F1"
    ELEVATED_BG = "#FFFDF6"
    INK = "#1A1A17"
    INK_SOFT = "#4A4A44"
    INK_MUTED = "#6B6A63"
    LINE_COL = "rgba(74,74,68,0.52)"
    GRID_COL = "rgba(26,26,23,0.15)"
    EQUATOR_COL = "rgba(26,26,23,0.30)"
    BOUNDARY_COL = "rgba(74,74,68,0.55)"
    BG_STAR_COL = "rgba(107,106,99,0.45)"
    MW_COL = "rgba(107,106,99,0.06)"
else:
    PAGE_BG = "#1A1A17"
    ELEVATED_BG = "#242420"
    INK = "#F0EFE8"
    INK_SOFT = "#B8B7B0"
    INK_MUTED = "#A8A79F"
    LINE_COL = "rgba(184,183,176,0.55)"
    GRID_COL = "rgba(240,239,232,0.16)"
    EQUATOR_COL = "rgba(240,239,232,0.32)"
    BOUNDARY_COL = "rgba(184,183,176,0.55)"
    BG_STAR_COL = "rgba(184,183,176,0.50)"
    MW_COL = "rgba(168,167,159,0.10)"

# Continuous Imprint colormap (sequential): brand green -> blue. Maps bright
# (low magnitude) stars to #009E73 and faint stars toward #4467A3.
IMPRINT_SEQ = [[0.0, "#009E73"], [1.0, "#4467A3"]]
# Amber semantic anchor for the ecliptic reference line (constant across themes).
ECLIPTIC_COL = "rgba(221,204,119,0.60)"


# Azimuthal-equidistant projection centred on the North Celestial Pole.
# Co-declination is the true radial distance (deg); RA is the azimuth.
def project(ra_hours, dec_deg):
    ra_rad = np.radians(np.asarray(ra_hours, dtype=float) * 15.0)
    r = 90.0 - np.asarray(dec_deg, dtype=float)
    return r * np.sin(ra_rad), r * np.cos(ra_rad)


# Galactic (l, b) -> equatorial (RA hours, Dec deg), J2000 pole constants.
def gal_to_eq(l_deg, b_deg):
    lon = np.radians(l_deg)
    b = np.radians(b_deg)
    a_ngp = np.radians(192.85948)
    d_ngp = np.radians(27.12825)
    l_ncp = np.radians(122.93192)
    sin_d = np.sin(d_ngp) * np.sin(b) + np.cos(d_ngp) * np.cos(b) * np.cos(l_ncp - lon)
    dec = np.arcsin(sin_d)
    yy = np.cos(b) * np.sin(l_ncp - lon)
    xx = np.cos(d_ngp) * np.sin(b) - np.sin(d_ngp) * np.cos(b) * np.cos(l_ncp - lon)
    ra = (a_ngp + np.arctan2(yy, xx)) % (2 * np.pi)
    return np.degrees(ra) / 15.0, np.degrees(dec)


# Data - Notable stars with RA (hours), Dec (degrees), magnitude, constellation
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

# Geometry of the planisphere (radius = co-declination, degrees)
R_BOUNDARY = 156.0  # outer frame, just beyond the southernmost catalogued stars
DEC_RINGS = [60, 30, 0, -30, -60]  # labelled declination circles

# Project the named stars
star_names = list(stars.keys())
ra_h = np.array([stars[s][0] for s in star_names])
dec = np.array([stars[s][1] for s in star_names])
mag = np.array([stars[s][2] for s in star_names])
star_x, star_y = project(ra_h, dec)

# Magnitude -> marker size (brighter / lower magnitude = larger)
max_size, min_size = 15.0, 2.5
mag_min, mag_max = mag.min(), mag.max()
sizes = max_size - (mag - mag_min) / (mag_max - mag_min) * (max_size - min_size)

# Dimmer background star field, projected within the visible cap
bg_ra = np.random.uniform(0, 24, 220)
bg_dec = np.random.uniform(-58, 87, 220)
bg_x, bg_y = project(bg_ra, bg_dec)

fig = go.Figure()

# Milky Way band - faint filled great-circle ribbon (galactic latitude +/-12 deg)
gl = np.linspace(0, 360, 361)
mw_ra_top, mw_dec_top = gal_to_eq(gl, 12.0)
mw_ra_bot, mw_dec_bot = gal_to_eq(gl[::-1], -12.0)
mw_xt, mw_yt = project(mw_ra_top, mw_dec_top)
mw_xb, mw_yb = project(mw_ra_bot, mw_dec_bot)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([mw_xt, mw_xb]),
        y=np.concatenate([mw_yt, mw_yb]),
        mode="lines",
        fill="toself",
        fillcolor=MW_COL,
        line={"width": 0},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Coordinate grid - declination rings + right-ascension spokes
ring_x, ring_y = [], []
for dec_ring in DEC_RINGS:
    if dec_ring == 0:
        continue  # equator drawn separately, emphasised
    rr = 90.0 - dec_ring
    th = np.linspace(0, 2 * np.pi, 240)
    ring_x.extend((rr * np.cos(th)).tolist() + [None])
    ring_y.extend((rr * np.sin(th)).tolist() + [None])

spoke_x, spoke_y = [], []
for h in range(0, 24, 2):
    a = np.radians(h * 15)
    spoke_x.extend([0.0, 150.0 * np.sin(a), None])
    spoke_y.extend([0.0, 150.0 * np.cos(a), None])

fig.add_trace(
    go.Scatter(
        x=ring_x + spoke_x,
        y=ring_y + spoke_y,
        mode="lines",
        line={"color": GRID_COL, "width": 0.7},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Celestial equator (dec = 0) - emphasised reference circle
th = np.linspace(0, 2 * np.pi, 300)
fig.add_trace(
    go.Scatter(
        x=90.0 * np.cos(th),
        y=90.0 * np.sin(th),
        mode="lines",
        line={"color": EQUATOR_COL, "width": 1.0},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Outer sky boundary
fig.add_trace(
    go.Scatter(
        x=R_BOUNDARY * np.cos(th),
        y=R_BOUNDARY * np.sin(th),
        mode="lines",
        line={"color": BOUNDARY_COL, "width": 1.2},
        hoverinfo="skip",
        showlegend=False,
    )
)

# Ecliptic - amber dashed great circle (23.44 deg inclined to the equator)
ecl_lon = np.linspace(0, 360, 361)
obliquity = np.radians(23.44)
ecl_ra = np.degrees(np.arctan2(np.sin(np.radians(ecl_lon)) * np.cos(obliquity), np.cos(np.radians(ecl_lon)))) / 15.0
ecl_dec = np.degrees(np.arcsin(np.sin(np.radians(ecl_lon)) * np.sin(obliquity)))
ecl_x, ecl_y = project(ecl_ra % 24, ecl_dec)
fig.add_trace(
    go.Scatter(
        x=ecl_x,
        y=ecl_y,
        mode="lines",
        line={"color": ECLIPTIC_COL, "width": 1.4, "dash": "dash"},
        name="Ecliptic",
        hoverinfo="skip",
        showlegend=False,
    )
)

# Constellation stick-figure lines (projected, single trace with separators)
line_x, line_y = [], []
for s1, s2 in edges:
    if s1 in stars and s2 in stars:
        x1, y1 = project(stars[s1][0], stars[s1][1])
        x2, y2 = project(stars[s2][0], stars[s2][1])
        line_x.extend([float(x1), float(x2), None])
        line_y.extend([float(y1), float(y2), None])

fig.add_trace(
    go.Scatter(
        x=line_x, y=line_y, mode="lines", line={"color": LINE_COL, "width": 1.2}, hoverinfo="skip", showlegend=False
    )
)

# Background stars (WebGL for the dense field)
fig.add_trace(
    go.Scattergl(
        x=bg_x, y=bg_y, mode="markers", marker={"size": 1.6, "color": BG_STAR_COL}, hoverinfo="skip", showlegend=False
    )
)

# Named stars - size + Imprint-sequential colour both encode magnitude
fig.add_trace(
    go.Scattergl(
        x=star_x,
        y=star_y,
        mode="markers",
        marker={
            "size": sizes,
            "color": mag,
            "colorscale": IMPRINT_SEQ,
            "cmin": -1.5,
            "cmax": 3.8,
            "opacity": 0.95,
            "line": {"width": 0},
            "colorbar": {
                "title": {"text": "Apparent magnitude", "font": {"size": 11, "color": INK}, "side": "top"},
                "orientation": "h",
                "x": 0.5,
                "xanchor": "center",
                "y": -0.06,
                "yanchor": "top",
                "len": 0.46,
                "thickness": 14,
                "tickfont": {"size": 9, "color": INK_SOFT},
                "tickvals": [-1, 0, 1, 2, 3],
                "outlinewidth": 0,
            },
        },
        text=[
            f"{name}<br>Mag {stars[name][2]:.2f}<br>{constellation_names.get(stars[name][3], stars[name][3])}"
            for name in star_names
        ],
        hoverinfo="text",
        showlegend=False,
    )
)

# Annotations: constellation labels, grid labels, brightest-star labels
ann = []

# Constellation names at each group's projected centroid, nudged radially out
groups = defaultdict(list)
for i, name in enumerate(star_names):
    groups[stars[name][3]].append((star_x[i], star_y[i]))
centroids = {}
for abbr, pts in groups.items():
    centroids[abbr] = (float(np.mean([p[0] for p in pts])), float(np.mean([p[1] for p in pts])))
    if len(pts) < 2:
        continue  # skip single-star constellations to avoid clutter
    cx, cy = centroids[abbr]
    rad = np.hypot(cx, cy) or 1.0
    ann.append(
        {
            "x": cx + cx / rad * 9.0,
            "y": cy + cy / rad * 9.0,
            "text": constellation_names.get(abbr, abbr),
            "showarrow": False,
            "font": {"size": 10, "color": INK_SOFT, "family": "Arial"},
        }
    )

# Brightest stars (mag < 0.2) get individual labels, pushed away from the
# constellation-name centroid so the two labels never collide.
for i, name in enumerate(star_names):
    if mag[i] < 0.2:
        cx, cy = centroids[stars[name][3]]
        dx, dy = star_x[i] - cx, star_y[i] - cy
        d = np.hypot(dx, dy)
        if d < 1.0:  # star sits on the centroid -> push radially outward instead
            dx, dy = star_x[i], star_y[i]
            d = np.hypot(dx, dy) or 1.0
        ann.append(
            {
                "x": float(star_x[i] + dx / d * 9.0),
                "y": float(star_y[i] + dy / d * 9.0),
                "text": name,
                "showarrow": False,
                "font": {"size": 9, "color": INK, "family": "Arial"},
            }
        )

# Declination ring labels (placed along a clear gap between spokes)
for dec_ring in DEC_RINGS:
    rr = 90.0 - dec_ring
    a = np.radians(7)
    dec_label = f"{dec_ring:+d}°" if dec_ring != 0 else "0°"
    ann.append(
        {
            "x": float(rr * np.sin(a)),
            "y": float(rr * np.cos(a)),
            "text": dec_label,
            "showarrow": False,
            "font": {"size": 9, "color": INK_MUTED, "family": "Arial"},
        }
    )

# Right-ascension labels around the outer rim
for h in range(0, 24, 2):
    a = np.radians(h * 15)
    ann.append(
        {
            "x": float((R_BOUNDARY + 6) * np.sin(a)),
            "y": float((R_BOUNDARY + 6) * np.cos(a)),
            "text": f"{h}h",
            "showarrow": False,
            "font": {"size": 9, "color": INK_SOFT, "family": "Arial"},
        }
    )

# North Celestial Pole marker at the centre
ann.append(
    {"x": 0, "y": -7, "text": "NCP", "showarrow": False, "font": {"size": 8.5, "color": INK_MUTED, "family": "Arial"}}
)

axis_off = {"visible": False, "showgrid": False, "zeroline": False, "range": [-(R_BOUNDARY + 14), R_BOUNDARY + 14]}

fig.update_layout(
    title={
        "text": "star-chart-constellation · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK, "family": "Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={**axis_off, "scaleanchor": "y", "scaleratio": 1},
    yaxis=dict(axis_off),
    margin={"l": 40, "r": 40, "t": 70, "b": 90},
    annotations=ann,
)

# Save - square 2400 x 2400 (600 x 600 @ scale 4)
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
