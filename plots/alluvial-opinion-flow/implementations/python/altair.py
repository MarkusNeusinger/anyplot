"""anyplot.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: Likert levels carry a semantic color (positive green, negative red, neutral muted anchor)
SEMANTIC = {
    "Strongly Agree": IMPRINT_PALETTE[0],
    "Agree": IMPRINT_PALETTE[7],
    "Neutral": INK_MUTED,
    "Disagree": IMPRINT_PALETTE[3],
    "Strongly Disagree": IMPRINT_PALETTE[4],
}

# Columns: set these to your table's column names
WAVE = "Quarter"  # role: wave
NEXT_WAVE = "Next quarter"  # role: extra
SOURCE = "Opinion"  # role: source_category
TARGET = "Opinion next quarter"  # role: target_category
FLOW = "Respondents"  # role: flow_count

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
# Employee engagement survey: 1,000 staff tracked across 4 quarterly waves, one row per transition
levels = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
quarters = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]
transitions = [
    [[140, 25, 10, 5, 0], [20, 170, 40, 15, 5], [5, 30, 120, 35, 10], [0, 10, 25, 150, 35], [0, 5, 5, 20, 120]],
    [[135, 20, 8, 2, 0], [25, 155, 35, 20, 5], [5, 25, 105, 45, 20], [0, 8, 20, 145, 52], [0, 2, 7, 18, 143]],
    [[140, 18, 5, 2, 0], [22, 135, 30, 18, 5], [3, 22, 100, 35, 15], [0, 5, 15, 155, 55], [0, 2, 5, 15, 198]],
]
df = pd.DataFrame(
    [
        {WAVE: quarters[w], NEXT_WAVE: quarters[w + 1], SOURCE: levels[s], TARGET: levels[t], FLOW: matrix[s][t]}
        for w, matrix in enumerate(transitions)
        for s in range(len(levels))
        for t in range(len(levels))
        if matrix[s][t] > 0
    ]
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
f_source, f_target, f_flow, f_wave = (c.translate(ESCAPE) for c in (SOURCE, TARGET, FLOW, WAVE))

waves = list(df[WAVE].unique()) + [df[NEXT_WAVE].iloc[-1]]
categories = list(pd.unique(pd.concat([df[SOURCE], df[TARGET]])))
cat_colors = [SEMANTIC.get(cat, IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]) for i, cat in enumerate(categories)]
n_waves, n_cats = len(waves), len(categories)

# Respondents per category and wave. A block is as tall as the flows leaving it (first wave) or
# arriving in it (later waves); flows are scaled by the outgoing and incoming sums of their block.
out_sum = [df[df[WAVE] == wave].groupby(SOURCE)[FLOW].sum().to_dict() for wave in waves[:-1]] + [{}]
in_sum = [{}] + [df[df[WAVE] == wave].groupby(TARGET)[FLOW].sum().to_dict() for wave in waves[:-1]]
totals = [{cat: (out_sum[i] if i == 0 else in_sum[i]).get(cat, 0) for cat in categories} for i in range(n_waves)]

# Layout in view units: the view fills the 800 x 450 chart minus title, subtitle and legend
view_w, view_h = 780, 352
top_margin, bottom_margin = 36, 26
left_margin, right_margin = 190, 150
node_w, node_gap = 20, 7
avail_h = view_h - top_margin - bottom_margin
x_pos = [left_margin + i * (view_w - left_margin - right_margin) / (n_waves - 1) for i in range(n_waves)]

node_rows = []
for wi, wave in enumerate(waves):
    wave_total = sum(totals[wi].values())
    usable = avail_h - node_gap * (n_cats - 1)
    cy = top_margin
    for cat in categories:
        nh = totals[wi][cat] / wave_total * usable
        node_rows.append(
            {WAVE: wave, SOURCE: cat, FLOW: totals[wi][cat], "wi": wi, "x": x_pos[wi] - node_w / 2, "y": cy, "h": nh}
        )
        cy += nh + node_gap
nodes_df = pd.DataFrame(node_rows)
nodes_df["x2"] = nodes_df["x"] + node_w
nodes_df["y2"] = nodes_df["y"] + nodes_df["h"]
nodes_df["cx"] = nodes_df["x"] + node_w / 2
nodes_df["cy"] = nodes_df["y"] + nodes_df["h"] / 2
nodes_df["lbl"] = [f"{v:g}" for v in nodes_df[FLOW]]
# Count text: white on dark blocks, page ink on light blocks (relative luminance of the block color)
block_rgb = {
    cat: [int(col[k : k + 2], 16) / 255 for k in (1, 3, 5)] for cat, col in zip(categories, cat_colors, strict=True)
}
block_lum = {cat: 0.2126 * r + 0.7152 * g + 0.0722 * b for cat, (r, g, b) in block_rgb.items()}
nodes_df["txt"] = ["#1A1A17" if block_lum[cat] > 0.5 else "#FFFFFF" for cat in nodes_df[SOURCE]]
node_at = nodes_df.set_index(["wi", SOURCE])

# Flow polygons: a smoothstep band from the source block to the target block, stacked inside each block
out_off = node_at["y"].to_dict()
in_off = node_at["y"].to_dict()
n_pts = 40
flow_rows = []
for _, row in df.iterrows():
    wi = waves.index(row[WAVE])
    src, tgt, val = row[SOURCE], row[TARGET], row[FLOW]
    s_node, t_node = node_at.loc[(wi, src)], node_at.loc[(wi + 1, tgt)]
    s_top = out_off[(wi, src)]
    t_top = in_off[(wi + 1, tgt)]
    s_h = val / out_sum[wi][src] * s_node["h"]
    t_h = val / in_sum[wi + 1][tgt] * t_node["h"]
    out_off[(wi, src)] += s_h
    in_off[(wi + 1, tgt)] += t_h
    xs, xe = s_node["x"] + node_w, t_node["x"]
    ts = [i / (n_pts - 1) for i in range(n_pts)]
    top_edge = [(xs + t * (xe - xs), s_top + t * t * (3 - 2 * t) * (t_top - s_top)) for t in ts]
    bottom_edge = [(xs + t * (xe - xs), s_top + s_h + t * t * (3 - 2 * t) * (t_top + t_h - s_top - s_h)) for t in ts]
    for k, (px, py) in enumerate(top_edge + bottom_edge[::-1]):
        flow_rows.append(
            {
                "fid": f"{wi}|{src}|{tgt}",
                SOURCE: src,
                TARGET: tgt,
                FLOW: val,
                "x": px,
                "y": py,
                "ord": k,
                "stable": src == tgt,
            }
        )
flows_df = pd.DataFrame(flow_rows)

# Side labels: first-wave count on the left, last-wave count with the change since the first wave on the right
first_wave = nodes_df[nodes_df["wi"] == 0]
last_wave = nodes_df[nodes_df["wi"] == n_waves - 1]
label_rows = [
    {"x": r["x"] - 6, "y": r["cy"], "text": f"{r[SOURCE]} ({r[FLOW]:g})", "side": "left"}
    for _, r in first_wave.iterrows()
]
for _, r in last_wave.iterrows():
    delta = r[FLOW] - totals[0][r[SOURCE]]
    label_rows.append({"x": r["x2"] + 6, "y": r["cy"], "text": f"({r[FLOW]:g}) {delta:+g}", "side": "right"})
labels_df = pd.DataFrame(label_rows)

# Wave headers above the blocks, faint bands behind each column
headers_df = pd.DataFrame({"x": x_pos, "y": top_margin - 14, "text": waves})
bands_df = pd.DataFrame(
    {
        "x": [x - node_w for x in x_pos],
        "x2": [x + node_w for x in x_pos],
        "y": top_margin - 6,
        "y2": nodes_df["y2"].max() + 6,
    }
)

# Trend note: share of respondents in the two extreme categories, first versus last wave
extreme_share = [(totals[i][categories[0]] + totals[i][categories[-1]]) / sum(totals[i].values()) for i in (0, -1)]
trend_df = pd.DataFrame(
    [
        {
            "x": view_w / 2,
            "y": nodes_df["y2"].max() + 16,
            "text": f"{categories[0]} + {categories[-1]}: {extreme_share[0]:.0%} of respondents in {waves[0]}, "
            f"{extreme_share[1]:.0%} in {waves[-1]}",
        }
    ]
)

xs_scale = alt.Scale(domain=[0, view_w])
ys_scale = alt.Scale(domain=[0, view_h], reverse=True)
color_scale = alt.Scale(domain=categories, range=cat_colors)
hover = alt.selection_point(fields=[SOURCE.translate(ESCAPE)], on="pointerover")


def_x = alt.X("x:Q", scale=xs_scale, axis=None)
def_y = alt.Y("y:Q", scale=ys_scale, axis=None)

flow_color = alt.Color(f_source, type="nominal", scale=color_scale, legend=None)
stable_flows = (
    alt.Chart(flows_df)
    .transform_filter("datum.stable")
    .mark_line(filled=True, strokeWidth=0)
    .encode(
        x=def_x,
        y=def_y,
        color=flow_color,
        detail="fid:N",
        order="ord:Q",
        opacity=alt.condition(hover, alt.value(0.75), alt.value(0.6)),
        tooltip=[
            alt.Tooltip(f_source, type="nominal", title="Stays in"),
            alt.Tooltip(f_flow, type="quantitative", title=FLOW),
        ],
    )
)
change_flows = (
    alt.Chart(flows_df)
    .transform_filter("!datum.stable")
    .mark_line(filled=True, strokeWidth=0)
    .encode(
        x=def_x,
        y=def_y,
        color=flow_color,
        detail="fid:N",
        order="ord:Q",
        opacity=alt.condition(hover, alt.value(0.5), alt.value(0.3)),
        tooltip=[
            alt.Tooltip(f_source, type="nominal", title=SOURCE),
            alt.Tooltip(f_target, type="nominal", title=TARGET),
            alt.Tooltip(f_flow, type="quantitative", title=FLOW),
        ],
    )
)

nodes_layer = (
    alt.Chart(nodes_df)
    .mark_rect(stroke=INK_SOFT, strokeWidth=0.8, cornerRadius=3)
    .encode(
        x=alt.X("x:Q", scale=xs_scale, axis=None),
        y=alt.Y("y:Q", scale=ys_scale, axis=None),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color(f_source, type="nominal", scale=color_scale, legend=None),
        tooltip=[
            alt.Tooltip(f_wave, type="nominal", title=WAVE),
            alt.Tooltip(f_source, type="nominal", title=SOURCE),
            alt.Tooltip(f_flow, type="quantitative", title=FLOW),
        ],
    )
    .add_params(hover)
)

count_labels = (
    alt.Chart(nodes_df)
    .transform_filter(alt.datum.h >= 12)
    .mark_text(fontSize=11, fontWeight="bold", baseline="middle", align="center")
    .encode(
        x=alt.X("cx:Q", scale=xs_scale),
        y=alt.Y("cy:Q", scale=ys_scale),
        text="lbl:N",
        color=alt.Color("txt:N", scale=None, legend=None),
    )
)

side_labels = [
    alt.Chart(labels_df)
    .transform_filter(alt.datum.side == side)
    .mark_text(fontSize=12, color=INK_SOFT, align=align, baseline="middle")
    .encode(x=alt.X("x:Q", scale=xs_scale), y=alt.Y("y:Q", scale=ys_scale), text="text:N")
    for side, align in (("left", "right"), ("right", "left"))
]

wave_headers = (
    alt.Chart(headers_df)
    .mark_text(fontSize=13, fontWeight="bold", color=INK, baseline="bottom", align="center")
    .encode(x=alt.X("x:Q", scale=xs_scale), y=alt.Y("y:Q", scale=ys_scale), text="text:N")
)

trend_note = (
    alt.Chart(trend_df)
    .mark_text(fontSize=11, fontStyle="italic", color=INK_MUTED, baseline="top", align="center")
    .encode(x=alt.X("x:Q", scale=xs_scale), y=alt.Y("y:Q", scale=ys_scale), text="text:N")
)

wave_bands = (
    alt.Chart(bands_df)
    .mark_rect(color=INK_MUTED, opacity=0.12, cornerRadius=4)
    .encode(x=alt.X("x:Q", scale=xs_scale, axis=None), x2="x2:Q", y=alt.Y("y:Q", scale=ys_scale, axis=None), y2="y2:Q")
)

# Title: mandated format, font size scaled down for long titles
title_str = "alluvial-opinion-flow · python · altair · anyplot.ai"
title_fs = max(11, round(16 * (67 / len(title_str) if len(title_str) > 67 else 1.0)))

chart = (
    alt.layer(wave_bands, change_flows, stable_flows, nodes_layer, count_labels, *side_labels, wave_headers, trend_note)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(
            text=title_str,
            subtitle="Employee Engagement Survey — 1,000 Staff Quarterly Sentiment Tracking",
            fontSize=title_fs,
            subtitleFontSize=11,
            subtitleColor=INK_MUTED,
            anchor="middle",
            color=INK,
            offset=8,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .interactive()
)

# Save: 3200 x 1800 landscape
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")
