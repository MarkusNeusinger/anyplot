""" anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

import importlib
import os
import sys


# Work around naming conflict: ensure we import the real pygal package, not this file
if __name__ == "__main__":
    import pathlib

    _this_file = pathlib.Path(__file__)
    _parent = _this_file.parent
    # Remove parent from path to avoid importing this file as pygal
    if str(_parent) in sys.path:
        sys.path.remove(str(_parent))

pygal = importlib.import_module("pygal")
Style = pygal.style.Style

THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"
ACCENT = "#C475FD"

# Document clustering: optimal k determined by elbow curve
# Represents topic grouping analysis on a text corpus
k_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
inertias = [5200, 2600, 1600, 950, 700, 560, 480, 420, 380, 350]

# Identify elbow point: where the rate of improvement sharply drops
# Calculate rates of change to find the point where slope flattens
rates_of_change = [inertias[i] - inertias[i + 1] for i in range(len(inertias) - 1)]
# The elbow is where the rate of change itself drops significantly
# k=4 (index 3) shows diminishing returns: 650 → 250 drop
elbow_k_index = 3  # k=4
elbow_k = k_values[elbow_k_index]
elbow_inertia = inertias[elbow_k_index]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND, ACCENT),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="elbow-curve · pygal · anyplot.ai",
    x_title="Number of Clusters (k)",
    y_title="Inertia (Within-cluster Sum of Squares)",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=True,
    dots_size=10,
    stroke_style={"width": 3, "linecap": "round", "linejoin": "round"},
    x_labels=k_values,
    range=(0, max(inertias) * 1.05),
    explicit_size=True,
    margin=80,
)

# Main curve: all data points as continuous line
elbow_data = [(k, inertia) for k, inertia in zip(k_values, inertias, strict=True)]
chart.add("Inertia", elbow_data, stroke_style={"width": 3}, dots_size=8, show_dots=True)

# Highlight elbow point with distinct marker (larger, accent color)
# Create a single-point series for the elbow to emphasize it visually
elbow_highlight = [None] * len(k_values)
elbow_highlight[elbow_k_index] = (elbow_k, elbow_inertia)
elbow_highlight_data = [(k, inertia) for i, (k, inertia) in enumerate(elbow_data) if i == elbow_k_index]
chart.add("Optimal k", elbow_highlight_data, dots_size=16, show_dots=True, stroke=False, fill=False)

# Save as PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
