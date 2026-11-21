"""anyplot.ai
gain-curve: Cumulative Gains Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEED = 42
N_SAMPLES = 1000
GRID_STEP = 20

# Columns
Y_TRUE = "y_true"  # role: y_true
Y_SCORE = "y_score"  # role: y_score

# Data - credit scoring: loan default classification model
rng = np.random.default_rng(SEED)
base_score = rng.standard_normal(N_SAMPLES)
prob_default = 1 / (1 + np.exp(-(base_score + rng.standard_normal(N_SAMPLES) * 0.5)))
defaulted = (prob_default > 0.85).astype(int)
raw_score = base_score + np.where(defaulted == 1, 1.2, -0.4) + rng.standard_normal(N_SAMPLES) * 1.6
df = pd.DataFrame({Y_TRUE: defaulted, Y_SCORE: 1 / (1 + np.exp(-raw_score))})

# Plot
POPULATION = "Loan Portfolio Targeted (%)"
CAPTURED = "Defaults Captured (%)"
CURVE = "Curve"

# Cumulative gains: rank by score descending, accumulate captured positives
ranked = df.sort_values(Y_SCORE, ascending=False)[Y_TRUE].to_numpy()
n_rows = len(df)
total_positives = ranked.sum()
positive_rate = total_positives / n_rows * 100
curves = pd.concat(
    [
        pd.DataFrame(
            {
                POPULATION: np.arange(n_rows + 1) / n_rows * 100,
                CAPTURED: np.concatenate([[0.0], np.cumsum(ranked) / total_positives * 100]),
                CURVE: "Model",
            }
        ),
        pd.DataFrame({POPULATION: [0, 100], CAPTURED: [0, 100], CURVE: "Random"}),
        pd.DataFrame({POPULATION: [0, positive_rate, 100], CAPTURED: [0, 100, 100], CURVE: "Perfect"}),
    ],
    ignore_index=True,
)

groups = curves[CURVE].unique().tolist()
palette = [IMPRINT_PALETTE[0], INK_MUTED, IMPRINT_PALETTE[4]]
x_max = curves[POPULATION].max()
y_max = curves[CAPTURED].max()

plot = (
    ggplot(curves, aes(x=POPULATION, y=CAPTURED, color=CURVE))
    + geom_line(size=1.2)
    + scale_color_manual(values=palette, limits=groups)
    + scale_x_continuous(breaks=np.arange(0, x_max + 1, GRID_STEP), limits=(0, x_max))
    + scale_y_continuous(breaks=np.arange(0, y_max + 1, GRID_STEP), limits=(0, y_max))
    + labs(title="gain-curve · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(color=INK, size=12),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=9),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
