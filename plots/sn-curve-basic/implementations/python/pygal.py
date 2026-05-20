"""anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-20
"""

import os
import sys

import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Remove current dir from sys.path to avoid shadowing the pygal package
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)

# Data: Fatigue test results for steel specimens
np.random.seed(42)

stress_levels = np.array([450, 400, 350, 300, 275, 250, 225, 210, 200, 195])
base_cycles = np.array([1e2, 5e2, 2e3, 1e4, 3e4, 1e5, 4e5, 1e6, 5e6, 1e7])

cycles_data = []
stress_data = []

for stress, base_n in zip(stress_levels, base_cycles, strict=True):
    n_samples = np.random.randint(3, 6)
    scatter = np.exp(np.random.normal(0, 0.3, n_samples))
    cycles = base_n * scatter
    cycles_data.extend(cycles)
    stress_data.extend([stress] * n_samples)

cycles_data = np.array(cycles_data)
stress_data = np.array(stress_data)

# Basquin equation fit: S = A * N^b (linear in log-log space)
log_cycles = np.log10(cycles_data)
log_stress = np.log10(stress_data)
coeffs = np.polyfit(log_cycles, log_stress, 1)
b = coeffs[0]
A = 10 ** coeffs[1]

fit_cycles = np.logspace(2, 7, 100)
fit_stress = A * (fit_cycles**b)

# Material reference values (MPa)
ultimate_strength = 520
yield_strength = 350
endurance_limit = 190

xy_points = [
    {"value": (float(c), float(s)), "label": f"{float(c):.2e} cycles @ {float(s):.0f} MPa"}
    for c, s in zip(cycles_data, stress_data, strict=True)
]
fit_points = [
    {"value": (float(c), float(s)), "label": f"Fit: {float(c):.2e} → {float(s):.0f} MPa"}
    for c, s in zip(fit_cycles, fit_stress, strict=True)
]

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
    opacity=0.9,
    opacity_hover=1.0,
)

# Plot
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="sn-curve-basic · python · pygal · anyplot.ai",
    x_title="Cycles to Failure (N)",
    y_title="Stress Amplitude (MPa)",
    logarithmic=True,
    show_dots=True,
    dots_size=12,
    stroke=True,
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=90,
    legend_at_bottom=True,
    legend_box_size=32,
    margin=80,
    range=(150, 550),
    value_formatter=lambda xy: f"{xy[0]:.2e} cycles, {xy[1]:.0f} MPa" if isinstance(xy, tuple) else str(xy),
)

# Show only major log decades on x-axis to reduce tick clutter
chart.x_labels = [100, 1000, 10000, 100000, 1000000, 10000000]

# Series: Test Data first (primary), then derived/reference
chart.add("Test Data", xy_points, dots_size=16, stroke=False, show_dots=True)
chart.add(
    "Basquin Fit (S-N Curve)",
    fit_points,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 6, "dasharray": "20, 10"},
)
chart.add(
    f"Ultimate Strength ({ultimate_strength} MPa)",
    [(100, ultimate_strength), (1e7, ultimate_strength)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 6, "opacity": 0.65},
)
chart.add(
    f"Yield Strength ({yield_strength} MPa)",
    [(100, yield_strength), (1e7, yield_strength)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 6, "opacity": 0.65},
)
chart.add(
    f"Endurance Limit ({endurance_limit} MPa)",
    [(100, endurance_limit), (1e7, endurance_limit)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 6, "opacity": 0.65},
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
