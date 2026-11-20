"""anyplot.ai
lift-curve: Model Lift Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is the brand color
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RANDOM_LIFT = 1.0  # lift of random selection: the reference line
MARKER_STEP = 10  # decile markers every 10 % of the population

# Columns: set these to your table's column names
Y_TRUE = "Responded (0/1)"  # role: y_true
Y_SCORE = "Model score"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
n_samples = 1000
model_score = rng.beta(2, 5, n_samples)  # model predictions
response_prob = 0.05 + 0.6 * model_score  # higher score = higher response chance
df = pd.DataFrame(
    {
        Y_TRUE: (rng.random(n_samples) < response_prob).astype(int),
        Y_SCORE: np.clip(model_score + rng.normal(0, 0.05, n_samples), 0, 1),
    }
)

# Plot: reads only df and the constants above
ranked = df.dropna(subset=[Y_TRUE, Y_SCORE]).sort_values(Y_SCORE, ascending=False)
hits = ranked[Y_TRUE].to_numpy()
n_total = len(hits)
baseline_rate = hits.mean()

pct = np.arange(1, 101)
n_targeted = np.ceil(n_total * pct / 100).astype(int)
lift = hits.cumsum()[n_targeted - 1] / n_targeted / baseline_rate
curve = pd.DataFrame({"pct": pct, "lift": lift})
markers = curve[curve["pct"] % MARKER_STEP == 0]

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=None),
    panel_border=element_blank(),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=12, color=INK),
)

plot = (
    ggplot()
    + geom_hline(yintercept=RANDOM_LIFT, linetype="dashed", color=INK_SOFT, size=0.6)
    + geom_line(data=curve, mapping=aes(x="pct", y="lift"), color=IMPRINT_PALETTE[0], size=1.2)
    + geom_point(data=markers, mapping=aes(x="pct", y="lift"), color=IMPRINT_PALETTE[0], size=2.5)
    + scale_x_continuous(breaks=range(0, 101, MARKER_STEP), limits=(0, 100))
    + scale_y_continuous(limits=(0, max(curve["lift"].max(), RANDOM_LIFT) * 1.05))
    + labs(title="lift-curve · python · plotnine · anyplot.ai", x="Population targeted (%)", y="Cumulative lift")
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
