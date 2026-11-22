"""anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_errorbar,
    geom_hline,
    ggplot,
    labs,
    scale_fill_gradient,
    scale_x_discrete,
    theme,
    theme_minimal,
)


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential gradient runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Mean decrease in AUC"  # role: importance_mean
IMPORTANCE_STD = "Std across shuffles"  # role: importance_std

# Data: replace this block with your own table, for example df = pd.read_csv("importance.csv")
# Simulated permutation importance of a 30-day hospital readmission model (10 repeats)
rng = np.random.default_rng(7)
features = [
    "Prior Admissions (12 mo)",
    "Length of Stay",
    "Discharge Disposition",
    "Charlson Comorbidity Index",
    "Number of Medications",
    "Emergency Admission",
    "Age",
    "Hemoglobin at Discharge",
    "Creatinine at Discharge",
    "Sodium at Discharge",
    "Insurance Type",
    "Marital Status",
    "Weekend Discharge",
    "Primary Language",
    "Admission Month",
]
base_importance = np.array(
    [0.062, 0.048, 0.037, 0.031, 0.024, 0.019, 0.014, 0.011, 0.008, 0.006, 0.004, 0.002, 0.001, 0.0005, -0.003]
)
df = pd.DataFrame(
    {
        FEATURE: features,
        IMPORTANCE: base_importance + rng.normal(0, 0.0008, len(features)),
        IMPORTANCE_STD: np.abs(rng.normal(0.004, 0.0015, len(features))),
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(IMPORTANCE, ascending=True).reset_index(drop=True)
df["low"] = df[IMPORTANCE] - df[IMPORTANCE_STD]
df["high"] = df[IMPORTANCE] + df[IMPORTANCE_STD]

plot = (
    ggplot(df, aes(x=FEATURE, y=IMPORTANCE, fill=IMPORTANCE))
    + geom_col(width=0.7)
    + geom_errorbar(aes(ymin="low", ymax="high"), width=0.3, color=INK_SOFT, size=0.5)
    + geom_hline(yintercept=0, linetype="dashed", color=INK, size=0.5)
    + scale_x_discrete(limits=df[FEATURE].tolist())
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2], name="Importance")
    + coord_flip()
    + labs(x=FEATURE, y=IMPORTANCE, title="bar-permutation-importance · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(alpha=0),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.12),
        panel_grid_minor=element_line(alpha=0),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
