""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data - credit scoring: loan default classification model
np.random.seed(42)
n_samples = 1000

# Generate synthetic model scores and true labels
base_score = np.random.randn(n_samples)

# Generate true labels (defaults) with ~15% default rate, correlated with score
prob_default = 1 / (1 + np.exp(-(base_score + np.random.randn(n_samples) * 0.5)))
y_true = (prob_default > 0.85).astype(int)

# Model predictions - risk scores correlated with true labels but with noise
y_score = base_score + np.where(y_true == 1, 1.2, -0.4) + np.random.randn(n_samples) * 0.7
y_score = 1 / (1 + np.exp(-y_score))

# Calculate cumulative gains curve
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

total_positives = np.sum(y_true)
cumulative_positives = np.cumsum(y_true_sorted)
gains = cumulative_positives / total_positives * 100

percentages = np.arange(1, n_samples + 1) / n_samples * 100

# Create DataFrame for plotting
df_model = pd.DataFrame({"percent_population": percentages, "percent_positives": gains, "curve": "Model"})

# Random baseline (diagonal)
df_random = pd.DataFrame({"percent_population": [0, 100], "percent_positives": [0, 100], "curve": "Random"})

# Perfect model: vertical rise to 100% at positive rate, then horizontal
positive_rate = (total_positives / n_samples) * 100
df_perfect = pd.DataFrame(
    {"percent_population": [0, positive_rate, 100], "percent_positives": [0, 100, 100], "curve": "Perfect"}
)

# Combine all curves
df = pd.concat([df_model, df_random, df_perfect], ignore_index=True)

# Plot
plot = (
    ggplot(df, aes(x="percent_population", y="percent_positives", color="curve"))
    + geom_line(size=2.5)
    + scale_color_manual(values={"Model": "#009E73", "Random": INK_MUTED, "Perfect": "#AE3030"})
    + scale_x_continuous(breaks=range(0, 101, 20), limits=(0, 100))
    + scale_y_continuous(breaks=range(0, 101, 20), limits=(0, 100))
    + labs(
        title="gain-curve · plotnine · anyplot.ai",
        x="Loan Portfolio Targeted (%)",
        y="Defaults Captured (%)",
        color="Curve",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(color=INK, size=24),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=16),
        legend_title=element_text(color=INK, size=16),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
