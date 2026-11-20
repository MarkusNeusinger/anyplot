"""anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

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

# Columns: set these to your table's column names
K = "Number of Clusters (k)"  # role: k_values
INERTIA = "Inertia (Within-cluster Sum of Squares)"  # role: inertia

# Data: replace this block with your own table, for example df = pd.read_csv("kmeans_inertia.csv")
# Document clustering: inertia of K-means on a text corpus for k = 1..10
df = pd.DataFrame({K: list(range(1, 11)), INERTIA: [5200, 2600, 1600, 950, 700, 560, 480, 420, 380, 350]})

# Plot: reads only df and the constants above
# Elbow = the point farthest from the straight line joining the first and last points (both axes scaled 0-1)
k_scaled = (df[K] - df[K].min()) / (df[K].max() - df[K].min())
inertia_scaled = (df[INERTIA] - df[INERTIA].min()) / (df[INERTIA].max() - df[INERTIA].min())
elbow = df.loc[(1 - k_scaled - inertia_scaled).idxmax()]

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=44,
    stroke_width=6,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=style,
    title="elbow-curve · python · pygal · anyplot.ai",
    x_title=K,
    y_title=INERTIA,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=True,
    x_labels=df[K].tolist(),
    range=(0, df[INERTIA].max() * 1.05),
    explicit_size=True,
    margin=60,
)

chart.add("Inertia", list(zip(df[K], df[INERTIA], strict=True)), dots_size=14, show_dots=True)

# Highlight the optimal k at the curve's own point, labelled with its value
chart.add(
    "Optimal k",
    [{"value": (elbow[K], elbow[INERTIA]), "label": f"Elbow at k = {int(elbow[K])}"}],
    dots_size=26,
    stroke=False,
    show_dots=True,
)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
