""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from sklearn.datasets import make_classification


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
Y_TRUE = "Actual outcome (0/1)"  # role: y_true
Y_SCORE = "Predicted probability"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
X, labels = make_classification(
    n_samples=1000, n_features=10, n_informative=5, n_redundant=2, n_classes=2, weights=[0.7, 0.3], random_state=42
)
scores = 1 / (1 + np.exp(-(X[:, 0] * 0.8 + X[:, 1] * 0.5 + np.random.randn(1000) * 0.3)))
df = pd.DataFrame({Y_TRUE: labels, Y_SCORE: scores})

# Plot: reads only df and the constants above
ranked = df.sort_values(Y_SCORE, ascending=False)[Y_TRUE].to_numpy()
n_total = len(ranked)
gains = np.cumsum(ranked) / ranked.sum() * 100
population_pct = np.arange(1, n_total + 1) / n_total * 100

# Every 2% of the population keeps the curve readable; the computed points are joined, not smoothed
step = max(n_total // 50, 1)
idx = np.unique(np.concatenate([np.arange(step - 1, n_total, step), [n_total - 1]]))
model_curve = [(0.0, 0.0)] + [(float(population_pct[i]), float(gains[i])) for i in idx]

# Perfect model: full capture at the positive class rate, flat from there
positive_rate = float(ranked.mean() * 100)
perfect_curve = [(0.0, 0.0), (positive_rate, 100.0), (100.0, 100.0)]
random_curve = [(0.0, 0.0), (100.0, 100.0)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(IMPRINT_PALETTE[0], IMPRINT_PALETTE[2], INK_MUTED),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=8,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    title="gain-curve · python · pygal · anyplot.ai",
    x_title="Population targeted (%)",
    y_title="Positive cases captured (%)",
    style=custom_style,
    show_dots=False,
    range=(0, 100),
    xrange=(0, 100),
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    truncate_legend=-1,
    margin=40,
)

chart.add("Model", model_curve, stroke_style={"width": 9, "linecap": "round", "linejoin": "round"})
chart.add("Perfect model", perfect_curve, stroke_style={"width": 6, "dasharray": "40, 20"})
chart.add("Random selection", random_curve, stroke_style={"width": 6, "dasharray": "6, 18", "linecap": "round"})

# Save
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
