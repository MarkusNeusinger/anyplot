"""anyplot.ai
lift-curve: Model Lift Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
Y_TRUE = "Responded (0/1)"  # role: y_true
Y_SCORE = "Model score"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# Simulated customer response campaign: a model score and the actual response flag
rng = np.random.default_rng(42)
n_samples = 2000
score = rng.beta(2, 5, n_samples)
responded = (rng.random(n_samples) < 0.1 + 0.6 * score).astype(int)
df = pd.DataFrame({Y_TRUE: responded, Y_SCORE: score})

# Plot: reads only df and the constants above
ranked = df.dropna().sort_values(Y_SCORE, ascending=False)
outcomes = ranked[Y_TRUE].to_numpy()
n_total = len(outcomes)
baseline_rate = outcomes.mean()
targeted = np.arange(1, n_total + 1)
lift = np.cumsum(outcomes) / targeted / baseline_rate
pct = targeted / n_total * 100

# One point per percent of the population; decile markers sit on the same curve
step_idx = np.unique(np.round(np.arange(1, 101) / 100 * n_total).astype(int)) - 1
curve = [(float(pct[i]), float(lift[i])) for i in step_idx]
decile_idx = np.unique(np.round(np.arange(10, 101, 10) / 100 * n_total).astype(int)) - 1
deciles = [{"value": (float(pct[i]), float(lift[i])), "label": f"{lift[i]:.2f}"} for i in decile_idx]
reference = [(0, 1.0), (100, 1.0)]

top = float(lift[step_idx].max()) * 1.1

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(IMPRINT_PALETTE[0], INK_SOFT, IMPRINT_PALETTE[0]),
    title_font_size=60,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=36,
    value_colors=(INK,),
    stroke_width=6,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="lift-curve · python · pygal · anyplot.ai",
    x_title="Population targeted (%)",
    y_title="Cumulative lift (× baseline)",
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    range=(0, top),
    xrange=(0, 100),
    margin=60,
    value_formatter=lambda v: f"{v:.2f}",
    x_value_formatter=lambda v: f"{v:.0f}%",
    print_values=False,
)

chart.add("Model lift", curve, stroke_style={"width": 5})
chart.add("Random selection (lift = 1)", reference, stroke_style={"width": 4, "dasharray": "24, 16"})
chart.add(
    "Decile values",
    deciles,
    stroke=False,
    show_dots=True,
    dots_size=11,
    print_values=True,
    print_labels=True,
    formatter=lambda v: f"{v[1]:.2f}",
    value_label_font_size=36,
)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
