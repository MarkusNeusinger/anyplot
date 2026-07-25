"""anyplot.ai
stem-basic: Basic Stem Plot
Library: letsplot 4.9.0 | Python 3.13.13
"""
# ruff: noqa: F405

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — first series is always #009E73
BRAND = "#009E73"

# Data - discrete samples of a damped oscillation (impulse response)
np.random.seed(42)
n = 30
x = np.arange(n)
envelope = np.exp(-x / 10)
y = envelope * np.cos(x * 0.8) + np.random.randn(n) * 0.05

df = pd.DataFrame({"x": x, "y": y, "y_base": 0.0})
envelope_df = pd.DataFrame({"x": x, "upper": envelope, "lower": -envelope})

plot = (
    ggplot(df)
    + geom_line(aes(x="x", y="upper"), data=envelope_df, color=MUTED, size=1.0, linetype="dashed", alpha=0.7)
    + geom_line(aes(x="x", y="lower"), data=envelope_df, color=MUTED, size=1.0, linetype="dashed", alpha=0.7)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.5)
    + geom_segment(aes(x="x", y="y_base", xend="x", yend="y"), color=BRAND, size=1.2)
    + geom_point(
        aes(x="x", y="y"),
        color=BRAND,
        fill=BRAND,
        size=3.5,
        stroke=1.2,
        shape=21,
        tooltips=layer_tooltips().title("Sample @x").line("Amplitude|@y"),
    )
    + labs(x="Sample Index", y="Amplitude (a.u.)", title="stem-basic · letsplot · anyplot.ai")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_ticks=element_line(color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=16, color=INK),
    )
    + ggsize(800, 450)
)

# Save PNG (scale 4x for 3200 x 1800 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)

# Save HTML
ggsave(plot, f"plot-{THEME}.html", path=".")
