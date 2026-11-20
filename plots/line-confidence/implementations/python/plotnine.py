"""anyplot.ai
line-confidence: Line Plot with Confidence Interval
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-20
"""

import os
import pathlib
import sys

import numpy as np
import pandas as pd


sys.path = [p for p in sys.path if pathlib.Path(p).resolve() != pathlib.Path.cwd().resolve()]

from plotnine import (  # noqa: E402
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: a single series uses position 1
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
Z_95 = 1.96  # normal quantile of a two-sided 95% interval

# Columns: set these to your table's column names
SUBSTRATE = "Substrate concentration (mM)"  # role: x
RATE = "Reaction rate (µmol/min)"  # role: y
LOWER = "Lower 95% bound (µmol/min)"  # role: y_lower
UPPER = "Upper 95% bound (µmol/min)"  # role: y_upper
SERIES = "Series"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("kinetics.csv")
# Enzyme kinetics: Michaelis-Menten curve (Vmax 120, Km 2.5) with noise that grows with the rate
np.random.seed(42)
substrate = np.linspace(0.2, 10, 40)
expected = 120 * substrate / (2.5 + substrate)
std_error = 2.0 + 0.06 * expected
rate = expected + np.random.normal(0, std_error / 3)
df = pd.DataFrame(
    {SUBSTRATE: substrate, RATE: rate, LOWER: rate - Z_95 * std_error, UPPER: rate + Z_95 * std_error, SERIES: "fit"}
)

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=SUBSTRATE))
    + geom_ribbon(aes(ymin=LOWER, ymax=UPPER, fill=SERIES), alpha=0.25)
    + geom_line(aes(y=RATE, color=SERIES), size=1.2)
    + scale_fill_manual(values={"fit": IMPRINT_PALETTE[0]}, labels={"fit": "95% confidence interval"})
    + scale_color_manual(values={"fit": IMPRINT_PALETTE[0]}, labels={"fit": "Measured reaction rate"})
    + labs(x=SUBSTRATE, y=RATE, title="line-confidence · python · plotnine · anyplot.ai", fill="", color="")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=12),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_blank(),
        legend_position=(0.97, 0.05),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
