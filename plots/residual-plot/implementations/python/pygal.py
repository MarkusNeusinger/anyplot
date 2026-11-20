"""anyplot.ai
residual-plot: Residual Plot
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SIGMA_LIMIT = 2  # residuals beyond this many standard deviations count as outliers

# Columns: set these to your table's column names
Y_PRED = "Predicted delivery time (min)"  # role: y_pred
Y_TRUE = "Observed delivery time (min)"  # role: y_true

# Data: replace this block with your own table, for example df = pd.read_csv("deliveries.csv")
# Delivery-time regression: the model misses more on long routes (heteroscedastic), plus three bad days
rng = np.random.default_rng(7)
n_orders = 140
predicted = np.sort(rng.uniform(12, 75, n_orders))
noise = rng.normal(0, 2.2, n_orders) + (predicted / 75) * rng.normal(0, 4.0, n_orders)
observed = predicted + noise
observed[[22, 71, 118]] += [19.0, -16.0, 21.0]
df = pd.DataFrame({Y_PRED: predicted, Y_TRUE: observed})

# Plot: reads only df and the constants above
residuals = df[Y_TRUE] - df[Y_PRED]
limit = SIGMA_LIMIT * residuals.std()
is_outlier = residuals.abs() > limit
x_min, x_max = df[Y_PRED].min(), df[Y_PRED].max()
x_pad = (x_max - x_min) * 0.03
y_top = max(residuals.abs().max(), limit) * 1.15
x_ticks = np.linspace(x_min, x_max, 8).round().astype(int).tolist()
span = [float(x_min), float(x_max)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(IMPRINT_PALETTE[0], IMPRINT_PALETTE[4], INK, INK_MUTED, INK_MUTED),
    opacity=0.55,
    opacity_hover=0.9,
    title_font_size=64,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=36,
    value_font_size=32,
    stroke_width=3,
    guide_stroke_color=INK_MUTED,
    guide_stroke_dasharray="3, 6",
    major_guide_stroke_color=INK_MUTED,
    major_guide_stroke_dasharray="3, 6",
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="residual-plot · python · pygal · anyplot.ai",
    x_title=Y_PRED,
    y_title="Residual: observed minus predicted (min)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    spacing=30,
    margin_bottom=40,
    show_x_guides=True,
    show_y_guides=True,
    stroke=False,
    dots_size=11,
    truncate_legend=-1,
    x_label_rotation=0,
    xrange=(float(x_min - x_pad), float(x_max + x_pad)),
    range=(-float(y_top), float(y_top)),
    x_labels=x_ticks,
)

points = list(zip(df[Y_PRED].astype(float), residuals.astype(float), strict=True))
chart.add("Residuals", [p for p, out in zip(points, is_outlier, strict=True) if not out])
chart.add(f"Outliers (>{SIGMA_LIMIT}σ)", [p for p, out in zip(points, is_outlier, strict=True) if out])
chart.add("Zero line", [(x, 0.0) for x in span], stroke=True, show_dots=False, stroke_style={"width": 5})
chart.add(
    f"+{SIGMA_LIMIT}σ",
    [(x, float(limit)) for x in span],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "14, 10"},
)
chart.add(
    f"−{SIGMA_LIMIT}σ",
    [(x, float(-limit)) for x in span],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "14, 10"},
)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
