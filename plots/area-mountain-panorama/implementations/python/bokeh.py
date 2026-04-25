""" anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 86/100 | Created: 2026-04-25
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import FixedTicker, Label
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1 — always first series

# Data — Wallis (Valais, Switzerland) summit panorama, ordered W → E
peaks = [
    ("Weisshorn", 8, 4506),
    ("Zinalrothorn", 20, 4221),
    ("Ober Gabelhorn", 31, 4063),
    ("Dent Blanche", 42, 4358),
    ("Matterhorn", 58, 4478),
    ("Breithorn", 72, 4164),
    ("Pollux", 81, 4092),
    ("Castor", 89, 4223),
    ("Liskamm", 97, 4527),
    ("Dufourspitze", 109, 4634),
    ("Strahlhorn", 121, 4190),
    ("Rimpfischhorn", 132, 4199),
    ("Allalinhorn", 142, 4027),
    ("Alphubel", 152, 4206),
    ("Täschhorn", 162, 4491),
    ("Dom", 174, 4545),
]

# Build ridgeline control points: peaks alternating with saddles (cols)
np.random.seed(42)
ctrl_x = [-3.0]
ctrl_y = [3250.0]
for i, (_, ang, el) in enumerate(peaks):
    ctrl_x.append(float(ang))
    ctrl_y.append(float(el))
    if i < len(peaks) - 1:
        next_ang = peaks[i + 1][1]
        next_el = peaks[i + 1][2]
        col_ang = (ang + next_ang) / 2 + np.random.uniform(-1.2, 1.2)
        col_drop = np.random.uniform(420, 820)
        col_el = min(el, next_el) - col_drop
        ctrl_x.append(float(col_ang))
        ctrl_y.append(float(col_el))
ctrl_x.append(184.0)
ctrl_y.append(3350.0)
ctrl_x = np.array(ctrl_x)
ctrl_y = np.array(ctrl_y)

# Smooth ridgeline via cosine smoothstep between adjacent control points
ridge_x = []
ridge_y = []
for i in range(len(ctrl_x) - 1):
    n = 80
    last = i == len(ctrl_x) - 2
    t = np.linspace(0.0, 1.0, n, endpoint=last)
    s = 0.5 - 0.5 * np.cos(np.pi * t)
    ridge_x.append(ctrl_x[i] + (ctrl_x[i + 1] - ctrl_x[i]) * t)
    ridge_y.append(ctrl_y[i] + (ctrl_y[i + 1] - ctrl_y[i]) * s)
ridge_x = np.concatenate(ridge_x)
ridge_y = np.concatenate(ridge_y)

# Anchor the silhouette polygon at the lower edge of the visible y-range
Y_FLOOR = 2500
poly_x = np.concatenate([[ridge_x[0]], ridge_x, [ridge_x[-1]]])
poly_y = np.concatenate([[Y_FLOOR], ridge_y, [Y_FLOOR]])

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Wallis 4000ers · area-mountain-panorama · bokeh · anyplot.ai",
    y_axis_label="Elevation (m)",
    x_range=(-3, 184),
    y_range=(Y_FLOOR, 5400),
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
    toolbar_location=None,
)

# Mountain silhouette (first categorical series — brand green)
p.patch(poly_x, poly_y, fill_color=BRAND, line_color=BRAND, line_width=2)

# Peak labels staggered across three vertical tiers, with thin leader lines + summit dots
LEVEL_TIERS = [4880, 5040, 5200]
labels = []
for i, (name, ang, el) in enumerate(peaks):
    label_y = LEVEL_TIERS[i % 3]
    is_focal = name == "Matterhorn"
    leader_color = INK if is_focal else INK_SOFT
    leader_alpha = 0.9 if is_focal else 0.55
    leader_width = 3.0 if is_focal else 1.8

    # Leader line from just above summit to just below the label block
    p.line(
        [ang, ang], [el + 25, label_y - 90], line_color=leader_color, line_alpha=leader_alpha, line_width=leader_width
    )

    # Summit dot — slightly larger and inked for the focal peak
    p.scatter(
        [ang],
        [el],
        size=26 if is_focal else 16,
        fill_color=INK if is_focal else INK_SOFT,
        line_color=PAGE_BG,
        line_width=2,
    )

    # Name (top of stacked label block)
    labels.append(
        Label(
            x=ang,
            y=label_y + 55,
            text=name,
            text_color=INK,
            text_font_size="24pt" if is_focal else "20pt",
            text_font_style="bold" if is_focal else "normal",
            text_align="center",
            text_baseline="bottom",
        )
    )

    # Elevation (bottom of stacked label block)
    labels.append(
        Label(
            x=ang,
            y=label_y + 30,
            text=f"{el:,} m",
            text_color=INK_SOFT,
            text_font_size="18pt",
            text_align="center",
            text_baseline="top",
        )
    )

for lbl in labels:
    p.add_layout(lbl)

# Typography
p.title.text_font_size = "36pt"
p.title.text_color = INK
p.title.text_font_style = "normal"
p.title.align = "center"

p.yaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_color = INK
p.yaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.yaxis.minor_tick_line_color = None
p.yaxis.ticker = FixedTicker(ticks=[2500, 3000, 3500, 4000, 4500, 5000])
p.yaxis.axis_label_standoff = 18

# Hide x-axis entirely — the panorama silhouette is the visual; bearings would clutter it
p.xaxis.visible = False

# Grid: y-only, very subtle
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="Wallis 4000ers · area-mountain-panorama · bokeh · anyplot.ai")
save(p)
