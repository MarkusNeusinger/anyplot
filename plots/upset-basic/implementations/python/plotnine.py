"""anyplot.ai
upset-basic: UpSet Plot for Multi-Set Intersection Analysis
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os
import sys


# Prevent this file from shadowing the installed plotnine package
sys.path = [p for p in sys.path if p not in ("", os.path.dirname(os.path.abspath(__file__)))]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_rect,
    element_text,
    geom_point,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
DOT_DIM = "#C8C7BF" if THEME == "light" else "#3D3D38"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
MAX_COLUMNS = 14  # number of intersections shown, largest first
SEP = "; "  # separator between set names in the sets column

# Columns: set these to your table's column names
ELEMENT = "Gene"  # role: element
SETS = "Experiments"  # role: sets

# Data: replace this block with your own table, for example df = pd.read_csv("genes.csv")
# with one row per element and the sets it belongs to as one string, names joined by SEP.
rng = np.random.default_rng(42)
experiments = ["RNA-seq A", "RNA-seq B", "ChIP-seq", "ATAC-seq", "Proteomics"]
probs = [0.45, 0.40, 0.30, 0.25, 0.20]
n_genes = 600
member = np.column_stack([rng.binomial(1, p, n_genes) for p in probs])
for idx in np.where(member.sum(axis=1) == 0)[0]:
    member[idx, rng.integers(0, len(experiments))] = 1
df = pd.DataFrame(
    {
        ELEMENT: [f"gene_{i:04d}" for i in range(n_genes)],
        SETS: [SEP.join(experiments[j] for j in np.flatnonzero(row)) for row in member],
    }
)

# Plot
# Sets ordered by size (largest at the top), intersections counted per exact combination
memberships = df[SETS].str.split(SEP, regex=False)
set_sizes = memberships.explode().value_counts(sort=True)
set_names = list(set_sizes.index)
n_sets = len(set_names)
combo_counts = memberships.apply(lambda s: tuple(sorted(s, key=set_names.index))).value_counts()
top_ints = [(set(combo), count) for combo, count in combo_counts.head(MAX_COLUMNS).items()]
n_cols = len(top_ints)

# Layout coordinates: set 0 at y=n_sets (top), last set at y=1 (bottom)
set_row_y = {name: float(n_sets - i) for i, name in enumerate(set_names)}

max_count = top_ints[0][1]
BAR_BASE = n_sets + 1.2
BAR_MAX_H = n_sets * 2.2
bar_scale = BAR_MAX_H / max_count

SET_BAR_MAXW = 3.2
SET_BAR_RIGHT = -0.5
set_bar_scale = SET_BAR_MAXW / set_sizes.max()
SET_NAME_X = 0.75

# Intersection bars and their count labels
int_bars_df = pd.DataFrame(
    {
        "xmin": [i + 1 - 0.35 for i in range(n_cols)],
        "xmax": [i + 1 + 0.35 for i in range(n_cols)],
        "ymin": BAR_BASE,
        "ymax": [BAR_BASE + count * bar_scale for _, count in top_ints],
    }
)
count_labels_df = pd.DataFrame(
    {
        "x": [i + 1.0 for i in range(n_cols)],
        "y": [BAR_BASE + count * bar_scale + 0.4 for _, count in top_ints],
        "label": [str(count) for _, count in top_ints],
    }
)

# Connecting segments for multi-set intersections
segs_rows = []
for col_i, (members, _) in enumerate(top_ints):
    active_ys = [set_row_y[s] for s in members]
    if len(active_ys) > 1:
        segs_rows.append({"x": col_i + 1.0, "xend": col_i + 1.0, "y": min(active_ys), "yend": max(active_ys)})
segs_df = pd.DataFrame(segs_rows, columns=["x", "xend", "y", "yend"])

# Dot matrix: every set x column combination
dots_df = pd.DataFrame(
    [
        {"x": col_i + 1.0, "y": set_row_y[name], "active": name in members}
        for col_i, (members, _) in enumerate(top_ints)
        for name in set_names
    ]
)
active_dots = dots_df[dots_df["active"]]
dim_dots = dots_df[~dots_df["active"]]

# Set size horizontal bars and their number labels
set_bars_df = pd.DataFrame(
    {
        "xmin": [SET_BAR_RIGHT - set_sizes[name] * set_bar_scale for name in set_names],
        "xmax": SET_BAR_RIGHT,
        "ymin": [set_row_y[name] - 0.28 for name in set_names],
        "ymax": [set_row_y[name] + 0.28 for name in set_names],
    }
)
set_size_df = pd.DataFrame(
    {
        "x": [SET_BAR_RIGHT - set_sizes[name] * set_bar_scale - 0.15 for name in set_names],
        "y": [set_row_y[name] for name in set_names],
        "label": [str(int(set_sizes[name])) for name in set_names],
    }
)
set_name_df = pd.DataFrame({"x": SET_NAME_X, "y": [set_row_y[name] for name in set_names], "label": set_names})

# Section header above the bars
section_header_df = pd.DataFrame(
    {"x": [(n_cols + 2) / 2.0], "y": [BAR_BASE + BAR_MAX_H + 1.1], "label": ["Intersection Size"]}
)

# Axis limits
x_lo = SET_BAR_RIGHT - SET_BAR_MAXW - 1.0
x_hi = n_cols + 0.8
y_lo = 0.2
y_hi = BAR_BASE + BAR_MAX_H + 1.8

plot = (
    ggplot()
    + geom_rect(
        data=int_bars_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=BRAND,
        color=BRAND,
        alpha=0.92,
    )
    + geom_text(data=count_labels_df, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=5, va="bottom")
    + geom_segment(data=segs_df, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=BRAND, size=1.1)
    + geom_point(data=dim_dots, mapping=aes(x="x", y="y"), color=DOT_DIM, fill=DOT_DIM, size=2.0)
    + geom_point(data=active_dots, mapping=aes(x="x", y="y"), color=BRAND, fill=BRAND, size=2.75)
    + geom_rect(
        data=set_bars_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=INK_SOFT,
        color=INK_SOFT,
        alpha=0.65,
    )
    + geom_text(data=set_size_df, mapping=aes(x="x", y="y", label="label"), color=INK_MUTED, size=4.5, ha="right")
    + geom_text(data=set_name_df, mapping=aes(x="x", y="y", label="label"), color=INK, size=5.5, ha="right")
    + geom_text(data=section_header_df, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=5.5, va="bottom")
    + labs(title="upset-basic · python · plotnine · anyplot.ai")
    + scale_x_continuous(limits=(x_lo, x_hi), expand=(0, 0))
    + scale_y_continuous(limits=(y_lo, y_hi), expand=(0, 0))
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(color=INK, size=12, ha="center"),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
