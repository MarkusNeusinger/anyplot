"""anyplot.ai
calibration-curve: Calibration Curve
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 10  # the spec's default: equal-width bins of 0.1
HIST_HEIGHT = 0.25  # tallest histogram bar as a share of the axis, so it stays secondary
HIST_BINS = 20  # finer bins for the distribution of predictions

# Columns: set these to your table's column names
Y_TRUE = "Actual outcome"  # role: y_true
Y_PROB = ["Predicted probability"]  # role: y_prob

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
np.random.seed(42)
n_negative, n_positive = 600, 400
y_true = np.concatenate([np.zeros(n_negative), np.ones(n_positive)])
# Overconfident model: negatives score low, positives score high, both with noise
y_prob = np.concatenate(
    [
        np.clip(np.random.beta(2, 5, n_negative) * 0.6 + np.random.normal(0, 0.05, n_negative), 0, 1),
        np.clip(np.random.beta(5, 2, n_positive) * 0.6 + 0.35 + np.random.normal(0, 0.08, n_positive), 0, 1),
    ]
)
order = np.random.permutation(n_negative + n_positive)
df = pd.DataFrame({Y_TRUE: y_true[order], Y_PROB[0]: y_prob[order]})

# Plot: reads only df and the constants above
prob = df[Y_PROB[0]].to_numpy()
outcome = df[Y_TRUE].to_numpy()

# Bin the predictions; the last bin includes its right edge, empty bins get no point
bin_index = np.minimum((prob * N_BINS).astype(int), N_BINS - 1)
curve = (
    pd.DataFrame({"bin": bin_index, "predicted": prob, "observed": outcome})
    .groupby("bin")
    .agg(predicted=("predicted", "mean"), observed=("observed", "mean"), size=("observed", "size"))
    .reset_index(drop=True)
)
tooltips = (
    layer_tooltips()
    .line("Predicted|@predicted")
    .line("Observed|@observed")
    .line("Bin size|@size")
    .format("@{predicted}", ".3f")
    .format("@{observed}", ".3f")
)

brier_score = np.mean((prob - outcome) ** 2)
ece = np.sum(curve["size"] / curve["size"].sum() * (curve["observed"] - curve["predicted"]).abs())

diagonal = pd.DataFrame({"x": [0, 1], "y": [0, 1]})

counts, edges = np.histogram(prob, bins=HIST_BINS, range=(0, 1))
histogram = pd.DataFrame({"center": (edges[:-1] + edges[1:]) / 2, "share": counts / counts.max() * HIST_HEIGHT})

plot = (
    ggplot()
    + geom_line(aes(x="x", y="y"), data=diagonal, color=INK_SOFT, size=0.8, linetype="dashed")
    + geom_bar(
        aes(x="center", y="share"), data=histogram, stat="identity", fill=INK_MUTED, color=PAGE_BG, alpha=0.4, width=0.9
    )
    + geom_line(aes(x="predicted", y="observed"), data=curve, color=IMPRINT_PALETTE[0], size=1.2)
    + geom_point(aes(x="predicted", y="observed"), data=curve, color=IMPRINT_PALETTE[0], size=3.5, tooltips=tooltips)
    + labs(
        x="Mean predicted probability",
        y="Fraction of positives",
        title="calibration-curve · python · letsplot · anyplot.ai",
        subtitle=f"Brier score {brier_score:.3f} · ECE {ece:.3f} · grey bars: share of predictions per bin",
    )
    + scale_x_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.4),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=16, color=INK),
        plot_subtitle=element_text(size=12, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save outputs
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
