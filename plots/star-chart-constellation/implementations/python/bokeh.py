"""anyplot.ai
star-chart-constellation: Star Chart with Constellations
Library: bokeh | Python 3.14
Quality: pending | Created: 2026-06-17
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label, LabelSet, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome").
# A star chart is intrinsically a night-sky view, so the two themes are read as:
#   dark  -> literal night sky: pale stars on near-black #1A1A17
#   light -> antique engraved star atlas: ink stars on warm cream #FAF8F1
# Star MAGNITUDE is encoded by point SIZE (the real data dimension); the star tone
# only flips with the theme so the chart stays legible on both surfaces.
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Sky-specific theme tones (structural chrome, not categorical data)
STAR_BRIGHT = "#1A1A17" if THEME == "light" else "#FFFDE7"
STAR_MID = "#3D4D6B" if THEME == "light" else "#DDE3F0"
STAR_DIM = "#8089A0" if THEME == "light" else "#9FB0C4"
LINE_COLOR = "#4467A3" if THEME == "light" else "#5E7BB5"  # Imprint blue (lightened on dark)
GRID_COLOR = "#C2C8D6" if THEME == "light" else "#3D4A66"
GRID_LABEL = "#7A8398" if THEME == "light" else "#6E7C9E"
CNAME_COLOR = "#5A6478" if THEME == "light" else "#9BA6BD"  # constellation names
SNAME_COLOR = "#2A2A26" if THEME == "light" else "#D6DCE6"  # bright star names

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
    ("Dschubba", 16.01, -22.62, 2.32, "Sco"),
    ("Graffias", 16.09, -19.81, 2.62, "Sco"),
    ("Pi Sco", 15.98, -26.11, 2.89, "Sco"),
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
    # Canis Minor / Sirius region kept north of the crop
    ("Sirius", 6.75, -16.72, -1.46, "CMa"),
    ("Mirzam", 6.38, -17.96, 1.98, "CMa"),
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
    # Corona / Hercules anchor
    ("Rasalgethi", 17.24, 14.39, 3.49, "Her"),
    ("Kornephoros", 16.50, 21.49, 2.78, "Her"),
]

# Background stars for realism, drawn within the visible northern view
n_bg = 220
bg_ra = np.random.uniform(0, 24, n_bg)
bg_dec = np.random.uniform(-25, 82, n_bg)
bg_mag = np.random.uniform(3.6, 5.4, n_bg)
for i in range(n_bg):
    stars_data.append((f"BG{i}", bg_ra[i], bg_dec[i], bg_mag[i], ""))

# Parse star data
star_names = [s[0] for s in stars_data]
ra_hours = np.array([s[1] for s in stars_data])
dec_deg = np.array([s[2] for s in stars_data])
magnitudes = np.array([s[3] for s in stars_data])
constellations = [s[4] for s in stars_data]

# Stereographic projection (north celestial pole centered)
ra_rad = ra_hours * (2 * np.pi / 24)
dec_rad = np.deg2rad(dec_deg)
r = np.cos(dec_rad) / (1 + np.sin(dec_rad))
proj_x = -r * np.cos(ra_rad)  # flip x so RA increases right-to-left (sky convention)
proj_y = r * np.sin(ra_rad)

# Invert magnitude to point size: brighter (lower mag) = bigger
mag_min, mag_max = magnitudes.min(), magnitudes.max()
size_min, size_max = 4, 40
sizes = size_min + (size_max - size_min) * (mag_max - magnitudes) / (mag_max - mag_min)

# Star tone by magnitude (brightest -> brightest tone for the theme)
star_colors = []
for m in magnitudes:
    frac = (m - mag_min) / (mag_max - mag_min)
    if frac < 0.3:
        star_colors.append(STAR_BRIGHT)
    elif frac < 0.6:
        star_colors.append(STAR_MID)
    else:
        star_colors.append(STAR_DIM)

# Constellation stick-figure edges (pairs of star names)
edges = [
    ("Betelgeuse", "Bellatrix"),
    ("Bellatrix", "Mintaka"),
    ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"),
    ("Betelgeuse", "Alnilam"),
    ("Alnitak", "Saiph"),
    ("Mintaka", "Rigel"),
    ("Rigel", "Saiph"),
    ("Dubhe", "Merak"),
    ("Merak", "Phecda"),
    ("Phecda", "Megrez"),
    ("Megrez", "Dubhe"),
    ("Megrez", "Alioth"),
    ("Alioth", "Mizar"),
    ("Mizar", "Alkaid"),
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
    ("Delta Cyg", "Sadr"),
    ("Sadr", "Gienah Cyg"),
    ("Graffias", "Dschubba"),
    ("Dschubba", "Antares"),
    ("Antares", "Pi Sco"),
    ("Castor", "Pollux"),
    ("Castor", "Mebsuta"),
    ("Mebsuta", "Tejat"),
    ("Pollux", "Alhena"),
    ("Vega", "Sheliak"),
    ("Sheliak", "Sulafat"),
    ("Sulafat", "Vega"),
    ("Altair", "Tarazed"),
    ("Altair", "Alshain"),
    ("Aldebaran", "Tianguan"),
    ("Tianguan", "Elnath"),
    ("Aldebaran", "Alcyone"),
    ("Sirius", "Mirzam"),
    ("Mirfak", "Algol"),
    ("Mirfak", "Epsilon Per"),
    ("Epsilon Per", "Zeta Per"),
    ("Capella", "Menkalinan"),
    ("Menkalinan", "Theta Aur"),
    ("Arcturus", "Izar"),
    ("Arcturus", "Muphrid"),
    ("Alpheratz", "Mirach"),
    ("Mirach", "Almach"),
    ("Markab", "Algenib"),
    ("Algenib", "Alpheratz"),
    ("Alpheratz", "Scheat"),
    ("Scheat", "Markab"),
    ("Eltanin", "Rastaban"),
    ("Rasalgethi", "Kornephoros"),
]

name_to_idx = {name: i for i, name in enumerate(star_names)}

# Plot — square canvas (sky projection has no preferred horizontal axis)
title = "star-chart-constellation · python · bokeh · anyplot.ai"
p = figure(
    width=2400,
    height=2400,
    title=title,
    tools="pan,wheel_zoom,box_zoom,reset,hover",
    toolbar_location=None,  # bokeh's default toolbar shrinks the saved PNG below height=
    match_aspect=True,
    tooltips=[("Star", "@name"), ("Magnitude", "@mag")],
    min_border_left=40,
    min_border_right=40,
    min_border_top=100,
    min_border_bottom=40,
)
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

view_range = 1.6

# RA/Dec coordinate grid
# Declination circles (celestial equator + northern parallels)
for dec_grid in range(0, 90, 30):
    dec_r = np.deg2rad(dec_grid)
    r_circle = np.cos(dec_r) / (1 + np.sin(dec_r))
    theta_vals = np.linspace(0, 2 * np.pi, 200)
    gx = -r_circle * np.cos(theta_vals)
    gy = r_circle * np.sin(theta_vals)
    p.line(gx, gy, line_color=GRID_COLOR, line_alpha=0.7, line_width=1.5, line_dash="dotted")
    # Skip the innermost (+60°) label — it collapses into the crowded pole region
    if dec_grid <= 30:
        dec_label = Label(
            x=-r_circle,
            y=0.0,
            text=f"+{dec_grid}°",
            text_font_size="18pt",
            text_color=GRID_LABEL,
            x_offset=6,
            y_offset=-6,
        )
        p.add_layout(dec_label)

# RA meridians
for ra_grid in range(0, 24, 3):
    ra_r = ra_grid * (2 * np.pi / 24)
    dec_vals = np.linspace(-24, 89, 100)
    r_vals = np.cos(np.deg2rad(dec_vals)) / (1 + np.sin(np.deg2rad(dec_vals)))
    gx = -r_vals * np.cos(ra_r)
    gy = r_vals * np.sin(ra_r)
    p.line(gx, gy, line_color=GRID_COLOR, line_alpha=0.7, line_width=1.5, line_dash="dotted")
    # Label each meridian just inside the chart edge
    edge_r = np.cos(np.deg2rad(-18)) / (1 + np.sin(np.deg2rad(-18)))
    lx = -edge_r * np.cos(ra_r)
    ly = edge_r * np.sin(ra_r)
    if abs(lx) < view_range - 0.05 and abs(ly) < view_range - 0.05:
        ra_label = Label(
            x=lx, y=ly, text=f"{ra_grid}h", text_font_size="16pt", text_color=GRID_LABEL, x_offset=5, y_offset=5
        )
        p.add_layout(ra_label)

# Constellation stick-figure lines
for s1_name, s2_name in edges:
    if s1_name in name_to_idx and s2_name in name_to_idx:
        i1, i2 = name_to_idx[s1_name], name_to_idx[s2_name]
        p.line(
            [proj_x[i1], proj_x[i2]], [proj_y[i1], proj_y[i2]], line_color=LINE_COLOR, line_alpha=0.5, line_width=2.5
        )

# Stars
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
p.scatter(x="x", y="y", size="size", color="color", alpha=0.92, line_color=None, source=source)

# Constellation names near each group centroid
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
    "Her": "Hercules",
}
# Per-constellation label offsets (px) to clear bright-star labels
constellation_offsets = {
    "Aur": (-90, -40),  # clear Capella label
    "Lyr": (60, -10),  # clear Vega label
    "Aql": (-95, -8),  # clear Altair label
    "Boo": (60, -10),  # clear Arcturus label
    "Ori": (-100, -10),
    "Per": (-60, 10),
    "CrB": (10, 30),
    "Her": (20, -30),
}

constellation_set = sorted({c for c in constellations if c})
label_x, label_y, label_text = [], [], []
label_x_offset, label_y_offset = [], []
for c in constellation_set:
    idxs = [i for i, cn in enumerate(constellations) if cn == c]
    cx, cy = np.mean(proj_x[idxs]), np.mean(proj_y[idxs])
    if abs(cx) > view_range or abs(cy) > view_range:
        continue
    label_x.append(cx)
    label_y.append(cy)
    label_text.append(constellation_full_names.get(c, c))
    ox, oy = constellation_offsets.get(c, (0, -34))
    label_x_offset.append(ox)
    label_y_offset.append(oy)

constellation_source = ColumnDataSource(
    data={"x": label_x, "y": label_y, "text": label_text, "x_offset": label_x_offset, "y_offset": label_y_offset}
)
constellation_labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=constellation_source,
    x_offset="x_offset",
    y_offset="y_offset",
    text_font_size="20pt",
    text_color=CNAME_COLOR,
    text_font_style="italic",
    text_align="center",
)
p.add_layout(constellation_labels)

# Bright named stars (mag < 1.0) — placed above their star, with a few overrides
bright_star_offsets = {
    "Capella": (0, 36),
    "Vega": (-18, 34),
    "Altair": (16, 34),
    "Deneb": (0, 36),
    "Arcturus": (-18, 34),
    "Antares": (0, -42),
    "Sirius": (0, 38),
}
bx, by, btext = [], [], []
bxo, byo = [], []
for i, (name, mag) in enumerate(zip(star_names, magnitudes, strict=False)):
    if mag < 1.0 and not name.startswith("BG"):
        if abs(proj_x[i]) > view_range or abs(proj_y[i]) > view_range:
            continue
        bx.append(proj_x[i])
        by.append(proj_y[i])
        btext.append(name)
        ox, oy = bright_star_offsets.get(name, (0, 34))
        bxo.append(ox)
        byo.append(oy)

bright_source = ColumnDataSource(data={"x": bx, "y": by, "text": btext, "x_offset": bxo, "y_offset": byo})
bright_labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=bright_source,
    x_offset="x_offset",
    y_offset="y_offset",
    text_font_size="17pt",
    text_color=SNAME_COLOR,
    text_align="center",
)
p.add_layout(bright_labels)

# Magnitude scale legend (bottom-left)
legend_mags = [0, 1, 2, 3, 4]
legend_x_base = -1.42
legend_y_base = -1.30
p.add_layout(
    Label(
        x=legend_x_base - 0.02,
        y=legend_y_base + 0.12,
        text="Magnitude",
        text_font_size="18pt",
        text_color=INK_SOFT,
        text_font_style="bold",
    )
)
for j, lm in enumerate(legend_mags):
    lx = legend_x_base + j * 0.13
    ls = size_min + (size_max - size_min) * (mag_max - lm) / (mag_max - mag_min)
    lc = STAR_BRIGHT if lm < 1.5 else STAR_MID if lm < 3 else STAR_DIM
    p.scatter([lx], [legend_y_base], size=ls, color=lc, alpha=0.92, line_color=None)
    p.add_layout(
        Label(
            x=lx, y=legend_y_base - 0.10, text=str(lm), text_font_size="15pt", text_color=INK_SOFT, text_align="center"
        )
    )

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.outline_line_color = INK_SOFT
p.outline_line_alpha = 0.4
p.x_range = Range1d(-view_range, view_range)
p.y_range = Range1d(-view_range, view_range)

# Save — interactive HTML + headless-Chrome screenshot (export_png is unavailable here)
output_file(f"plot-{THEME}.html", title="Star Chart with Constellations")
save(p)

W, H = 2400, 2400
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
# Compensate for browser chrome so the inner viewport is exactly W x H
inner_w, inner_h = driver.execute_script("return [window.innerWidth, window.innerHeight];")
driver.set_window_size(W + (W - inner_w), H + (H - inner_h))
time.sleep(1)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
