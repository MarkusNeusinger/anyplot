"""anyplot.ai
silhouette-basic: Silhouette Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-10
"""

import os
import sys


# Prevent importing the local pygal.py file instead of the installed package
sys.path = [p for p in sys.path if not p.endswith("/implementations/python")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.metrics import silhouette_samples  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GAP_BARS = 4  # empty rows that separate two cluster blocks

# Columns: set these to your table's column names
FEATURE_1 = "Feature 1"  # role: samples
FEATURE_2 = "Feature 2"  # role: extra
CLUSTER = "Cluster"  # role: cluster_labels
SILHOUETTE = "Silhouette coefficient"  # role: silhouette_values

# Data: replace this block with your own table, for example df = pd.read_csv("clustered.csv")
np.random.seed(42)
X = np.vstack(
    [
        np.random.randn(50, 2) * 0.6 + np.array([0, 0]),
        np.random.randn(50, 2) * 0.7 + np.array([4, 4]),
        np.random.randn(50, 2) * 1.0 + np.array([0.8, 0.3]),
    ]
)
labels = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(X)
df = pd.DataFrame({FEATURE_1: X[:, 0], FEATURE_2: X[:, 1], CLUSTER: labels, SILHOUETTE: silhouette_samples(X, labels)})

# Plot: reads only df and the constants above
clusters = sorted(df[CLUSTER].dropna().unique())
avg_silhouette = df[SILHOUETTE].mean()

# One row per sample, sorted within its cluster, with empty rows between blocks
rows = []
for k in clusters:
    if rows:
        rows.extend([(None, None)] * GAP_BARS)
    scores = np.sort(df.loc[df[CLUSTER] == k, SILHOUETTE].to_numpy())[::-1]
    rows.extend((k, s) for s in scores)

low = min(0.0, df[SILHOUETTE].min())
axis_min = np.floor(low * 10) / 10 - 0.1 if low < 0 else 0.0
axis_max = min(1.0, np.ceil(df[SILHOUETTE].max() * 10) / 10 + 0.1)
ticks = [round(t, 1) for t in np.arange(axis_min, axis_max + 0.01, 0.2)]
avg_label = round(avg_silhouette, 3)
n_rows = len(rows)
bar_width = max(2, int(1300 / n_rows * 0.75))

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE[: len(clusters)]) + (INK,),
    title_font_size=64,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=40,
    stroke_width=3,
    opacity=1,
    opacity_hover=1,
)

# Each sample is a horizontal stroke from zero to its score, so one XY chart can
# also carry the vertical average line
bar_css = "".join(f".serie-{k} .line {{ stroke-width: {bar_width}px !important; }}" for k in range(len(clusters)))
bar_css += f".serie-{len(clusters)} .line {{ stroke-width: 6px !important; }}"
bar_css += f".text-overlay text {{ font-size: 38px !important; fill: {INK} !important; }}"

chart = pygal.XY(
    width=3200,
    height=1800,
    style=style,
    title="silhouette-basic · python · pygal · anyplot.ai",
    x_title=SILHOUETTE,
    y_title="Samples, grouped by cluster",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(clusters) + 1,
    show_y_guides=False,
    show_x_guides=True,
    print_labels=True,
    dots_size=0,
    allow_interruptions=True,
    range=(-1, n_rows),
    xrange=(axis_min, axis_max),
    margin=60,
    margin_bottom=40,
    show_y_labels=False,
    x_labels=ticks,
    truncate_label=-1,
    truncate_legend=-1,
    css=[
        "file://style.css",
        "file://graph.css",
        # CSS outranks the stroke-width attribute, so bar and line widths are set per series here
        f"inline:{bar_css}",
    ],
)

for k in clusters:
    members = [i for i, (c, _) in enumerate(rows) if c == k]
    middle = members[len(members) // 2]
    cluster_avg = df.loc[df[CLUSTER] == k, SILHOUETTE].mean()
    points = []
    for i in members:
        y = n_rows - 1 - i
        score = rows[i][1]
        label = f"avg {cluster_avg:.2f}" if i == middle else None
        points.append((0, y))
        points.append({"value": (score, y), "label": label} if label else (score, y))
        points.append((None, None))
    chart.add(
        f"Cluster {k} (n={len(members)}, avg {cluster_avg:.2f})",
        points,
        stroke_style={"width": bar_width, "linecap": "butt"},
    )

chart.add(
    f"Average {avg_label}", [(avg_label, -1), (avg_label, n_rows)], stroke_style={"width": 6, "dasharray": "20,12"}
)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
