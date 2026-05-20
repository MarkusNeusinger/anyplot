""" anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_shape_manual,
    scale_x_log10,
    scale_y_log10,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - S-N curve for steel specimen fatigue testing
np.random.seed(42)

# Material properties (MPa)
ultimate_strength = 550
yield_strength = 350
endurance_limit = 250

# Generate realistic S-N curve data with scatter
# Using Basquin equation: S = A * N^b
A = 1200  # Fatigue strength coefficient
b = -0.12  # Fatigue strength exponent

stress_levels = np.array([500, 450, 400, 375, 350, 325, 300, 280, 270, 260, 255])

cycles = []
stress = []
point_type = []

for s in stress_levels:
    n_expected = (s / A) ** (1 / b)
    n_tests = np.random.randint(3, 6)
    scatter = np.random.lognormal(0, 0.3, n_tests)
    n_values = n_expected * scatter
    cycles.extend(n_values)
    stress.extend([s] * n_tests)
    point_type.extend(["failure"] * n_tests)

# Runout data points (did not fail) — marked with distinct marker shape
runout_cycles = [1e7, 2e7, 5e7]
runout_stress = [endurance_limit - 10, endurance_limit - 5, endurance_limit + 5]
cycles.extend(runout_cycles)
stress.extend(runout_stress)
point_type.extend(["runout"] * 3)

df = pd.DataFrame({"cycles": cycles, "stress": stress, "type": point_type})

# Create Basquin fit line
fit_cycles = np.logspace(2, 7, 100)
fit_stress = A * fit_cycles**b
df_fit = pd.DataFrame({"cycles": fit_cycles, "stress": fit_stress})

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
)

plot = (
    ggplot()
    # Basquin fit line
    + geom_line(df_fit, aes(x="cycles", y="stress"), color=OKABE_ITO[0], size=1.2, alpha=0.85)
    # Data points — shape mapped to type for runout vs failure distinction
    + geom_point(df, aes(x="cycles", y="stress", shape="type"), color=OKABE_ITO[0], size=2.5, alpha=0.75)
    # Reference lines with Okabe-Ito colors
    + geom_hline(yintercept=ultimate_strength, linetype="dashed", color=OKABE_ITO[1], size=0.9, alpha=0.85)
    + geom_hline(yintercept=yield_strength, linetype="dashed", color=OKABE_ITO[2], size=0.9, alpha=0.85)
    + geom_hline(yintercept=endurance_limit, linetype="dashed", color=OKABE_ITO[3], size=0.9, alpha=0.85)
    # Reference line labels with matching colors
    + annotate(
        "text",
        x=1.2e2,
        y=ultimate_strength + 18,
        label="Ultimate Strength (550 MPa)",
        size=8,
        color=OKABE_ITO[1],
        ha="left",
    )
    + annotate(
        "text", x=1.2e2, y=yield_strength + 18, label="Yield Strength (350 MPa)", size=8, color=OKABE_ITO[2], ha="left"
    )
    + annotate(
        "text",
        x=1.2e2,
        y=endurance_limit - 22,
        label="Endurance Limit (250 MPa)",
        size=8,
        color=OKABE_ITO[3],
        ha="left",
    )
    # Logarithmic scales
    + scale_x_log10()
    + scale_y_log10()
    # Shape scale distinguishes runout (triangle) from failure (circle)
    + scale_shape_manual(values={"failure": "o", "runout": "^"}, name="Test Result")
    # Labels
    + labs(
        x="Number of Cycles to Failure (N)",
        y="Stress Amplitude (MPa)",
        title="sn-curve-basic · python · plotnine · anyplot.ai",
    )
    + theme_minimal()
    + theme(figure_size=(8, 4.5))
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
