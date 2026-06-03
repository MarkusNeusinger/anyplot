"""anyplot.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: pygal | Python 3.13
Quality: pending | Created: 2026-06-03
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — hybrid-v3 sort; position 1 (#009E73) always first series
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data: Synthetic 1H NMR spectrum of ethanol (CH3-CH2-OH)
np.random.seed(42)
chemical_shift = np.linspace(0, 12, 6000)
w = 0.010  # Lorentzian half-width for multiplet peaks

# Build spectrum with Lorentzian line shapes: h·w²/((x−c)²+w²)
intensity = np.zeros_like(chemical_shift)

# TMS reference peak at 0 ppm (singlet)
intensity += 0.30 * 0.008**2 / ((chemical_shift - 0.00) ** 2 + 0.008**2)

# CH3 triplet near 1.18 ppm (1:2:1 intensity pattern, J = 7 Hz)
tc, j = 1.18, 0.07
intensity += 0.50 * w**2 / ((chemical_shift - (tc - j)) ** 2 + w**2)
intensity += 1.00 * w**2 / ((chemical_shift - tc) ** 2 + w**2)
intensity += 0.50 * w**2 / ((chemical_shift - (tc + j)) ** 2 + w**2)

# CH2 quartet near 3.69 ppm (1:3:3:1 intensity pattern, J = 7 Hz)
qc = 3.69
intensity += 0.25 * w**2 / ((chemical_shift - (qc - 1.5 * j)) ** 2 + w**2)
intensity += 0.75 * w**2 / ((chemical_shift - (qc - 0.5 * j)) ** 2 + w**2)
intensity += 0.75 * w**2 / ((chemical_shift - (qc + 0.5 * j)) ** 2 + w**2)
intensity += 0.25 * w**2 / ((chemical_shift - (qc + 1.5 * j)) ** 2 + w**2)

# OH singlet near 2.61 ppm
intensity += 0.35 * 0.015**2 / ((chemical_shift - 2.61) ** 2 + 0.015**2)

# Subtle baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

# Downsample for pygal performance (every 6th point → ~1000 points)
cs_plot = chemical_shift[::6]
int_plot = intensity[::6]

# Negate x-values to reverse axis (NMR convention: high ppm on left)
cs_negated = -cs_plot

# Peak annotations with functional group labels
peak_info = [(0.00, "TMS"), (1.18, "CH₃ triplet"), (2.61, "OH singlet"), (3.69, "CH₂ quartet")]

# Style — Imprint palette, theme-adaptive chrome, canonical 3200×1800 sizing
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    stroke_width=2.5,
)

# Chart — 3200×1800 landscape (canonical canvas for native-pixel pygal)
title = "Ethanol ¹H NMR · spectrum-nmr · python · pygal · anyplot.ai"
chart = pygal.XY(
    style=custom_style,
    width=3200,
    height=1800,
    title=title,
    x_title="Chemical Shift (ppm)",
    y_title="Intensity (a.u.)",
    show_dots=False,
    print_labels=True,
    print_values=False,
    show_x_guides=False,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=20,
    xrange=(-12.5, 0.8),
    range=(-0.02, 1.12),
    margin=35,
    margin_top=60,
    margin_bottom=150,
    margin_left=75,
    margin_right=140,
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    x_value_formatter=lambda x: f"{abs(x):.1f}",
    y_value_formatter=lambda y: f"{y:.3f}",
    x_labels_major_every=2,
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.axis > .line { stroke: transparent !important; }",
        f"inline:.text-overlay .series .label {{ font-size: 40px !important; fill: {INK} !important; font-weight: bold !important; }}",
    ],
)

# Spectrum line — stroke_style width=4 for crisp visibility at 3200×1800
spectrum_points = [(float(cs), float(inten)) for cs, inten in zip(cs_negated, int_plot, strict=False)]
chart.add("¹H NMR Spectrum", spectrum_points, stroke_style={"width": 4}, fill=False)

# Peak markers — each as its own series for legend and on-chart annotation
for ppm, group_name in peak_info:
    mask = np.abs(chemical_shift - ppm) < 0.15
    region_idx = np.where(mask)[0]
    idx = int(region_idx[np.argmax(intensity[region_idx])])
    peak_x = -float(chemical_shift[idx])
    peak_y = float(intensity[idx])
    label_text = f"{group_name} ({ppm:.2f} ppm)"
    legend_label = f"{group_name} ({ppm:.1f})"
    point = {"value": (peak_x, peak_y), "label": label_text}
    chart.add(legend_label, [point], stroke=False, show_dots=True, dots_size=14)

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
