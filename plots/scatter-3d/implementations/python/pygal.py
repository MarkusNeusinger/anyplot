""" anyplot.ai
scatter-3d: 3D Scatter Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 40/100 | Created: 2026-05-08
"""

import os
import site
import sys

import numpy as np


sys.path.insert(0, site.getsitepackages()[0])

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9")

np.random.seed(42)
n_samples = 150
n_clusters = 3

clusters_x = np.random.uniform(10, 90, n_clusters)
clusters_y = np.random.uniform(20, 80, n_clusters)
clusters_z = np.random.uniform(15, 85, n_clusters)

points_x = []
points_y = []
points_z = []

for i in range(n_clusters):
    cluster_points_x = np.random.normal(clusters_x[i], 8, n_samples // n_clusters)
    cluster_points_y = np.random.normal(clusters_y[i], 8, n_samples // n_clusters)
    cluster_points_z = np.random.normal(clusters_z[i], 8, n_samples // n_clusters)

    points_x.extend(cluster_points_x)
    points_y.extend(cluster_points_y)
    points_z.extend(cluster_points_z)

points_x = np.array(points_x)
points_y = np.array(points_y)
points_z = np.array(points_z)

z_norm = (points_z - points_z.min()) / (points_z.max() - points_z.min())

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    stroke_width=0,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-3d · pygal · anyplot.ai",
    x_title="X Dimension",
    y_title="Y Dimension",
    show_legend=True,
    show_dots=True,
    dots_size=7,
)

for i in range(n_clusters):
    start_idx = (i * n_samples) // n_clusters
    end_idx = ((i + 1) * n_samples) // n_clusters

    cluster_data = [
        (x, y)
        for x, y in zip(
            points_x[start_idx:end_idx], points_y[start_idx:end_idx], strict=True
        )
    ]
    chart.add(f"Cluster {i + 1}", cluster_data)

chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
