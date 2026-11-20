"""anyplot.ai
calibration-curve: Calibration Curve
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per model in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 10  # equal-width probability bins, as the spec asks

# Columns: set these to your table's column names
Y_TRUE = "Observed outcome"  # role: y_true
Y_PROB = ["Logistic Regression", "Overconfident Model"]  # role: y_prob

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.default_rng(42)
n_samples = 2000
true_prob = rng.beta(2, 2, n_samples)
outcome = (rng.random(n_samples) < true_prob).astype(int)
well_calibrated = np.clip(true_prob + rng.normal(0, 0.08, n_samples), 0.01, 0.99)
overconfident = 1 / (1 + np.exp(-12 * (true_prob - 0.5)))
overconfident = np.clip(overconfident + rng.normal(0, 0.02, n_samples), 0.02, 0.98)
df = pd.DataFrame({Y_TRUE: outcome, Y_PROB[0]: well_calibrated, Y_PROB[1]: overconfident})

# Plot: reads only df and the constants above
bin_edges = np.linspace(0, 1, N_BINS + 1)
y_true = df[Y_TRUE].to_numpy()

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    # reference line first in the neutral tone, then the models from the Imprint palette
    colors=(INK_MUTED, *IMPRINT_PALETTE),
    title_font_size=60,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=38,
    value_font_size=32,
    stroke_width=4,
)

chart = pygal.XY(
    style=custom_style,
    width=3200,
    height=1800,
    title="calibration-curve · python · pygal · anyplot.ai",
    x_title="Mean predicted probability",
    y_title="Fraction of positives",
    show_dots=True,
    dots_size=11,
    stroke_style={"width": 5},
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:.1f}",
    value_formatter=lambda y: f"{y:.1f}",
    range=(0, 1),
    xrange=(0, 1),
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=30,
    truncate_legend=-1,
    margin=40,
    margin_top=60,
)

# Diagonal reference: perfect calibration (predicted = observed)
chart.add("Perfect calibration", [(0, 0), (1, 1)], stroke_style={"width": 4, "dasharray": "18,10"}, show_dots=False)

# One calibration curve per model; each point is one bin's (mean prediction, fraction of positives)
for model in Y_PROB:
    y_prob = df[model].to_numpy()
    bin_index = np.digitize(y_prob, bin_edges[1:-1])
    points = []
    for b in range(N_BINS):
        in_bin = bin_index == b
        if in_bin.any():
            pred, obs = float(y_prob[in_bin].mean()), float(y_true[in_bin].mean())
            points.append(
                {"value": (pred, obs), "label": f"{pred:.2f} predicted → {obs:.2f} observed (n={in_bin.sum()})"}
            )
    brier = np.mean((y_prob - y_true) ** 2)
    chart.add(f"{model} (Brier {brier:.3f})", points)

# Save output files
output_dir = os.path.dirname(os.path.abspath(__file__))
chart.render_to_png(os.path.join(output_dir, f"plot-{THEME}.png"))
chart.render_to_file(os.path.join(output_dir, f"plot-{THEME}.html"))
