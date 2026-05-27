""" anyplot.ai
facet-grid: Faceted Grid Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-13
"""

import os
import sys


# Handle import conflicts: remove the script directory from sys.path to prevent
# shadowing of installed modules (matplotlib, plotnine, etc.)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_original_path = sys.path.copy()
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

# Also remove any __pycache__ or .pyc files that might exist
_mod_cache = {k: v for k, v in sys.modules.items() if k not in ("matplotlib", "plotnine")}

try:
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
        theme,
        theme_minimal,
    )
finally:
    pass

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Student exam scores across teaching methods and subjects
np.random.seed(42)

methods = ["In-Person", "Online", "Hybrid"]
subjects = ["Math", "Science", "Reading", "Writing"]

data = []
for subject in subjects:
    for method in methods:
        subject_effect = {"Math": 5, "Science": 3, "Reading": -2, "Writing": 0}[subject]
        method_effect = {"In-Person": 3, "Online": -2, "Hybrid": 1}[method]

        n_points = 15
        hours = np.random.uniform(2, 10, n_points)

        base_score = 60 + 6 * hours + subject_effect + method_effect
        score = base_score + np.random.randn(n_points) * 5
        score = np.clip(score, 30, 100)

        for i in range(n_points):
            data.append({"hours": hours[i], "score": score[i], "subject": subject, "method": method})

df = pd.DataFrame(data)

df["subject"] = pd.Categorical(df["subject"], categories=subjects, ordered=True)
df["method"] = pd.Categorical(df["method"], categories=methods, ordered=True)

plot = (
    ggplot(df, aes(x="hours", y="score", color="method"))
    + geom_point(size=4, alpha=0.75)
    + facet_grid("subject ~ method", labeller="label_both")
    + scale_color_manual(values=IMPRINT[:3])
    + labs(title="facet-grid · plotnine · anyplot.ai", x="Study Hours", y="Exam Score", color="Method")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=24, color=INK, ha="center"),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        strip_text_x=element_text(size=14, color=INK, face="bold"),
        strip_text_y=element_text(size=14, color=INK, face="bold", rotation=0),
        strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        legend_text=element_text(size=14, color=INK_SOFT),
        legend_position="right",
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_spacing_x=0.06,
        panel_spacing_y=0.06,
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
