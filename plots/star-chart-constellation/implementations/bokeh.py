""" pyplots.ai
star-chart-constellation: Star Chart with Constellations
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-18
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label, LabelSet, Range1d
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data
np.random.seed(42)

# Star catalog: (name, RA in hours, Dec in degrees, magnitude, constellation)
stars_data = [
    # Orion
    ("Betelgeuse", 5.92, 7.41, 0.42, "Ori"),
    ("Rigel", 5.24, -8.20, 0.13, "Ori"),
    ("Bellatrix", 5.42, 6.35, 1.64, "Ori"),
    ("Mintaka", 5.53, -0.30, 2.23, "Ori"),
    ("Alnilam", 5.60, -1.20, 1.69, "Ori"),
    ("Alnitak", 5.68, -1.94, 1.77, "Ori"),
    ("Saiph", 5.80, -9.67, 2.09, "Ori"),
    # Ursa Major
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
    ("Denebola", 11.82, 14.57, 2.13, "Leo"),
    ("Algieba", 10.33, 19.84, 2.28, "Leo"),
    ("Zosma", 11.24, 20.52, 2.56, "Leo"),
    ("Chertan", 11.24, 15.43, 3.33, "Leo"),
    # Cygnus
    ("Deneb", 20.69, 45.28, 1.25, "Cyg"),
    ("Sadr", 20.37, 40.26, 2.20, "Cyg"),
    ("Gienah Cyg", 20.77, 33.97, 2.46, "Cyg"),
    ("Delta Cyg", 19.75, 45.13, 2.87, "Cyg"),
    ("Albireo", 19.51, 27.96, 3.08, "Cyg"),
    # Scorpius
    ("Antares", 16.49, -26.43, 0.96, "Sco"),
    ("Shaula", 17.56, -37.10, 1.63, "Sco"),
    ("Sargas", 17.62, -42.99, 1.87, "Sco"),
    ("Dschubba", 16.01, -22.62, 2.32, "Sco"),
    ("Graffias", 16.09, -19.81, 2.62, "Sco"),
    ("Epsilon Sco", 16.84, -34.29, 2.29, "Sco"),
    ("Kappa Sco", 17.71, -39.03, 2.41, "Sco"),
    # Gemini
    ("Pollux", 7.76, 28.03, 1.14, "Gem"),
    ("Castor", 7.58, 31.89, 1.58, "Gem"),
    ("Alhena", 6.63, 16.40, 1.93, "Gem"),
    ("Tejat", 6.38, 22.51, 2.88, "Gem"),
    ("Mebsuta", 6.73, 25.13, 2.98, "Gem"),
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
    ("Mirfak", 3.41, 49.86, 1.80, "Per"),
    ("Algol", 3.14, 40.96, 2.12, "Per"),
    ("Zeta Per", 3.90, 31.88, 2.85, "Per"),
    ("Epsilon Per", 3.96, 40.01, 2.89, "Per"),
    # Auriga
    ("Capella", 5.28, 46.00, 0.08, "Aur"),
    ("Menkalinan", 5.99, 44.95, 1.90, "Aur"),
    ("Theta Aur", 5.99, 37.21, 2.62, "Aur"),
    # Bootes
    ("Arcturus", 14.26, 19.18, -0.05, "Boo"),
    ("Izar", 14.75, 27.07, 2.37, "Boo"),
    ("Muphrid", 13.91, 18.40, 2.68, "Boo"),
    # Corona Borealis
    ("Alphecca", 15.58, 26.71, 2.23, "CrB"),
    ("Nusakan", 15.46, 29.11, 3.68, "CrB"),
    # Andromeda
    ("Alpheratz", 0.14, 29.09, 2.06, "And"),
    ("Mirach", 1.16, 35.62, 2.05, "And"),
    ("Almach", 2.07, 42.33, 2.17, "And"),
    # Pegasus
    ("Markab", 23.08, 15.21, 2.49, "Peg"),
    ("Scheat", 23.06, 28.08, 2.42, "Peg"),
    ("Algenib", 0.22, 15.18, 2.84, "Peg"),
    # Draco
    ("Eltanin", 17.94, 51.49, 2.23, "Dra"),
    ("Rastaban", 17.51, 52.30, 2.79, "Dra"),
    ("Thuban", 14.07, 64.38, 3.65, "Dra"),
    # Southern constellations for better coverage
    # Centaurus
    ("Rigil Kent", 14.66, -60.84, -0.01, "Cen"),
    ("Hadar", 14.06, -60.37, 0.61, "Cen"),
    ("Menkent", 14.11, -36.37, 2.06, "Cen"),
    # Crux (Southern Cross)
    ("Acrux", 12.44, -63.10, 0.76, "Cru"),
    ("Mimosa", 12.80, -59.69, 1.25, "Cru"),
    ("Gacrux", 12.52, -57.11, 1.63, "Cru"),
    ("Delta Cru", 12.25, -58.75, 2.80, "Cru"),
    # Puppis
    ("Naos", 8.06, -40.00, 2.25, "Pup"),
    ("Pi Pup", 7.29, -37.10, 2.71, "Pup"),
    # Vela
    ("Gamma Vel", 8.16, -47.34, 1.78, "Vel"),
    ("Delta Vel", 8.74, -54.71, 1.96, "Vel"),
    ("Kappa Vel", 9.37, -55.01, 2.50, "Vel"),
    # Carina
    ("Canopus", 6.40, -52.70, -0.74, "Car"),
    ("Avior", 8.38, -59.51, 1.86, "Car"),
    ("Miaplacidus", 9.22, -69.72, 1.68, "Car"),
]

# Add background stars for realism
n_bg = 200
bg_ra = np.random.uniform(0, 24, n_bg)
bg_dec = np.random.uniform(-70, 70, n_bg)
bg_mag = np.random.uniform(3.5, 5.5, n_bg)
for i in range(n_bg):
    stars_data.append((f"BG{i}", bg_ra[i], bg_dec[i], bg_mag[i], ""))

# Parse star data
star_names = [s[0] for s in stars_data]
ra_hours = np.array([s[1] for s in stars_data])
dec_deg = np.array([s[2] for s in stars_data])
magnitudes = np.array([s[3] for s in stars_data])
constellations = [s[4] for s in stars_data]

# Stereographic projection (north pole centered)
ra_rad = ra_hours * (2 * np.pi / 24)
dec_rad = np.deg2rad(dec_deg)
r = np.cos(dec_rad) / (1 + np.sin(dec_rad))
proj_x = r * np.cos(ra_rad)
proj_y = r * np.sin(ra_rad)

# Flip x so RA increases right-to-left (astronomical convention)
proj_x = -proj_x

# Invert magnitude to point size: brighter = bigger
mag_min, mag_max = magnitudes.min(), magnitudes.max()
size_min, size_max = 3, 42
sizes = size_min + (size_max - size_min) * (mag_max - magnitudes) / (mag_max - mag_min)

# Star colors based on magnitude (brighter = more yellow-white, dimmer = blue-white)
star_colors = []
for m in magnitudes:
    frac = (m - mag_min) / (mag_max - mag_min)
    if frac < 0.3:
        star_colors.append("#FFFDE7")
    elif frac < 0.6:
        star_colors.append("#E8EAF6")
    else:
        star_colors.append("#B0BEC5")

# Constellation edges (pairs of star names)
edges = [
    # Orion
    ("Betelgeuse", "Bellatrix"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Betelgeuse", "Alnilam"),
    ("Alnitak", "Saiph"),
    ("Mintaka", "Rigel"),
    ("Rigel", "Saiph"),
    # Ursa Major (Big Dipper)
    ("Dubhe", "Merak"),
    ("Merak", "Phecda"),
    ("Phecda", "Megrez"),
    ("Megrez", "Dubhe"),
    ("Megrez", "Alioth"),
    ("Alioth", "Mizar"),
    ("Mizar", "Alkaid"),
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
    # Cygnus (Northern Cross)
    ("Deneb", "Sadr"),
    ("Sadr", "Albireo"),
    ("Delta Cyg", "Sadr"),
    ("Sadr", "Gienah Cyg"),
    # Scorpius
    ("Graffias", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Epsilon Sco"),
    ("Epsilon Sco", "Shaula"),
    ("Shaula", "Kappa Sco"),
    ("Kappa Sco", "Sargas"),
    # Gemini
    ("Castor", "Pollux"),
    ("Castor", "Mebsuta"),
    ("Mebsuta", "Tejat"),
    ("Pollux", "Alhena"),
    # Lyra
    ("Vega", "Sheliak"),
    ("Sheliak", "Sulafat"),
    ("Sulafat", "Vega"),
    # Aquila
    ("Altair", "Tarazed"),
    ("Altair", "Alshain"),
    # Taurus
    ("Aldebaran", "Tianguan"),
    ("Tianguan", "Elnath"),
    ("Aldebaran", "Alcyone"),
    # Canis Major
    ("Sirius", "Mirzam"),
    ("Sirius", "Adhara"),
    ("Adhara", "Wezen"),
    ("Wezen", "Aludra"),
    # Perseus
    ("Mirfak", "Algol"),
    ("Mirfak", "Epsilon Per"),
    ("Epsilon Per", "Zeta Per"),
    # Auriga
    ("Capella", "Menkalinan"),
    ("Menkalinan", "Theta Aur"),
    # Bootes
    ("Arcturus", "Izar"),
    ("Arcturus", "Muphrid"),
    # Andromeda
    ("Alpheratz", "Mirach"),
    ("Mirach", "Almach"),
    # Pegasus (Great Square partial)
    ("Markab", "Algenib"),
    ("Algenib", "Alpheratz"),
    ("Alpheratz", "Scheat"),
    ("Scheat", "Markab"),
    # Draco (partial)
    ("Eltanin", "Rastaban"),
    # Centaurus
    ("Rigil Kent", "Hadar"),
    ("Hadar", "Menkent"),
    # Crux (Southern Cross)
    ("Acrux", "Gacrux"),
    ("Mimosa", "Delta Cru"),
    # Puppis
    ("Naos", "Pi Pup"),
    # Vela
    ("Gamma Vel", "Delta Vel"),
    ("Delta Vel", "Kappa Vel"),
    # Carina
    ("Canopus", "Avior"),
    ("Avior", "Miaplacidus"),
]

# Build star name to index lookup
name_to_idx = {name: i for i, name in enumerate(star_names)}

# Plot
p = figure(
    width=3600,
    height=3600,
    title="star-chart-constellation · bokeh · pyplots.ai",
    x_axis_label="",
    y_axis_label="",
    tools="pan,wheel_zoom,box_zoom,reset,hover",
    match_aspect=True,
    tooltips=[("Star", "@name"), ("Magnitude", "@mag")],
)

# Dark sky background
p.background_fill_color = "#0a0e2a"
p.border_fill_color = "#060818"

# Draw RA/Dec coordinate grid with labels
grid_color = "#253070"
grid_alpha = 0.7

# Declination circles with labels
for dec_grid in range(-60, 90, 30):
    dec_r = np.deg2rad(dec_grid)
    r_circle = np.cos(dec_r) / (1 + np.sin(dec_r))
    theta_vals = np.linspace(0, 2 * np.pi, 200)
    gx = -r_circle * np.cos(theta_vals)
    gy = r_circle * np.sin(theta_vals)
    p.line(gx, gy, line_color=grid_color, line_alpha=grid_alpha, line_width=1.5, line_dash="dotted")
    # Label declination at RA=0h position (right side of chart)
    lx = -r_circle
    ly = 0.0
    dec_label = Label(
        x=lx,
        y=ly,
        text=f"{dec_grid}°",
        text_font_size="16pt",
        text_color="#5577aa",
        text_alpha=0.85,
        x_offset=5,
        y_offset=-5,
    )
    p.add_layout(dec_label)

# RA lines with labels
for ra_grid in range(0, 24, 3):
    ra_r = ra_grid * (2 * np.pi / 24)
    dec_vals = np.linspace(-70, 89, 100)
    dec_r_vals = np.deg2rad(dec_vals)
    r_vals = np.cos(dec_r_vals) / (1 + np.sin(dec_r_vals))
    gx = -r_vals * np.cos(ra_r)
    gy = r_vals * np.sin(ra_r)
    p.line(gx, gy, line_color=grid_color, line_alpha=grid_alpha, line_width=1.5, line_dash="dotted")
    # Label RA at the outer edge (near dec=-30)
    edge_dec = np.deg2rad(-30)
    edge_r = np.cos(edge_dec) / (1 + np.sin(edge_dec))
    lx = -edge_r * np.cos(ra_r)
    ly = edge_r * np.sin(ra_r)
    ra_label = Label(
        x=lx,
        y=ly,
        text=f"{ra_grid}h",
        text_font_size="14pt",
        text_color="#5577aa",
        text_alpha=0.85,
        x_offset=5,
        y_offset=5,
    )
    p.add_layout(ra_label)

# Draw constellation lines
for s1_name, s2_name in edges:
    if s1_name in name_to_idx and s2_name in name_to_idx:
        i1 = name_to_idx[s1_name]
        i2 = name_to_idx[s2_name]
        p.line([proj_x[i1], proj_x[i2]], [proj_y[i1], proj_y[i2]], line_color="#4a6fa5", line_alpha=0.5, line_width=2)

# Plot stars
source = ColumnDataSource(
    data={
        "x": proj_x,
        "y": proj_y,
        "size": sizes,
        "color": star_colors,
        "name": star_names,
        "mag": [f"{m:.1f}" for m in magnitudes],
    }
)

p.scatter(x="x", y="y", size="size", color="color", alpha=0.9, line_color=None, source=source)

# Label constellation names at centroids with adjusted offsets to avoid overlap
constellation_set = sorted({c for c in constellations if c})
constellation_full_names = {
    "Ori": "Orion",
    "UMa": "Ursa Major",
    "Cas": "Cassiopeia",
    "Leo": "Leo",
    "Cyg": "Cygnus",
    "Sco": "Scorpius",
    "Gem": "Gemini",
    "Lyr": "Lyra",
    "Aql": "Aquila",
    "Tau": "Taurus",
    "CMa": "Canis Major",
    "Per": "Perseus",
    "Aur": "Auriga",
    "Boo": "Boötes",
    "CrB": "Corona Bor.",
    "And": "Andromeda",
    "Peg": "Pegasus",
    "Dra": "Draco",
    "Cen": "Centaurus",
    "Cru": "Crux",
    "Pup": "Puppis",
    "Vel": "Vela",
    "Car": "Carina",
}

# Custom label offsets to avoid overlap with bright star labels
constellation_offsets = {
    "Aur": (30, 30),
    "Lyr": (-70, -20),
    "Aql": (20, 25),
    "CrB": (15, 25),
    "Boo": (20, 30),
    "Cyg": (20, 30),
    "Per": (-55, 20),
}

label_x = []
label_y = []
label_text = []
label_x_offset = []
label_y_offset = []
for c in constellation_set:
    idxs = [i for i, cn in enumerate(constellations) if cn == c]
    cx = np.mean(proj_x[idxs])
    cy = np.mean(proj_y[idxs])
    label_x.append(cx)
    label_y.append(cy)
    label_text.append(constellation_full_names.get(c, c))
    ox, oy = constellation_offsets.get(c, (10, 12))
    label_x_offset.append(ox)
    label_y_offset.append(oy)

label_source = ColumnDataSource(
    data={"x": label_x, "y": label_y, "text": label_text, "x_offset": label_x_offset, "y_offset": label_y_offset}
)

labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=label_source,
    x_offset="x_offset",
    y_offset="y_offset",
    text_font_size="18pt",
    text_color="#8899bb",
    text_alpha=0.75,
    text_font_style="italic",
)
p.add_layout(labels)

# Label bright named stars (mag < 1.0) with offset adjustments to avoid overlap
bright_star_offsets = {
    "Capella": (18, -30),
    "Vega": (18, -30),
    "Altair": (-60, -10),
    "Canopus": (18, -25),
    "Rigil Kent": (18, -25),
    "Deneb": (18, 15),
    "Arcturus": (-70, -10),
}

bright_names_x = []
bright_names_y = []
bright_names_text = []
bright_x_offsets = []
bright_y_offsets = []
for i, (name, mag) in enumerate(zip(star_names, magnitudes, strict=False)):
    if mag < 1.0 and not name.startswith("BG"):
        bright_names_x.append(proj_x[i])
        bright_names_y.append(proj_y[i])
        bright_names_text.append(name)
        ox, oy = bright_star_offsets.get(name, (15, -22))
        bright_x_offsets.append(ox)
        bright_y_offsets.append(oy)

bright_source = ColumnDataSource(
    data={
        "x": bright_names_x,
        "y": bright_names_y,
        "text": bright_names_text,
        "x_offset": bright_x_offsets,
        "y_offset": bright_y_offsets,
    }
)

bright_labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=bright_source,
    x_offset="x_offset",
    y_offset="y_offset",
    text_font_size="15pt",
    text_color="#c8d8e8",
    text_alpha=0.85,
)
p.add_layout(bright_labels)

# Magnitude scale legend (bottom-left corner)
legend_mags = [0, 1, 2, 3, 4, 5]
legend_x_base = -1.35
legend_y_base = -1.25
legend_title = Label(
    x=legend_x_base,
    y=legend_y_base + 0.08,
    text="Magnitude",
    text_font_size="14pt",
    text_color="#8899bb",
    text_font_style="bold",
)
p.add_layout(legend_title)

for j, lm in enumerate(legend_mags):
    lx = legend_x_base + j * 0.07
    ly = legend_y_base
    ls = size_min + (size_max - size_min) * (mag_max - lm) / (mag_max - mag_min)
    p.scatter(
        [lx],
        [ly],
        size=ls,
        color="#FFFDE7" if lm < 2 else "#E8EAF6" if lm < 4 else "#B0BEC5",
        alpha=0.9,
        line_color=None,
    )
    mag_label = Label(
        x=lx,
        y=ly - 0.06,
        text=str(lm),
        text_font_size="12pt",
        text_color="#8899bb",
        text_alpha=0.8,
        text_align="center",
    )
    p.add_layout(mag_label)

# Style
p.title.text_font_size = "36pt"
p.title.text_color = "#c8d8e8"
p.title.align = "center"

p.xaxis.visible = False
p.yaxis.visible = False

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

p.outline_line_color = "#1a2555"
p.outline_line_width = 2

view_range = 1.45
p.x_range = Range1d(-view_range, view_range)
p.y_range = Range1d(-view_range, view_range)

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Star Chart with Constellations")
