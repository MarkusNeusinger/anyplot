"""anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
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

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: material properties of the steel (MPa), true for any test series
ULTIMATE_STRENGTH = 550
YIELD_STRENGTH = 350
ENDURANCE_LIMIT = 250

# Marker per test result: circle for failures, triangle for runouts, spare shapes for more groups
MARKERS = ["o", "^", "s", "D", "v", "P", "X", "*"]

# Column names, written as the axis and legend titles should read
CYCLES = "Number of Cycles to Failure (N)"  # role: cycles
STRESS = "Stress Amplitude (MPa)"  # role: stress
RESULT = "Test Result"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("fatigue.csv")
np.random.seed(42)
basquin_a = 1200
basquin_b = -0.12
sigma_log_n = 0.3  # log-normal scatter in cycles

stress_levels = np.array([500, 450, 400, 375, 350, 325, 300, 280, 270, 260, 255])
cycles_list = []
stress_list = []
result_list = []
for s in stress_levels:
    n_expected = (s / basquin_a) ** (1 / basquin_b)
    n_tests = np.random.randint(3, 6)
    cycles_list.extend(n_expected * np.random.lognormal(0, sigma_log_n, n_tests))
    stress_list.extend([s] * n_tests)
    result_list.extend(["failure"] * n_tests)

# Runout specimens: tested to the limit without failing
cycles_list.extend([1e7, 2e7, 5e7])
stress_list.extend([ENDURANCE_LIMIT - 10, ENDURANCE_LIMIT - 5, ENDURANCE_LIMIT + 5])
result_list.extend(["runout"] * 3)

df = pd.DataFrame({CYCLES: cycles_list, STRESS: stress_list, RESULT: result_list})

# Plot
# Basquin fit S = A * N^b: a straight line in log-log space through the failures
failures = df[df[RESULT] == df[RESULT].iloc[0]].dropna(subset=[CYCLES, STRESS])  # first result group = the failures
slope, intercept = np.polyfit(np.log10(failures[CYCLES]), np.log10(failures[STRESS]), 1)
fit_cycles = np.logspace(np.log10(failures[CYCLES].min()), np.log10(failures[CYCLES].max()), 100)
df_fit = pd.DataFrame({CYCLES: fit_cycles, STRESS: 10**intercept * fit_cycles**slope})

log_mid = 10 ** np.log10(df[CYCLES]).mean()

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_blank(),
    axis_line_x=element_line(color=INK_SOFT, size=0.8),
    axis_line_y=element_line(color=INK_SOFT, size=0.8),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    plot_title=element_text(color=INK, size=12, weight="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color="none"),
    legend_key=element_rect(fill=ELEVATED_BG, color="none"),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
    plot_margin=0.05,
)

plot = (
    ggplot()
    # Basquin fit line
    + geom_line(df_fit, aes(x=CYCLES, y=STRESS), color=IMPRINT_PALETTE[0], size=1.2, alpha=0.85)
    # Data points: shape separates runout (triangle) from failure (circle)
    + geom_point(df, aes(x=CYCLES, y=STRESS, shape=RESULT), color=IMPRINT_PALETTE[0], size=4.2, alpha=0.80)
    # Reference lines; the endurance limit is slightly thicker as the focal point
    + geom_hline(yintercept=ULTIMATE_STRENGTH, linetype="dashed", color=IMPRINT_PALETTE[1], size=0.9, alpha=0.85)
    + geom_hline(yintercept=YIELD_STRENGTH, linetype="dashed", color=IMPRINT_PALETTE[2], size=0.9, alpha=0.85)
    + geom_hline(yintercept=ENDURANCE_LIMIT, linetype="dashed", color=IMPRINT_PALETTE[3], size=1.2, alpha=0.90)
    + annotate(
        "text",
        x=df[CYCLES].min(),
        y=ULTIMATE_STRENGTH * 1.05,
        label=f"Ultimate Strength ({ULTIMATE_STRENGTH} MPa)",
        size=10,
        color=IMPRINT_PALETTE[1],
        ha="left",
    )
    + annotate(
        "text",
        x=log_mid * 3,
        y=YIELD_STRENGTH * 1.05,
        label=f"Yield Strength ({YIELD_STRENGTH} MPa)",
        size=10,
        color=IMPRINT_PALETTE[2],
        ha="left",
    )
    + annotate(
        "text",
        x=df[CYCLES].min(),
        y=ENDURANCE_LIMIT * 0.93,
        label=f"Endurance Limit ({ENDURANCE_LIMIT} MPa)",
        size=10,
        color=IMPRINT_PALETTE[3],
        ha="left",
    )
    # Logarithmic scales
    + scale_x_log10()
    + scale_y_log10()
    # Shape scale distinguishes runout (triangle) from failure (circle)
    + scale_shape_manual(
        values=[MARKERS[i % len(MARKERS)] for i in range(df[RESULT].nunique())],
        limits=df[RESULT].unique().tolist(),
        name=RESULT,
    )
    # Labels
    + labs(title="sn-curve-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
