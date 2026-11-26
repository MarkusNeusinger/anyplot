"""anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: letsplot 4.10.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_x_log10,
    scale_y_log10,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#E4E2DB" if THEME == "light" else "#2F2F2C"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: material properties drawn as reference lines, in MPa
ULTIMATE_STRENGTH = 500
YIELD_STRENGTH = 350
ENDURANCE_LIMIT = 200

# Columns: set these to your table's column names
CYCLES = "Number of Cycles to Failure (N)"  # role: cycles
STRESS = "Stress Amplitude (MPa)"  # role: stress

# Data: replace this block with your own table, for example df = pd.read_csv("fatigue_tests.csv")
# Synthetic fatigue tests on structural steel: 3-5 specimens per stress level,
# cycles follow the Basquin relation S = A * N^b with lognormal scatter.
np.random.seed(42)
stress_levels = np.array([450, 400, 350, 320, 300, 280, 260, 240, 220, 210])
basquin_a = 800
basquin_b = -0.10
base_cycles = (stress_levels / basquin_a) ** (1 / basquin_b)

all_stress = []
all_cycles = []
for stress, base_n in zip(stress_levels, base_cycles, strict=True):
    n_specimens = np.random.randint(3, 6)
    all_stress.extend([stress] * n_specimens)
    all_cycles.extend(base_n * np.random.lognormal(0, 0.15, n_specimens))

df = pd.DataFrame({CYCLES: all_cycles, STRESS: all_stress})

# Plot: reads only df and the constants above
# Basquin fit: straight line in log-log space, S = A * N^b
valid = df[[CYCLES, STRESS]].dropna().astype(float)
slope, intercept = np.polyfit(np.log10(valid[CYCLES]), np.log10(valid[STRESS]), 1)
fit_cycles = np.logspace(np.log10(df[CYCLES].min()) - 0.2, np.log10(df[CYCLES].max()) + 1.0, 100)
df_fit = pd.DataFrame({CYCLES: fit_cycles, STRESS: 10**intercept * fit_cycles**slope})

# Fatigue regime zones span the full width of the axis, bounded by the reference stresses
x_lo = 10 ** np.floor(np.log10(df[CYCLES].min()))
x_hi = 10 ** (np.ceil(np.log10(df[CYCLES].max())) + 1)
y_lo = df[STRESS].min() / 1.8
zone_bounds = [
    (YIELD_STRENGTH, ULTIMATE_STRENGTH, IMPRINT_PALETTE[1]),  # low-cycle (plastic)
    (ENDURANCE_LIMIT, YIELD_STRENGTH, IMPRINT_PALETTE[2]),  # high-cycle (elastic)
    (y_lo, ENDURANCE_LIMIT, IMPRINT_PALETTE[3]),  # infinite life
]

# Reference lines: (stress, label, color, linetype, label offset factor)
references = [
    (ULTIMATE_STRENGTH, "Ultimate Strength", IMPRINT_PALETTE[1], "dashed", 0.92),
    (YIELD_STRENGTH, "Yield Strength", IMPRINT_PALETTE[2], "dotted", 1.07),
    (ENDURANCE_LIMIT, "Endurance Limit", IMPRINT_PALETTE[3], "dotdash", 1.07),
]
label_x = df[CYCLES].max() * 2

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK),
)

plot = ggplot()

# Zone shading, drawn first so it sits behind the data
for y_min, y_max, color in zone_bounds:
    zone = pd.DataFrame({"xmin": [x_lo], "xmax": [x_hi], "ymin": [y_min], "ymax": [y_max]})
    plot += geom_rect(
        data=zone,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=color,
        alpha=0.10,
        color="transparent",
    )

plot += geom_line(data=df_fit, mapping=aes(x=CYCLES, y=STRESS), color=IMPRINT_PALETTE[0], size=1.5, alpha=0.9)
plot += geom_point(
    data=df,
    mapping=aes(x=CYCLES, y=STRESS),
    color=IMPRINT_PALETTE[0],
    size=3.5,
    alpha=0.85,
    tooltips=layer_tooltips()
    .line(f"Cycles to failure|@{{{CYCLES}}}{{,.0f}}")
    .line(f"Stress amplitude|@{{{STRESS}}} MPa"),
)

# Reference lines with inline labels at the right side, clear of the fit line
for stress_value, name, color, linetype, offset in references:
    plot += geom_hline(yintercept=stress_value, color=color, size=0.9, linetype=linetype)
    # The lowest line's label goes to the empty left side: the data runs down to it on the right
    at_left = stress_value == min(r[0] for r in references)
    label = pd.DataFrame({"x": [x_lo * 1.4 if at_left else label_x], "y": [stress_value * offset], "label": [name]})
    plot += geom_text(
        data=label, mapping=aes(x="x", y="y", label="label"), color=color, size=11, hjust=0 if at_left else 1
    )

plot = (
    plot
    + scale_x_log10()
    + scale_y_log10(limits=[y_lo, ULTIMATE_STRENGTH * 1.12], expand=[0, 0])
    + labs(title="sn-curve-basic · python · letsplot · anyplot.ai", x=CYCLES, y=STRESS)
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
