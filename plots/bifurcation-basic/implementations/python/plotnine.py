""" anyplot.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-17
"""

import os
import sys


# Prevent this file (plotnine.py) from shadowing the installed plotnine package
sys.path = [p for p in sys.path if p and not p.endswith("implementations") and not p.endswith("/python")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bin2d,
    geom_vline,
    ggplot,
    guides,
    labs,
    scale_fill_gradient,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme-adaptive chrome (Imprint tokens)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette anchors used here
BRAND = "#009E73"  # brand green — low end of the sequential density ramp
BLUE = "#4467A3"  # imprint_seq high end
ANYPLOT_AMBER = "#DDCC77"  # warning / caution — flags the chaotic regime

# Data — logistic map: x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 4000)
n_discard = 300
n_keep = 150

parameter = np.empty(r_values.size * n_keep)
state = np.empty(r_values.size * n_keep)

x0 = 0.5
idx = 0
for r in r_values:
    x = x0
    for _ in range(n_discard):
        x = r * x * (1.0 - x)
    for _ in range(n_keep):
        x = r * x * (1.0 - x)
        parameter[idx] = r
        state[idx] = x
        idx += 1

df = pd.DataFrame({"parameter": parameter, "state": state})

# Key period-doubling bifurcation points of the logistic map
bifurcation_r = [3.0, 3.449, 3.544]

# Plot — geom_bin2d (2D density histogram) is the distinctive plotnine read on
# this spec. A log-scaled imprint_seq fill keeps the sparse chaotic bins visible
# instead of washing them out against the dense fixed-point/period branches.
plot = (
    ggplot(df, aes(x="parameter", y="state"))
    + geom_bin2d(bins=(440, 280), na_rm=True)
    + scale_fill_gradient(low=BRAND, high=BLUE, trans="log10")
    + geom_vline(xintercept=bifurcation_r, linetype="dashed", color=INK_SOFT, alpha=0.7, size=0.4)
    + annotate("text", x=2.98, y=0.95, label="Period-2\nr ≈ 3.0", size=3.4, color=INK, ha="right", fontweight="bold")
    + annotate("text", x=3.435, y=0.95, label="Period-4\nr ≈ 3.449", size=3.4, color=INK, ha="right", fontweight="bold")
    + annotate("text", x=3.56, y=0.06, label="Period-8\nr ≈ 3.544", size=3.4, color=INK, ha="left", fontweight="bold")
    + annotate(
        "label",
        x=2.62,
        y=0.74,
        label="Stable\nFixed Point",
        size=3.4,
        color=BRAND,
        fontweight="bold",
        fill=ELEVATED_BG,
        label_size=0,
    )
    + annotate(
        "label", x=3.86, y=0.12, label="Chaos", size=3.6, color=INK, fontweight="bold", fill=ANYPLOT_AMBER, label_size=0
    )
    + labs(
        x="Growth Rate (r)", y="Steady-State Population (x)", title="bifurcation-basic · python · plotnine · anyplot.ai"
    )
    + scale_x_continuous(breaks=np.arange(2.5, 4.1, 0.25), expand=(0, 0))
    + scale_y_continuous(breaks=np.arange(0, 1.1, 0.2), expand=(0, 0))
    + coord_cartesian(xlim=(2.5, 4.0), ylim=(0, 1.0))
    + guides(fill=False)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        panel_grid_major=element_line(color=INK_MUTED, size=0.25, alpha=0.18),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        legend_position="none",
    )
)

# Save (3200 x 1800 px)
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
