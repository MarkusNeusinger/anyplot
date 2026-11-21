"""anyplot.ai
facet-grid: Faceted Grid Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    facet_grid,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEED = 42
N_POINTS = 15

# Columns
HOURS = "Study Hours"  # role: x
SCORE = "Exam Score"  # role: y
SUBJECT = "Subject"  # role: row_facet
METHOD = "Method"  # role: col_facet

# Data - student exam scores across teaching methods and subjects
np.random.seed(SEED)
subject_effects = {"Math": 5, "Science": 3, "Reading": -2, "Writing": 0}
method_effects = {"In-Person": 3, "Online": -2, "Hybrid": 1}

rows = []
for subject, subject_effect in subject_effects.items():
    for method, method_effect in method_effects.items():
        hours = np.random.uniform(2, 10, N_POINTS)
        score = 60 + 6 * hours + subject_effect + method_effect + np.random.randn(N_POINTS) * 5
        rows.append(pd.DataFrame({HOURS: hours, SCORE: np.clip(score, 30, 100), SUBJECT: subject, METHOD: method}))
df = pd.concat(rows, ignore_index=True)
df[SUBJECT] = pd.Categorical(df[SUBJECT], categories=df[SUBJECT].unique(), ordered=True)
df[METHOD] = pd.Categorical(df[METHOD], categories=df[METHOD].unique(), ordered=True)

# Plot
plot = (
    ggplot(df, aes(x=HOURS, y=SCORE, color=METHOD))
    + geom_point(size=2.5, alpha=0.75)
    + facet_grid(rows=SUBJECT, cols=METHOD, labeller="label_both")
    + scale_color_manual(values=IMPRINT_PALETTE, limits=df[METHOD].unique().tolist())
    + scale_y_continuous(expand=(0.1, 0, 0.08, 0))
    + labs(title="facet-grid · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=12, color=INK, ha="center"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        strip_text_x=element_text(size=8, color=INK, face="bold"),
        strip_text_y=element_text(size=8, color=INK, face="bold", rotation=0),
        strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_spacing_x=0.02,
        panel_spacing_y=0.02,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
