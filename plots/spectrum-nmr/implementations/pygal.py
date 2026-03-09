""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-09
"""

import numpy as np
import pygal
from pygal.style import Style


# Data: Synthetic 1H NMR spectrum of ethanol (CH3-CH2-OH)
np.random.seed(42)
chemical_shift = np.linspace(0, 12, 6000)
w = 0.010  # Lorentzian half-width for multiplet peaks

# Build spectrum with realistic splitting patterns using inline Lorentzian: h*w²/((x-c)²+w²)
intensity = np.zeros_like(chemical_shift)

# TMS reference peak at 0 ppm (singlet)
intensity += 0.30 * 0.008**2 / ((chemical_shift - 0.00) ** 2 + 0.008**2)

# CH3 triplet near 1.18 ppm (3 peaks, 1:2:1 pattern, J = 7 Hz)
tc, j = 1.18, 0.07
intensity += 0.50 * w**2 / ((chemical_shift - (tc - j)) ** 2 + w**2)
intensity += 1.00 * w**2 / ((chemical_shift - tc) ** 2 + w**2)
intensity += 0.50 * w**2 / ((chemical_shift - (tc + j)) ** 2 + w**2)

# CH2 quartet near 3.69 ppm (4 peaks, 1:3:3:1 pattern, J = 7 Hz)
qc = 3.69
intensity += 0.25 * w**2 / ((chemical_shift - (qc - 1.5 * j)) ** 2 + w**2)
intensity += 0.75 * w**2 / ((chemical_shift - (qc - 0.5 * j)) ** 2 + w**2)
intensity += 0.75 * w**2 / ((chemical_shift - (qc + 0.5 * j)) ** 2 + w**2)
intensity += 0.25 * w**2 / ((chemical_shift - (qc + 1.5 * j)) ** 2 + w**2)

# OH singlet near 2.61 ppm
intensity += 0.35 * 0.015**2 / ((chemical_shift - 2.61) ** 2 + 0.015**2)

# Add subtle baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

# Downsample for pygal performance (every 6th point)
cs_plot = chemical_shift[::6]
int_plot = intensity[::6]

# Negate x-values to reverse axis (NMR convention: high ppm on left)
cs_negated = -cs_plot

# Peak annotations with chemical shift values and functional group labels
peak_info = [(0.00, "TMS"), (1.18, "CH\u2083 triplet"), (2.61, "OH singlet"), (3.69, "CH\u2082 quartet")]

# Style — colorblind-safe teal/orange palette
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2c3e50",
    foreground_strong="#2c3e50",
    foreground_subtle="#e8e8e8",
    colors=("#306998", "#d35400", "#1a9988", "#8e44ad", "#2980b9"),
    guide_stroke_color="#e8e8e8",
    major_guide_stroke_color="#d5d5d5",
    guide_stroke_dasharray="2,2",
    major_guide_stroke_dasharray="",
    title_font_size=68,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=36,
    value_font_size=52,
    tooltip_font_size=34,
    stroke_width=3,
    opacity=1.0,
    opacity_hover=1.0,
)

# Chart — negated x so pygal renders high ppm on left; format labels as positive
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="Ethanol \u00b9H NMR \u00b7 spectrum-nmr \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Chemical Shift (ppm)",
    y_title="Intensity (a.u.)",
    show_dots=False,
    print_labels=True,
    print_values=False,
    show_x_guides=False,
    show_y_guides=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    xrange=(-12.5, 1.0),
    range=(-0.02, 1.25),
    margin=50,
    margin_top=80,
    margin_bottom=200,
    margin_left=100,
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    x_value_formatter=lambda x: f"{abs(x):.1f}",
    y_value_formatter=lambda y: f"{y:.3f}",
    x_labels_major_every=2,
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.axis > .line { stroke: transparent !important; }",
        "inline:.text-overlay .series .label { font-size: 40px !important; fill: #2c3e50 !important; font-weight: bold !important; }",
    ],
)

# Spectrum line (no per-point labels to keep print_labels clean)
spectrum_points = [(float(cs), float(inten)) for cs, inten in zip(cs_negated, int_plot, strict=False)]
chart.add("\u00b9H NMR Spectrum", spectrum_points, stroke_style={"width": 3}, fill=False)

# Peak markers — each as its own series so label appears in legend and on chart
for ppm, group_name in peak_info:
    # Find local maximum within ±0.15 ppm of the nominal center
    mask = np.abs(chemical_shift - ppm) < 0.15
    region_idx = np.where(mask)[0]
    idx = int(region_idx[np.argmax(intensity[region_idx])])
    peak_x = -float(chemical_shift[idx])
    peak_y = float(intensity[idx])
    label_text = f"{group_name} ({ppm:.2f} ppm)"
    point = {"value": (peak_x, peak_y), "label": label_text}
    chart.add(label_text, [point], stroke=False, show_dots=True, dots_size=18)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
