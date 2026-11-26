""" anyplot.ai
pp-basic: Probability-Probability (P-P) Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-26
"""

import os
from math import erf, sqrt

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "#D8D7D0" if THEME == "light" else "#3A3A36"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
KS_FACTOR = 1.36  # 95% Kolmogorov-Smirnov critical value factor for the confidence envelope

# Columns: set these to your table's column names
OBSERVED = "Tablet weight (mg)"  # role: observed
DISTRIBUTION = "Reference distribution"  # role: theoretical_distribution

# Data: replace this block with your own table, for example df = pd.read_csv("weights.csv")
# Pharmaceutical tablet weights (target 500 mg, occasional overfills) checked against a normal reference
np.random.seed(42)
normal_fill = np.random.normal(500, 8, 160)
overfill_events = np.random.exponential(5, 40) + 498
df = pd.DataFrame({OBSERVED: np.concatenate([normal_fill, overfill_events]), DISTRIBUTION: "Normal"})

# Plot: reads only df and the constants above
EMPIRICAL = "Empirical CDF"
THEORETICAL = f"Theoretical CDF ({df[DISTRIBUTION].iloc[0]})"
pp = pd.DataFrame({OBSERVED: np.sort(df[OBSERVED].dropna().to_numpy())})
n = len(pp)

# Empirical CDF with plotting position i/(n+1)
pp[EMPIRICAL] = np.arange(1, n + 1) / (n + 1)

# Theoretical normal CDF with fitted mean and standard deviation
mu = pp[OBSERVED].mean()
sigma = pp[OBSERVED].std(ddof=0)
z = (pp[OBSERVED].to_numpy() - mu) / (sigma * sqrt(2))
pp[THEORETICAL] = 0.5 * (1 + np.vectorize(erf)(z))

# Pointwise 95% Kolmogorov envelope around the diagonal
ks_band = KS_FACTOR / sqrt(n)
band_x = np.linspace(0, 1, 100)
band = pd.DataFrame(
    {"x": band_x, "y_lower": np.maximum(band_x - ks_band, 0.0), "y_upper": np.minimum(band_x + ks_band, 1.0)}
)

# Reference line of perfect fit, corner to corner
ref = pd.DataFrame({"x": [0, 1], "y": [0, 1]})

plot = (
    ggplot()
    + geom_ribbon(
        aes(x="x", ymin="y_lower", ymax="y_upper"),
        data=band,
        fill=INK_MUTED,
        alpha=0.18,
        size=0,
        tooltips=layer_tooltips().line("95% Kolmogorov band"),
    )
    + geom_line(aes(x="x", y="y"), data=ref, color=INK, size=1.0, linetype="dashed", tooltips="none")
    + geom_point(
        aes(x=THEORETICAL, y=EMPIRICAL),
        data=pp,
        shape=21,
        size=3.5,
        fill=IMPRINT_PALETTE[0],
        color=INK_SOFT,
        stroke=0.6,
        alpha=0.75,
        tooltips=layer_tooltips().line(f"@|@{{{OBSERVED}}}").line(f"@{{{EMPIRICAL}}}"),
    )
    + scale_x_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + labs(
        x=THEORETICAL,
        y=EMPIRICAL,
        title="pp-basic · python · letsplot · anyplot.ai",
        subtitle=f"Tablet weights vs. fitted normal reference (n={n})",
    )
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.3),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_text(size=11, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
    )
)

# The fixed aspect leaves canvas strips transparent: a one-panel grid paints the whole square canvas
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
