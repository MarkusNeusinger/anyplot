""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-09
"""

import numpy as np
import pygal
from pygal.style import Style


# Data: Synthetic 1H NMR spectrum of ethanol (CH3-CH2-OH)
np.random.seed(42)
chemical_shift = np.linspace(0, 12, 6000)


# Lorentzian peak function for realistic NMR line shapes
def _peak(x, center, height, width):
    return height * width**2 / ((x - center) ** 2 + width**2)


# Build spectrum with realistic splitting patterns
intensity = np.zeros_like(chemical_shift)

# TMS reference peak at 0 ppm (singlet)
intensity += _peak(chemical_shift, 0.00, 0.30, 0.008)

# CH3 triplet near 1.18 ppm (3 peaks, 1:2:1 pattern)
triplet_center = 1.18
j_coupling = 0.07
intensity += _peak(chemical_shift, triplet_center - j_coupling, 0.50, 0.010)
intensity += _peak(chemical_shift, triplet_center, 1.00, 0.010)
intensity += _peak(chemical_shift, triplet_center + j_coupling, 0.50, 0.010)

# CH2 quartet near 3.69 ppm (4 peaks, 1:3:3:1 pattern)
quartet_center = 3.69
intensity += _peak(chemical_shift, quartet_center - 1.5 * j_coupling, 0.25, 0.010)
intensity += _peak(chemical_shift, quartet_center - 0.5 * j_coupling, 0.75, 0.010)
intensity += _peak(chemical_shift, quartet_center + 0.5 * j_coupling, 0.75, 0.010)
intensity += _peak(chemical_shift, quartet_center + 1.5 * j_coupling, 0.25, 0.010)

# OH singlet near 2.61 ppm
intensity += _peak(chemical_shift, 2.61, 0.35, 0.015)

# Add subtle baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

# Downsample for pygal performance (every 6th point)
step = 6
cs_plot = chemical_shift[::step]
int_plot = intensity[::step]

# Negate x-values to reverse axis (NMR convention: high ppm on left)
cs_negated = -cs_plot
int_plot_arr = int_plot

# Peak annotations for key signals
peak_labels = {
    0.00: "TMS (0.00 ppm)",
    1.18: "CH₃ triplet (1.18 ppm)",
    2.61: "OH singlet (2.61 ppm)",
    3.69: "CH₂ quartet (3.69 ppm)",
}

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2c3e50",
    foreground_strong="#2c3e50",
    foreground_subtle="#e8e8e8",
    colors=("#306998", "#c0392b"),
    guide_stroke_color="#e8e8e8",
    major_guide_stroke_color="#d5d5d5",
    guide_stroke_dasharray="2,2",
    major_guide_stroke_dasharray="",
    title_font_size=68,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=34,
    tooltip_font_size=34,
    stroke_width=3,
    opacity=1.0,
    opacity_hover=1.0,
)

# Chart — use negated x so pygal renders high ppm on left; format labels as positive
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="Ethanol ¹H NMR · spectrum-nmr · pygal · pyplots.ai",
    x_title="Chemical Shift (ppm)",
    y_title="Intensity (a.u.)",
    show_dots=False,
    show_x_guides=False,
    show_y_guides=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    xrange=(-12.5, 0.5),
    range=(-0.02, 1.15),
    margin=50,
    margin_top=80,
    margin_bottom=200,
    margin_left=100,
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    x_value_formatter=lambda x: f"{abs(x):.1f}",
    y_value_formatter=lambda y: f"{y:.3f}",
    css=["file://style.css", "file://graph.css", "inline:.axis > .line { stroke: transparent !important; }"],
)

# Spectrum line
spectrum_points = [
    {"value": (float(cs), float(inten)), "label": f"δ = {abs(cs):.2f} ppm"}
    for cs, inten in zip(cs_negated, int_plot_arr, strict=False)
]
chart.add("¹H NMR Spectrum", spectrum_points, stroke_style={"width": 3}, fill=False)

# Peak markers for key signals
marker_points = []
for ppm, label in peak_labels.items():
    idx = np.argmin(np.abs(chemical_shift - ppm))
    marker_points.append({"value": (-float(chemical_shift[idx]), float(intensity[idx])), "label": label})

chart.add("Peak Assignments", marker_points, stroke=False, show_dots=True, dots_size=16)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
