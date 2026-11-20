"""anyplot.ai
lift-curve: Model Lift Chart
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-12-27
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BASELINE_LIFT = 1.0  # random selection captures responders at the base rate
DECILE_STEP = 10  # markers every 10 % of the population

# Columns: set these to your table's column names
Y_TRUE = "Actual fraud (0/1)"  # role: y_true
Y_SCORE = "Model fraud score"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
n_samples = 1200
n_fraud = int(n_samples * 0.10)
fraud_scores = np.clip(np.random.exponential(scale=0.3, size=n_fraud), 0, 1)
legit_scores = np.clip(np.random.exponential(scale=0.15, size=n_samples - n_fraud), 0, 1)
y_true = np.concatenate([np.ones(n_fraud), np.zeros(n_samples - n_fraud)])
y_score = np.concatenate([fraud_scores, legit_scores])
shuffle_idx = np.random.permutation(n_samples)
df = pd.DataFrame({Y_TRUE: y_true[shuffle_idx].astype(int), Y_SCORE: y_score[shuffle_idx]})

# Plot: reads only df and the constants above
ranked = df.sort_values(Y_SCORE, ascending=False)
n_rows = len(ranked)
n_targeted = np.arange(1, n_rows + 1)
cum_responders = ranked[Y_TRUE].to_numpy().cumsum()
base_rate = df[Y_TRUE].mean()

POP = "Population targeted (%)"
LIFT = "Cumulative lift"
curve = pd.DataFrame({POP: n_targeted / n_rows * 100, LIFT: cum_responders / n_targeted / base_rate})
step_rows = np.round(np.arange(DECILE_STEP, 100 + DECILE_STEP, DECILE_STEP) / 100 * n_rows).astype(int) - 1
deciles = curve.iloc[step_rows]

top = curve[LIFT].max()
reference = pd.DataFrame({POP: [0, 100], LIFT: [BASELINE_LIFT, BASELINE_LIFT]})
ref_label = pd.DataFrame({POP: [98], LIFT: [BASELINE_LIFT + top * 0.05], "label": ["Random selection (lift = 1)"]})

title = "lift-curve · python · letsplot · anyplot.ai"

plot = (
    ggplot(curve, aes(x=POP, y=LIFT))
    + geom_line(aes(x=POP, y=LIFT), data=reference, color=INK_SOFT, size=1.0, linetype="dashed")
    + geom_line(color=IMPRINT_PALETTE[0], size=1.4)
    + geom_point(data=deciles, color=IMPRINT_PALETTE[0], fill=PAGE_BG, shape=21, size=4, stroke=1.5)
    + geom_text(aes(x=POP, y=LIFT, label="label"), data=ref_label, size=4, color=INK_SOFT, hjust="right")
    + scale_x_continuous(breaks=list(range(0, 101, 10)), limits=[0, 100], expand=[0.01, 0])
    + scale_y_continuous(limits=[0, top * 1.08], expand=[0, 0])
    + labs(title=title)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=16, color=INK),
    )
    + ggsize(800, 450)
)

# Save with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
