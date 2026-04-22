""" pyplots.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: pygal 3.1.0 | Python 3.13.11
Quality: 78/100 | Created: 2026-01-15
"""

import numpy as np
import pygal
from pygal.style import Style


# Data: Fatigue test results for steel specimens
np.random.seed(42)

# Stress levels (MPa) - from high to low
stress_levels = np.array([450, 400, 350, 300, 275, 250, 225, 210, 200, 195])

# Generate cycles to failure with realistic scatter (Basquin relationship: S = A * N^b)
base_cycles = np.array([1e2, 5e2, 2e3, 1e4, 3e4, 1e5, 4e5, 1e6, 5e6, 1e7])

# Add multiple test specimens per stress level (3-5 samples each) with scatter
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

# Fit Basquin equation: S = A * N^b (linear in log-log space)
log_cycles = np.log10(cycles_data)
log_stress = np.log10(stress_data)
coeffs = np.polyfit(log_cycles, log_stress, 1)
b = coeffs[0]  # slope (negative for S-N curve)
log_A = coeffs[1]  # intercept
A = 10**log_A

# Generate fitted curve points with more points for smooth line
fit_cycles = np.logspace(2, 7, 100)
fit_stress = A * (fit_cycles**b)

# Material reference values (MPa)
ultimate_strength = 520
yield_strength = 350
endurance_limit = 190

# Create XY data points for pygal
xy_points = [(float(c), float(s)) for c, s in zip(cycles_data, stress_data, strict=True)]

# Fitted curve points as list of tuples
fit_points = [(float(c), float(s)) for c, s in zip(fit_cycles, fit_stress, strict=True)]

# Custom style for 4800x2700 canvas with larger fonts
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FF6B35", "#E74C3C", "#27AE60", "#8E44AD"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    stroke_width=6,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create XY chart with logarithmic x-axis
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="sn-curve-basic · pygal · pyplots.ai",
    x_title="Cycles to Failure (N)",
    y_title="Stress Amplitude (MPa)",
    logarithmic=True,
    show_dots=True,
    dots_size=16,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    legend_at_bottom=True,
    legend_box_size=32,
    margin=80,
    truncate_legend=-1,
    range=(150, 550),
)

# Add series in logical order for legend: data → fit → references (high to low)

# 1. Test data points (primary data - most important)
chart.add("Test Data", xy_points, dots_size=20, stroke=False, show_dots=True)

# 2. Fitted Basquin curve (derived from data)
chart.add(
    "Basquin Fit (S-N Curve)",
    fit_points,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 8, "dasharray": "20, 10"},
)

# 3. Reference lines in descending order of stress value
# Ultimate Strength (highest)
ultimate_line = [(100, ultimate_strength), (1e7, ultimate_strength)]
chart.add(
    f"Ultimate Strength ({ultimate_strength} MPa)",
    ultimate_line,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4},
)

# Yield Strength (middle)
yield_line = [(100, yield_strength), (1e7, yield_strength)]
chart.add(f"Yield Strength ({yield_strength} MPa)", yield_line, stroke=True, show_dots=False, stroke_style={"width": 4})

# Endurance Limit (lowest)
endurance_line = [(100, endurance_limit), (1e7, endurance_limit)]
chart.add(
    f"Endurance Limit ({endurance_limit} MPa)", endurance_line, stroke=True, show_dots=False, stroke_style={"width": 4}
)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
