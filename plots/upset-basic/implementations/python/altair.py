"""anyplot.ai
upset-basic: UpSet Plot for Multi-Set Intersection Analysis
Library: altair 6.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-11-21
"""

import os
import sys


# Remove script directory from sys.path to avoid importing local altair.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per intersection degree in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
TOP_N = 14  # number of largest intersections shown, for readability

# Columns: set these to your table's column names
ELEMENT = "Gene"  # role: element
SET = "Experiment"  # role: sets

# Data: replace this block with your own membership table, for example df = pd.read_csv("memberships.csv")
# One row per (element, set) pair: an element in three sets has three rows.
set_names = ["Exp A", "Exp B", "Exp C", "Exp D", "Exp E"]
base_sizes = [220, 180, 160, 140, 120]
overlap_groups = [
    (["Exp A", "Exp B"], 60),
    (["Exp A", "Exp C"], 40),
    (["Exp B", "Exp C"], 35),
    (["Exp A", "Exp B", "Exp C"], 25),
    (["Exp B", "Exp D"], 30),
    (["Exp C", "Exp D"], 20),
    (["Exp A", "Exp D"], 18),
    (["Exp D", "Exp E"], 22),
    (["Exp A", "Exp B", "Exp D"], 15),
    (["Exp A", "Exp B", "Exp C", "Exp D"], 10),
    (["Exp A", "Exp E"], 12),
    (["Exp B", "Exp C", "Exp E"], 8),
    (["Exp A", "Exp B", "Exp C", "Exp D", "Exp E"], 5),
]
memberships = []
gene_id = 0
for name, size in zip(set_names, base_sizes, strict=True):
    for _ in range(size):
        memberships.append((f"g{gene_id}", name))
        gene_id += 1
for sets_in_group, count in overlap_groups:
    for _ in range(count):
        memberships.extend((f"g{gene_id}", name) for name in sets_in_group)
        gene_id += 1
df = pd.DataFrame(memberships, columns=[ELEMENT, SET])

# Plot: reads only df and the constants above
sets = list(df[SET].unique())
n_sets = len(sets)
set_index = {name: i for i, name in enumerate(sets)}

# Intersections: the exact combination of sets per element, sorted by size (descending)
combos = df.groupby(ELEMENT, sort=False)[SET].agg(lambda s: tuple(sorted(s, key=set_index.get)))
combo_counts = combos.value_counts().rename("size").reset_index()
combo_counts.columns = ["combo", "size"]
combo_counts = combo_counts.sort_values("size", ascending=False, kind="stable").head(TOP_N).reset_index(drop=True)
combo_counts["col_idx"] = range(len(combo_counts))
combo_counts["degree"] = combo_counts["combo"].map(len)
combo_counts["label"] = combo_counts["combo"].map(lambda c: " ∩ ".join(c) if len(c) <= 2 else f"{len(c)}-way")
n_cols = len(combo_counts)

# Set sizes
set_df = df.groupby(SET, sort=False).size().rename("size").reset_index()
set_df.columns = ["set", "size"]
set_df["row_idx"] = set_df["set"].map(set_index)

# Dot matrix: one dot per (intersection, set)
dot_df = pd.DataFrame(
    [
        {
            "col_idx": row.col_idx,
            "row_idx": set_index[name],
            "set": name,
            "active": name in row.combo,
            "degree": row.degree,
        }
        for row in combo_counts.itertuples()
        for name in sets
    ]
)

# Connectors span the first to the last participating row of each intersection
conn_df = pd.DataFrame(
    [
        {
            "col_idx": row.col_idx,
            "y_min": min(set_index[name] for name in row.combo),
            "y_max": max(set_index[name] for name in row.combo),
        }
        for row in combo_counts.itertuples()
        if row.degree >= 2
    ],
    columns=["col_idx", "y_min", "y_max"],
)

degrees = sorted(combo_counts["degree"].unique())
degree_range = [IMPRINT_PALETTE[d - 1] for d in degrees]

# Layout (CSS px, rendered at scale_factor 4 onto the 3200 x 1800 canvas)
TARGET_W, TARGET_H = 3200, 1800
bar_left_w = 130
main_w = 480
bar_top_h = 170
spacer_trim = 34  # the top bars' count axis is wider than the set-name axis; trimming aligns the columns
matrix_h = 135

col_x = alt.X("col_idx:O", axis=None, scale=alt.Scale(paddingInner=0.25))
row_scale = alt.Scale(domain=[-0.5, n_sets - 0.5], reverse=True)  # first set on top
axis_style = {
    "titleFontSize": 16,
    "labelFontSize": 13,
    "titleColor": INK,
    "labelColor": INK_SOFT,
    "domainColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridColor": INK,
    "gridOpacity": 0.10,
}

# 1. Intersection size bars (top)
bar_top = (
    alt.Chart(combo_counts)
    .mark_bar(color=BRAND, stroke=PAGE_BG, strokeWidth=1)
    .encode(
        x=col_x,
        y=alt.Y("size:Q", title=f"Intersection size ({ELEMENT.lower()} count)", axis=alt.Axis(**axis_style)),
        tooltip=[alt.Tooltip("label:N", title="Intersection"), alt.Tooltip("size:Q", title=f"{ELEMENT} count")],
    )
    .properties(width=main_w, height=bar_top_h)
)
bar_labels = (
    alt.Chart(combo_counts)
    .mark_text(dy=-8, fontSize=12, fontWeight="bold")
    .encode(x=col_x, y="size:Q", text=alt.Text("size:Q", format="d"), color=alt.value(INK_SOFT))
    .properties(width=main_w, height=bar_top_h)
)
bar_top_chart = alt.layer(bar_top, bar_labels)

# 2. Dot matrix: muted dots for non-members, connectors, degree-colored dots for members
dot_inactive = (
    alt.Chart(dot_df[~dot_df["active"]])
    .mark_circle(size=90, opacity=0.18)
    .encode(x=col_x, y=alt.Y("row_idx:Q", axis=None, scale=row_scale), color=alt.value(INK_SOFT))
    .properties(width=main_w, height=matrix_h)
)
conn_chart = (
    alt.Chart(conn_df)
    .mark_rule(strokeWidth=3)
    .encode(x=col_x, y=alt.Y("y_min:Q", axis=None, scale=row_scale), y2="y_max:Q", color=alt.value(INK_SOFT))
    .properties(width=main_w, height=matrix_h)
)
dot_active = (
    alt.Chart(dot_df[dot_df["active"]])
    .mark_circle(size=150)
    .encode(
        x=col_x,
        y=alt.Y("row_idx:Q", axis=None, scale=row_scale),
        color=alt.Color(
            "degree:O",
            scale=alt.Scale(domain=degrees, range=degree_range),
            legend=alt.Legend(
                title="Degree",
                titleColor=INK,
                labelColor=INK_SOFT,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                labelFontSize=12,
                titleFontSize=12,
                padding=6,
            ),
        ),
        tooltip=[alt.Tooltip("set:N", title="Set"), alt.Tooltip("degree:Q", title="Degree")],
    )
    .properties(width=main_w, height=matrix_h)
)
matrix_layer = alt.layer(dot_inactive, conn_chart, dot_active)

# 3. Set size bars (left), set names as the row axis
set_bar = (
    alt.Chart(set_df)
    .mark_bar(color=BRAND, opacity=0.75)
    .encode(
        y=alt.Y(
            "set:N",
            sort=sets,
            title=None,
            axis=alt.Axis(labelFontSize=13, labelColor=INK_SOFT, domainColor=INK_SOFT, tickColor=INK_SOFT),
        ),
        x=alt.X(
            "size:Q",
            title=f"Set size ({ELEMENT.lower()} count)",
            axis=alt.Axis(**axis_style),
            scale=alt.Scale(reverse=True),
        ),
        tooltip=[alt.Tooltip("set:N", title="Set"), alt.Tooltip("size:Q", title=f"{ELEMENT} count")],
    )
    .properties(width=bar_left_w, height=matrix_h)
)

# Invisible spacer keeps the top bars aligned with the matrix columns
spacer_top = (
    alt.Chart(pd.DataFrame({"x": [0]}))
    .mark_point(opacity=0)
    .encode(x=alt.X("x:Q", axis=None))
    .properties(width=bar_left_w - spacer_trim, height=bar_top_h, view=alt.ViewConfig(stroke=None))
)

title = "upset-basic · python · altair · anyplot.ai"
title_fontsize = round(22 * min(1.0, 67 / len(title)))
chart = (
    alt.vconcat(
        alt.hconcat(spacer_top, bar_top_chart, spacing=4), alt.hconcat(set_bar, matrix_layer, spacing=4), spacing=8
    )
    .properties(title=alt.Title(title, fontSize=title_fontsize, color=INK, anchor="start"), background=PAGE_BG)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_concat(spacing=4)
)

# Save: vl-convert pads outside the view, so shrink if oversized, pad up to the exact target canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
img.thumbnail((TARGET_W, TARGET_H), Image.LANCZOS)  # on other data the labels can grow; shrink, never crop
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
