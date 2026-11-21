""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: pygal 3.1.3 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
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
UP_COLOR = IMPRINT_PALETTE[4]  # matte red: up-regulated (semantic)
DOWN_COLOR = IMPRINT_PALETTE[2]  # blue: down-regulated (semantic)
REST_COLOR = INK_MUTED  # muted anchor: non-significant

# Constants
POINT_ALPHA = 0.65  # transparency so the dense non-significant mass reads as density
FC_THRESHOLD = 1.0  # |log2 fold change| cutoff (2-fold)
P_THRESHOLD = 0.05  # significance cutoff on the raw p-value

# Columns: set these to your table's column names
LOG2_FC = "Log₂ Fold Change"  # role: log2_fold_change
NEG_LOG10_P = "-Log₁₀(p-value)"  # role: neg_log10_pvalue
GENE = "Gene"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("de_results.csv")
rng = np.random.default_rng(42)
fold_change = np.concatenate([rng.normal(0, 0.5, 400), rng.normal(2.5, 0.5, 50), rng.normal(-2.5, 0.5, 50)])
p_value = rng.uniform(0.001, 0.9, 500)
p_value[400:] = rng.uniform(0.0001, 0.01, 100)
df = pd.DataFrame({GENE: [f"Gene {i}" for i in range(500)], LOG2_FC: fold_change, NEG_LOG10_P: -np.log10(p_value)})

# Plot: reads only df and the constants above
neg_log10_cut = -np.log10(P_THRESHOLD)
is_sig = df[NEG_LOG10_P] > neg_log10_cut
groups = [
    ("Not significant", ~(is_sig & (df[LOG2_FC].abs() > FC_THRESHOLD)), REST_COLOR),
    ("Up-regulated", is_sig & (df[LOG2_FC] > FC_THRESHOLD), UP_COLOR),
    ("Down-regulated", is_sig & (df[LOG2_FC] < -FC_THRESHOLD), DOWN_COLOR),
]

x_lo = float(np.floor(df[LOG2_FC].min() * 1.1))
x_hi = float(np.ceil(df[LOG2_FC].max() * 1.1))
y_hi = float(np.ceil(df[NEG_LOG10_P].max() * 1.1))


def rgba(hex_color, alpha):
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


title = "volcano-basic · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(rgba(REST_COLOR, POINT_ALPHA), rgba(UP_COLOR, POINT_ALPHA), rgba(DOWN_COLOR, POINT_ALPHA), INK, INK, INK),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
    opacity=1,
    opacity_hover=1,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=LOG2_FC,
    y_title=NEG_LOG10_P,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    dots_size=9,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    include_x_axis=True,
    include_y_axis=True,
    explicit_size=True,
    truncate_legend=-1,
    margin=30,
    range=(0, y_hi),
    xrange=(x_lo, x_hi),
)

for name, mask, _color in groups:
    sub = df[mask]
    points = [
        {"value": (float(fc), float(nl)), "label": gene}
        for gene, fc, nl in zip(sub[GENE], sub[LOG2_FC], sub[NEG_LOG10_P], strict=True)
    ]
    chart.add(name, points)

# Threshold lines: dashed, drawn in the ink color so they read through the points
line_style = {"width": 4, "dasharray": "14, 10"}
chart.add(
    f"p = {P_THRESHOLD}",
    [(x_lo, neg_log10_cut), (x_hi, neg_log10_cut)],
    stroke=True,
    show_dots=False,
    stroke_style=line_style,
)
chart.add(
    f"log₂ FC = -{FC_THRESHOLD:g}",
    [(-FC_THRESHOLD, 0.0), (-FC_THRESHOLD, y_hi)],
    stroke=True,
    show_dots=False,
    stroke_style=line_style,
)
chart.add(
    f"log₂ FC = +{FC_THRESHOLD:g}",
    [(FC_THRESHOLD, 0.0), (FC_THRESHOLD, y_hi)],
    stroke=True,
    show_dots=False,
    stroke_style=line_style,
)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
