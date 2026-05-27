# ruff: noqa: F405
"""anyplot.ai
lift-curve: Model Lift Chart
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-12-27
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1
REFERENCE = "#AE3030"  # Okabe-Ito position 5 for reference line

# Data: Fraud detection model
# Using exponential distribution for scores to reflect realistic fraud detection patterns
np.random.seed(42)
n_samples = 1200

# Fraud cases (10% base rate) with skewed distribution
n_fraud = int(n_samples * 0.10)
fraud_scores = np.random.exponential(scale=0.3, size=n_fraud)
fraud_scores = np.clip(fraud_scores, 0, 1)  # Normalize to [0, 1]

# Legitimate cases with lower exponential scores
legit_scores = np.random.exponential(scale=0.15, size=n_samples - n_fraud)
legit_scores = np.clip(legit_scores, 0, 1)

y_true = np.concatenate([np.ones(n_fraud), np.zeros(n_samples - n_fraud)])
y_score = np.concatenate([fraud_scores, legit_scores])

# Shuffle data
shuffle_idx = np.random.permutation(n_samples)
y_true = y_true[shuffle_idx]
y_score = y_score[shuffle_idx]

# Calculate lift curve
sorted_idx = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_idx]

n_fraud_total = np.sum(y_true)
baseline_rate = n_fraud_total / n_samples
cumsum_fraud = np.cumsum(y_true_sorted)
n_evaluated = np.arange(1, n_samples + 1)
population_pct = n_evaluated / n_samples * 100
response_rate = cumsum_fraud / n_evaluated
lift = response_rate / baseline_rate

# Sample points for smooth curve
sample_idx = np.arange(0, n_samples, max(1, n_samples // 100))
df = pd.DataFrame({"population_pct": population_pct[sample_idx], "lift": lift[sample_idx]})

# Reference line
ref_df = pd.DataFrame({"population_pct": [0, 100], "lift": [1, 1]})

# Create plot with theme-adaptive styling
plot = (
    ggplot()
    + geom_line(aes(x="population_pct", y="lift"), data=ref_df, color=INK_SOFT, size=1.5, linetype="dashed", alpha=0.6)
    + geom_line(aes(x="population_pct", y="lift"), data=df, color=BRAND, size=2.5)
    + geom_point(aes(x="population_pct", y="lift"), data=df[::5], color=BRAND, size=4, alpha=0.8)
    + labs(x="Population Targeted (%)", y="Cumulative Lift", title="lift-curve · letsplot · anyplot.ai")
    + scale_x_continuous(breaks=list(range(0, 101, 10)), limits=[0, 100])
    + scale_y_continuous(breaks=[1, 2, 3, 4, 5, 6, 7])
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG),
        legend_text=element_text(color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Add reference line label
plot = plot + geom_text(
    aes(x="x", y="y", label="label"),
    data=pd.DataFrame({"x": [85], "y": [1.15], "label": ["Baseline (Lift = 1)"]}),
    size=14,
    color=INK_SOFT,
)

# Save with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
