""" anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: pygal 3.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import math
import os
import sys
from importlib import import_module

from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Ensure we import the installed pygal package, not the local script
site_packages = [p for p in sys.path if "site-packages" in p or "dist-packages" in p]
if site_packages:
    sys.path = site_packages + [p for p in sys.path if "site-packages" not in p and "dist-packages" not in p]

pygal = import_module("pygal")
Style = import_module("pygal.style").Style

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette: first series always #009E73 (brand), then position 2 and 3
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Load and prepare data
iris = load_iris()
X = iris.data
y = iris.target
target_names = iris.target_names

# Standardize features
X_scaled = StandardScaler().fit_transform(X)

# Perform PCA
pca = PCA(n_components=2)
scores = pca.fit_transform(X_scaled)
loadings = pca.components_.T
variance_explained = pca.explained_variance_ratio_ * 100

# Use correlation biplot scaling
score_range = max(scores[:, 0].max() - scores[:, 0].min(), scores[:, 1].max() - scores[:, 1].min())
loading_scale = score_range * 0.4

# Custom style for theme-adaptive rendering
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=2,
)

# Create XY chart for biplot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="biplot-pca · pygal · anyplot.ai",
    x_title=f"PC1 ({variance_explained[0]:.1f}%)",
    y_title=f"PC2 ({variance_explained[1]:.1f}%)",
    show_legend=True,
    legend_at_bottom=True,
    dots_size=10,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    truncate_legend=0,
    explicit_size=True,
)

# Add score points for each species (class)
for i, name in enumerate(target_names):
    mask = y == i
    points = [(float(scores[j, 0]), float(scores[j, 1])) for j in range(len(y)) if mask[j]]
    chart.add(name.capitalize(), points, stroke=False, dots_size=10)

# Full feature names for legend clarity
full_names = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]

# Add each loading vector as a thin line arrow
for i, full_name in enumerate(full_names):
    tip_x = float(loadings[i, 0] * loading_scale)
    tip_y = float(loadings[i, 1] * loading_scale)

    dx, dy = tip_x, tip_y
    length = math.sqrt(dx * dx + dy * dy)
    ux = dx / length if length > 0 else 0
    uy = dy / length if length > 0 else 0
    px, py = -uy, ux  # Perpendicular vector

    head_len = 0.06 * loading_scale
    head_wid = 0.03 * loading_scale
    hb_x = tip_x - ux * head_len
    hb_y = tip_y - uy * head_len

    arrow_line = [
        (0.0, 0.0),
        (tip_x, tip_y),
        (hb_x + px * head_wid, hb_y + py * head_wid),
        (tip_x, tip_y),
        (hb_x - px * head_wid, hb_y - py * head_wid),
        (tip_x, tip_y),
    ]
    chart.add(full_name, arrow_line, stroke=True, show_dots=False, fill=False, stroke_style={"width": 2})

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
