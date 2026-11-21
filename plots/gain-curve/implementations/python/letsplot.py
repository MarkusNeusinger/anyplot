"""anyplot.ai
gain-curve: Cumulative Gains Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
OUTCOME = "Responded (0/1)"  # role: y_true
SCORE = "Model score"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("campaign.csv")
np.random.seed(42)
n_customers = 1000
affinity = np.random.beta(2, 5, n_customers)
df = pd.DataFrame(
    {
        OUTCOME: (np.random.random(n_customers) < affinity * 0.6 + 0.05).astype(int),
        SCORE: np.clip(affinity + np.random.normal(0, 0.1, n_customers), 0, 1),
    }
)

# Plot: reads only df and the constants above
ranked = df.sort_values(SCORE, ascending=False)[OUTCOME].to_numpy()
n_rows = len(ranked)
positive_rate = ranked.mean()
population = np.arange(n_rows + 1) / n_rows * 100
model_gain = np.concatenate([[0], np.cumsum(ranked) / ranked.sum() * 100])
perfect_gain = np.minimum(population / (positive_rate * 100), 1) * 100

CURVES = ["Model", "Perfect model", "Random selection"]
curves = pd.DataFrame(
    {
        "Population": np.tile(population, 3),
        "Gain": np.concatenate([model_gain, perfect_gain, population]),
        "Curve": np.repeat(CURVES, len(population)),
    }
)

plot = (
    ggplot(curves, aes(x="Population", y="Gain", color="Curve", linetype="Curve"))
    + geom_line(size=1.6)
    + scale_color_manual(values=[IMPRINT_PALETTE[0], IMPRINT_PALETTE[2], INK_SOFT], limits=CURVES)
    + scale_linetype_manual(values=["solid", "longdash", "dotted"], limits=CURVES)
    + scale_x_continuous(limits=[0, 100], expand=[0, 0])
    + scale_y_continuous(limits=[0, 100], expand=[0, 0])
    + labs(
        x="Population targeted (%)",
        y="Positive cases captured (%)",
        title="gain-curve · python · letsplot · anyplot.ai",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_blank(),
        legend_position=[0.8, 0.2],
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, os.path.join(os.getcwd(), f"plot-{THEME}.png"), scale=4)
ggsave(plot, os.path.join(os.getcwd(), f"plot-{THEME}.html"))
