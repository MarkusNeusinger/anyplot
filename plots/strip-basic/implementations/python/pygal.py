""" anyplot.ai
strip-basic: Basic Strip Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-04
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data — employee satisfaction scores by department (1–10 scale)
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Support"]
n_per_category = 40

scores = {
    "Engineering": np.clip(np.random.normal(7.5, 1.2, n_per_category), 1, 10),
    "Marketing": np.clip(np.random.normal(6.8, 1.5, n_per_category), 1, 10),
    "Sales": np.clip(np.random.normal(7.2, 1.0, n_per_category), 1, 10),
    "Support": np.clip(np.random.normal(6.5, 1.8, n_per_category), 1, 10),
}

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    opacity=0.65,
    stroke_width=0,
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="strip-basic · pygal · anyplot.ai",
    x_title="Department",
    y_title="Satisfaction Score (1–10)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    show_x_guides=False,
    show_y_guides=True,
    stroke=False,
    dots_size=12,
    x_label_rotation=0,
)

# X-axis labels aligned to integer positions
chart.x_labels = ["", "Engineering", "Marketing", "Sales", "Support", ""]
chart.xrange = (0, 5)

# Add jittered points per category
for i, cat in enumerate(categories, start=1):
    jitter = np.random.uniform(-0.25, 0.25, n_per_category)
    points = [(float(i + j), float(v)) for j, v in zip(jitter, scores[cat], strict=True)]
    chart.add(cat, points)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
