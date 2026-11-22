"""anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: pygal 3.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os
import sys
from importlib import import_module

import numpy as np
from sklearn.datasets import load_wine
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CULTIVAR = "Cultivar"  # role: labels
ALCOHOL = "Alcohol (%)"  # role: features
MALIC_ACID = "Malic acid (g/L)"  # role: extra
FLAVANOIDS = "Flavanoids"  # role: extra
COLOR = "Color intensity"  # role: extra
PROLINE = "Proline (mg/L)"  # role: extra
FEATURES = [ALCOHOL, MALIC_ACID, FLAVANOIDS, COLOR, PROLINE]

# Data: replace this block with your own table, for example df = pd.read_csv("wines.csv")
wine = load_wine(as_frame=True)
df = wine.frame.rename(
    columns=dict(zip(["alcohol", "malic_acid", "flavanoids", "color_intensity", "proline"], FEATURES, strict=True))
)
df[CULTIVAR] = df["target"].map(lambda t: f"Cultivar {t + 1}")
df = df[[CULTIVAR, *FEATURES]]

# Plot: reads only df and the constants above
df = df.dropna(subset=FEATURES).reset_index(drop=True)
groups = list(dict.fromkeys(df[CULTIVAR].astype(str)))
scaled = StandardScaler().fit_transform(df[FEATURES])
pca = PCA(n_components=2)
scores = pca.fit_transform(scaled)
loadings = pca.components_.T
variance_explained = pca.explained_variance_ratio_ * 100

# One common factor scales all arrows so they sit alongside the scores
score_extent = np.abs(scores).max()
loading_scale = score_extent * 0.85 / np.abs(loadings).max()

title = "biplot-pca · python · pygal · anyplot.ai"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=52,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    value_label_font_size=40,
    value_colors=(INK,) * 8,
    tooltip_font_size=36,
    stroke_width=4,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=f"PC1 ({variance_explained[0]:.1f}%)",
    y_title=f"PC2 ({variance_explained[1]:.1f}%)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    dots_size=9,
    stroke=False,
    show_x_guides=False,
    show_y_guides=True,
    truncate_legend=-1,
    explicit_size=True,
    print_values=False,
    print_labels=True,
)

# Observation scores, one series per cultivar
for group in groups:
    mask = (df[CULTIVAR].astype(str) == group).to_numpy()
    chart.add(group, [(float(x), float(y)) for x, y in scores[mask]], stroke=False, dots_size=9)

# Loading vectors: a line from the origin to the tip with a two-stroke head, named at the tip
for i, feature in enumerate(FEATURES):
    tip_x, tip_y = (float(v) for v in loadings[i] * loading_scale)
    length = np.hypot(tip_x, tip_y)
    ux, uy = tip_x / length, tip_y / length
    px, py = -uy, ux
    head_len = 0.07 * loading_scale * np.abs(loadings).max()
    head_wid = 0.035 * loading_scale * np.abs(loadings).max()
    bx, by = tip_x - ux * head_len, tip_y - uy * head_len
    arrow = [
        (0.0, 0.0),
        {"value": (tip_x, tip_y), "label": feature.split(" (")[0]},
        (float(bx + px * head_wid), float(by + py * head_wid)),
        (tip_x, tip_y),
        (float(bx - px * head_wid), float(by - py * head_wid)),
        (tip_x, tip_y),
    ]
    chart.add(
        feature,
        arrow,
        stroke=True,
        show_dots=True,
        dots_size=1,
        fill=False,
        stroke_style={"width": 5},
        print_labels=True,
        print_values=False,
    )

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
