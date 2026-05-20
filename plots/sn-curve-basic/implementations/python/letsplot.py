""" anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: letsplot 4.10.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#E4E2DB" if THEME == "light" else "#2F2F2C"

# Okabe-Ito palette — positions 1-4
BRAND = "#009E73"  # position 1 — data points and fit line
OI_2 = "#D55E00"  # vermillion — Ultimate Strength
OI_3 = "#0072B2"  # blue — Yield Strength
OI_4 = "#CC79A7"  # reddish purple — Endurance Limit

# Generate realistic S-N curve data for structural steel
np.random.seed(42)

ultimate_strength = 500
yield_strength = 350
endurance_limit = 200

stress_levels = np.array([450, 400, 350, 320, 300, 280, 260, 240, 220, 210])

# Basquin equation: S = A * N^b  →  N = (S/A)^(1/b)
A = 800
b = -0.10
base_cycles = (stress_levels / A) ** (1 / b)

all_stress = []
all_cycles = []
for stress, base_N in zip(stress_levels, base_cycles, strict=True):
    n_specimens = np.random.randint(3, 6)
    scatter = np.random.lognormal(0, 0.15, n_specimens)
    cycles = base_N * scatter
    all_stress.extend([stress] * n_specimens)
    all_cycles.extend(cycles)

df = pd.DataFrame({"stress": all_stress, "cycles": all_cycles})

# Fit line starting at ~300 cycles to avoid crowding near Ultimate Strength at low N
fit_cycles = np.logspace(2.5, 7, 100)
fit_stress = A * fit_cycles**b
df_fit = pd.DataFrame({"cycles": fit_cycles, "stress": fit_stress})

# Fatigue regime zones: infinite life / high-cycle / low-cycle
df_zone_infinite = pd.DataFrame({"xmin": [100.0], "xmax": [1e8], "ymin": [100.0], "ymax": [float(endurance_limit)]})
df_zone_highcycle = pd.DataFrame(
    {"xmin": [100.0], "xmax": [1e8], "ymin": [float(endurance_limit)], "ymax": [float(yield_strength)]}
)
df_zone_lowcycle = pd.DataFrame(
    {"xmin": [100.0], "xmax": [1e8], "ymin": [float(yield_strength)], "ymax": [float(ultimate_strength)]}
)

anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major=element_line(color=GRID, size=0.3),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    axis_title=element_text(color=INK, size=12),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    plot_title=element_text(color=INK, size=16),  # noqa: F405
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
    legend_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    legend_title=element_text(color=INK),  # noqa: F405
)

plot = (
    ggplot()  # noqa: F405
    # Zone shading — demarcates fatigue regimes (rendered first, behind data)
    + geom_rect(  # noqa: F405
        data=df_zone_lowcycle,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),  # noqa: F405
        fill=OI_2,
        alpha=0.07,
        color="transparent",
    )
    + geom_rect(  # noqa: F405
        data=df_zone_highcycle,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),  # noqa: F405
        fill=OI_3,
        alpha=0.07,
        color="transparent",
    )
    + geom_rect(  # noqa: F405
        data=df_zone_infinite,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),  # noqa: F405
        fill=OI_4,
        alpha=0.07,
        color="transparent",
    )
    # Basquin power-law fit line — thicker (size=1.5) to stand apart from scatter points
    + geom_line(  # noqa: F405
        data=df_fit,
        mapping=aes(x="cycles", y="stress"),  # noqa: F405
        color=BRAND,
        size=1.5,
        alpha=0.9,
    )
    # Test specimen data points with interactive tooltips
    + geom_point(  # noqa: F405
        data=df,
        mapping=aes(x="cycles", y="stress"),  # noqa: F405
        color=BRAND,
        size=3.5,
        alpha=0.85,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Cycles to failure|@cycles{,.0f}")
        .line("Stress amplitude|@stress MPa"),
    )
    # Reference lines — distinct linetypes for CVD accessibility
    + geom_hline(yintercept=ultimate_strength, color=OI_2, size=0.9, linetype="dashed")  # noqa: F405
    + geom_hline(yintercept=yield_strength, color=OI_3, size=0.9, linetype="dotted")  # noqa: F405
    + geom_hline(yintercept=endurance_limit, color=OI_4, size=0.9, linetype="dotdash")  # noqa: F405
    # Inline labels at right side of chart (x=2e6, hjust=1) — well clear of the fit line
    + geom_text(  # noqa: F405
        data=pd.DataFrame({"cycles": [2e6], "stress": [ultimate_strength * 0.97], "label": ["Ultimate Strength"]}),
        mapping=aes(x="cycles", y="stress", label="label"),  # noqa: F405
        color=OI_2,
        size=11,
        hjust=1,
    )
    + geom_text(  # noqa: F405
        data=pd.DataFrame({"cycles": [2e6], "stress": [yield_strength * 1.04], "label": ["Yield Strength"]}),
        mapping=aes(x="cycles", y="stress", label="label"),  # noqa: F405
        color=OI_3,
        size=11,
        hjust=1,
    )
    + geom_text(  # noqa: F405
        data=pd.DataFrame({"cycles": [2e6], "stress": [endurance_limit * 1.04], "label": ["Endurance Limit"]}),
        mapping=aes(x="cycles", y="stress", label="label"),  # noqa: F405
        color=OI_4,
        size=11,
        hjust=1,
    )
    + scale_x_log10()  # noqa: F405
    + scale_y_log10()  # noqa: F405
    + labs(  # noqa: F405
        title="sn-curve-basic · python · letsplot · anyplot.ai",
        x="Number of Cycles to Failure (N)",
        y="Stress Amplitude (MPa)",
    )
    + theme_minimal()  # noqa: F405
    + anyplot_theme
    + ggsize(800, 450)  # noqa: F405
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
