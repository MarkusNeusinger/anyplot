""" anyplot.ai
calibration-curve: Calibration Curve
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-20
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_line,
    element_rect,
    element_text,
    geom_abline,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_size_identity,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — a single model uses it alone

# Constants
N_BINS = 10  # equal-width probability bins, as the spec asks

# Columns: set these to your table's column names
Y_TRUE = "True label"  # role: y_true
Y_PROB = ["Predicted probability"]  # role: y_prob

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
np.random.seed(42)
n_samples = 2000
# A slightly overconfident classifier: true event rate sits below the predicted probability
prob = np.random.beta(2, 3, n_samples)
true_prob = np.clip(prob - 0.08 + np.random.normal(0, 0.05, n_samples), 0, 1)
df = pd.DataFrame({Y_TRUE: (np.random.random(n_samples) < true_prob).astype(int), Y_PROB[0]: prob})

# Plot: reads only df and the constants above
bin_index = np.clip(np.digitize(df[Y_PROB[0]], np.linspace(0, 1, N_BINS + 1)) - 1, 0, N_BINS - 1)
bins = (
    df.groupby(bin_index)
    .agg(mean_predicted=(Y_PROB[0], "mean"), fraction_positives=(Y_TRUE, "mean"), count=(Y_TRUE, "size"))
    .reset_index(drop=True)
)
bins["point_size"] = 2 + 3 * bins["count"] / bins["count"].max()

# Expected Calibration Error: count-weighted gap between observed and predicted
ece = (bins["count"] * (bins["fraction_positives"] - bins["mean_predicted"]).abs()).sum() / bins["count"].sum()

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.8),
    axis_title=element_text(size=11, color=INK),
    axis_text=element_text(size=9, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.8),
    plot_title=element_text(size=12, color=INK),
    plot_subtitle=element_text(size=10, color=INK_SOFT),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT),
    legend_title=element_text(color=INK),
)

plot = (
    ggplot(bins, aes(x="mean_predicted", y="fraction_positives"))
    + geom_abline(intercept=0, slope=1, linetype="dashed", color=INK_SOFT, size=0.8)
    + geom_line(color=BRAND, size=1.0)
    + geom_point(aes(size="point_size"), color=BRAND, fill=BRAND, stroke=0, alpha=0.85)
    + scale_size_identity()
    + labs(
        x="Mean predicted probability",
        y="Fraction of positives (observed)",
        title="calibration-curve · python · plotnine · anyplot.ai",
        subtitle=f"ECE = {ece:.3f} · point size shows samples per bin",
    )
    + coord_fixed(ratio=1, xlim=(0, 1), ylim=(0, 1))
    + theme_minimal()
    + anyplot_theme
    + theme(figure_size=(6, 6))
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
