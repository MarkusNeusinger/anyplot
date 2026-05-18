""" anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_jitter,
    geom_violin,
    ggplot,
    guides,
    labs,
    position_dodge,
    scale_color_manual,
    scale_fill_manual,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00"]

# Data - Response times (ms) across task types and expertise levels
np.random.seed(42)

categories = ["Simple", "Moderate", "Complex"]
groups = ["Novice", "Expert"]
n_per_combination = 40

data = []
for category in categories:
    for group in groups:
        base = {"Simple": 400, "Moderate": 700, "Complex": 1100}[category]
        if group == "Expert":
            base -= 150
        spread = {"Simple": 60, "Moderate": 100, "Complex": 150}[category]
        values = np.random.normal(base, spread, n_per_combination)
        values = np.clip(values, base - 3 * spread, base + 3 * spread)
        for v in values:
            data.append({"task_type": category, "expertise": group, "response_time": v})

df = pd.DataFrame(data)
df["task_type"] = pd.Categorical(df["task_type"], categories=categories, ordered=True)
df["expertise"] = pd.Categorical(df["expertise"], categories=groups, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="task_type", y="response_time", fill="expertise"))
    + geom_violin(position=position_dodge(width=0.8), alpha=0.5, size=0.8)
    + geom_jitter(aes(color="expertise"), position=position_dodge(width=0.8), size=2.5, alpha=0.8)
    + scale_fill_manual(values=OKABE_ITO, name="Expertise")
    + scale_color_manual(values=OKABE_ITO, name="Expertise")
    + guides(color="none")
    + labs(title="violin-grouped-swarm · Python · plotnine · anyplot.ai", x="Task Type", y="Response Time (ms)")
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        text=element_text(size=14),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
