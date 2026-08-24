"""anyplot.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: pygal | Python 3.13
Quality: pending | Created: 2026-08-24
"""

import os

import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (first series always brand green) + semantic anchors.
# Series color order below matches the exact chart.add() call order further down
# (pygal has no per-series color override, so this is how each series gets its hue).
ANYPLOT_NEUTRAL = INK  # baseline / reference-line role (theme-adaptive)
ANYPLOT_MUTED = INK_MUTED  # secondary construction-line role (theme-adaptive)
SERIES_COLORS = (
    "#009E73",
    "#C475FD",
    "#4467A3",
    ANYPLOT_NEUTRAL,
    ANYPLOT_MUTED,
    ANYPLOT_NEUTRAL,
    ANYPLOT_NEUTRAL,
    "#AE3030",
)

# Data - mild steel tensile test: elastic modulus, 0.2% offset yield, UTS, necking to fracture
np.random.seed(42)
YOUNGS_MODULUS = 200_000  # MPa (200 GPa)
ELASTIC_LIMIT_STRAIN = 250.0 / YOUNGS_MODULUS  # end of the linear region, at 250 MPa
YIELD_STRAIN, YIELD_STRESS = 0.00325, 250.0  # 0.2% offset method: E * (strain - 0.002) = stress
UTS_STRAIN, UTS_STRESS = 0.21, 400.0
FRACTURE_STRAIN, FRACTURE_STRESS = 0.30, 330.0
PLATEAU_STRAIN_END = 0.02  # Luders plateau before strain hardening ramps up

elastic_strain = np.linspace(0, ELASTIC_LIMIT_STRAIN, 20)
elastic_stress = YOUNGS_MODULUS * elastic_strain

plateau_strain = np.linspace(ELASTIC_LIMIT_STRAIN, PLATEAU_STRAIN_END, 40)
plateau_stress = YIELD_STRESS + np.random.normal(0, 1.5, plateau_strain.size)

hardening_strain = np.linspace(PLATEAU_STRAIN_END, UTS_STRAIN, 140)
hardening_progress = (hardening_strain - PLATEAU_STRAIN_END) / (UTS_STRAIN - PLATEAU_STRAIN_END)
hardening_stress = YIELD_STRESS + (UTS_STRESS - YIELD_STRESS) * hardening_progress**0.4
hardening_stress += np.random.normal(0, 1.5, hardening_strain.size)

plastic_strain = np.concatenate([plateau_strain, hardening_strain])
plastic_stress = np.concatenate([plateau_stress, hardening_stress])

necking_strain = np.linspace(UTS_STRAIN, FRACTURE_STRAIN, 60)
necking_progress = (necking_strain - UTS_STRAIN) / (FRACTURE_STRAIN - UTS_STRAIN)
necking_stress = UTS_STRESS - (UTS_STRESS - FRACTURE_STRESS) * necking_progress**1.3
necking_stress += np.random.normal(0, 1.5, necking_strain.size)

# Construction lines for the 0.2% offset yield method (both capped at the same stress
# so the parallel, 0.002-strain-shifted geometry reads clearly)
construction_cap = 300.0
tangent_strain = (0, construction_cap / YOUNGS_MODULUS)
offset_strain = (0.002, construction_cap / YOUNGS_MODULUS + 0.002)

# Title - fontsize scales down only if the string exceeds the ~67-char baseline
title = "line-stress-strain · python · pygal · anyplot.ai"
title_font_size = 66 if len(title) <= 67 else max(44, round(66 * 67 / len(title)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=SERIES_COLORS,
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=40,
    value_font_size=36,
    stroke_width=5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title="Engineering Strain (mm/mm)",
    y_title="Engineering Stress (MPa)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_x_guides=False,
    show_y_guides=True,
    show_dots=False,
    margin=110,
    margin_bottom=260,
    margin_left=210,
    margin_right=90,
    xrange=(0, 0.33),
    range=(0, 440),
    x_labels_major_count=7,
    show_minor_x_labels=False,
    truncate_legend=-1,
)
chart.x_labels = [round(v, 2) for v in np.linspace(0, 0.30, 7)]

# Curve, split into the three labeled mechanical regions
chart.add("Elastic", list(zip(elastic_strain, elastic_stress, strict=True)), stroke_style={"width": 5})
chart.add(
    "Plastic (Strain Hardening)", list(zip(plastic_strain, plastic_stress, strict=True)), stroke_style={"width": 5}
)
chart.add("Necking", list(zip(necking_strain, necking_stress, strict=True)), stroke_style={"width": 5})

# 0.2% offset construction: elastic-modulus tangent + its 0.002-strain-shifted twin
chart.add(
    "Elastic Modulus (E ≈ 200 GPa)",
    [(tangent_strain[0], 0), (tangent_strain[1], construction_cap)],
    stroke_style={"width": 4, "dasharray": "18, 14"},
)
chart.add(
    "0.2% Offset Line",
    [(offset_strain[0], 0), (offset_strain[1], construction_cap)],
    stroke_style={"width": 4, "dasharray": "18, 14"},
)

# Critical points
chart.add(
    f"Yield Point (0.2% Offset) — {YIELD_STRESS:.0f} MPa",
    [(YIELD_STRAIN, YIELD_STRESS)],
    show_dots=True,
    dots_size=11,
    stroke=False,
)
chart.add(
    f"Ultimate Tensile Strength — {UTS_STRESS:.0f} MPa",
    [(UTS_STRAIN, UTS_STRESS)],
    show_dots=True,
    dots_size=11,
    stroke=False,
)
chart.add(
    f"Fracture Point — {FRACTURE_STRESS:.0f} MPa",
    [(FRACTURE_STRAIN, FRACTURE_STRESS)],
    show_dots=True,
    dots_size=11,
    stroke=False,
)

# Save
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
