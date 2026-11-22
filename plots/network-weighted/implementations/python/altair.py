"""anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SOURCE = "Exporter"  # role: edges
TARGET = "Importer"  # role: extra
WEIGHT = "Trade volume (billion USD)"  # role: weight
NODE = "Country"  # role: nodes
REGION = "Region"  # role: extra

# Data: replace this block with your own edge list, for example df = pd.read_csv("trade.csv")
np.random.seed(42)
nodes = pd.DataFrame(
    {
        NODE: [
            "USA",
            "China",
            "Germany",
            "Japan",
            "UK",
            "France",
            "India",
            "Italy",
            "Brazil",
            "Canada",
            "S. Korea",
            "Australia",
            "Mexico",
            "Spain",
            "Netherlands",
        ],
        REGION: [
            "Americas",
            "Asia",
            "Europe",
            "Asia",
            "Europe",
            "Europe",
            "Asia",
            "Europe",
            "Americas",
            "Americas",
            "Asia",
            "Oceania",
            "Americas",
            "Europe",
            "Europe",
        ],
    }
)

df = pd.DataFrame(
    [
        ("USA", "China", 560),
        ("USA", "Germany", 185),
        ("USA", "Japan", 210),
        ("USA", "UK", 140),
        ("USA", "Canada", 580),
        ("USA", "Mexico", 490),
        ("China", "Japan", 320),
        ("China", "S. Korea", 280),
        ("China", "Germany", 175),
        ("China", "Australia", 145),
        ("Germany", "France", 165),
        ("Germany", "Italy", 130),
        ("Germany", "Netherlands", 195),
        ("Germany", "UK", 125),
        ("Japan", "S. Korea", 85),
        ("Japan", "Australia", 75),
        ("UK", "France", 95),
        ("UK", "Netherlands", 85),
        ("France", "Italy", 80),
        ("France", "Spain", 75),
        ("India", "USA", 95),
        ("India", "China", 110),
        ("Brazil", "USA", 60),
        ("Brazil", "China", 115),
        ("Canada", "UK", 25),
        ("S. Korea", "USA", 120),
        ("Australia", "China", 190),
        ("Mexico", "China", 45),
        ("Spain", "France", 55),
        ("Netherlands", "UK", 70),
    ],
    columns=[SOURCE, TARGET, WEIGHT],
)

# Plot: reads only df, nodes and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
TOTAL = "Total trade (billion USD)"
regions = list(dict.fromkeys(nodes[REGION]))
names = list(nodes[NODE])
index = {name: i for i, name in enumerate(names)}
src = df[SOURCE].map(index).to_numpy()
tgt = df[TARGET].map(index).to_numpy()
w = df[WEIGHT].to_numpy(dtype=float)

# Force-directed layout (Fruchterman-Reingold), attraction scaled by edge weight
n = len(names)
pos = np.random.rand(n, 2) * 2 - 1
k = 0.3
w_rel = w / np.nanmax(w)
steps = 200
for it in range(steps):
    delta = pos[:, None, :] - pos[None, :, :]
    dist = np.maximum(np.linalg.norm(delta, axis=2), 0.01)
    disp = ((delta / dist[..., None]) * (k * k / dist)[..., None]).sum(axis=1)
    for s, t, wr in zip(src, tgt, w_rel, strict=True):
        d = pos[s] - pos[t]
        dd = max(np.linalg.norm(d), 0.01)
        pull = (d / dd) * dd * dd / k * (0.25 + 0.5 * wr)
        disp[s] -= pull
        disp[t] += pull
    length = np.maximum(np.linalg.norm(disp, axis=1), 0.01)
    temp = 0.1 * (1 - it / steps)
    pos += (disp / length[:, None]) * np.minimum(length, temp)[:, None]
    pos = np.clip(pos, -1, 1)

# Weighted degree: sum of the weights of every edge at a node
strength = np.zeros(n)
np.add.at(strength, src, w)
np.add.at(strength, tgt, w)

node_df = pd.DataFrame({NODE: names, REGION: nodes[REGION], TOTAL: strength, "x": pos[:, 0], "y": pos[:, 1]})
edge_df = pd.DataFrame(
    {
        WEIGHT: w,
        "x": pos[src, 0],
        "y": pos[src, 1],
        "x2": pos[tgt, 0],
        "y2": pos[tgt, 1],
        SOURCE: df[SOURCE],
        TARGET: df[TARGET],
    }
)

limit = float(np.abs(pos).max()) * 1.2
x_scale = alt.Scale(domain=[-limit, limit])
y_scale = alt.Scale(domain=[-limit, limit])
legend_style = {"titleFontSize": 12, "labelFontSize": 11, "offset": 6, "padding": 6}

edge_layer = (
    alt.Chart(edge_df)
    .mark_rule(opacity=0.45, strokeCap="round")
    .encode(
        x=alt.X("x", type="quantitative", axis=None, scale=x_scale),
        y=alt.Y("y", type="quantitative", axis=None, scale=y_scale),
        x2="x2",
        y2="y2",
        strokeWidth=alt.StrokeWidth(
            WEIGHT.translate(ESCAPE),
            type="quantitative",
            title="Trade (billion USD)",
            scale=alt.Scale(domain=[float(w.min()), float(w.max())], range=[1, 7]),
            legend=alt.Legend(**legend_style, symbolStrokeColor=INK_SOFT, symbolType="stroke"),
        ),
        color=alt.value(INK_SOFT),
    )
)

node_layer = (
    alt.Chart(node_df)
    .mark_circle(stroke=INK_SOFT, strokeWidth=1, opacity=1)
    .encode(
        x=alt.X("x", type="quantitative", axis=None, scale=x_scale),
        y=alt.Y("y", type="quantitative", axis=None, scale=y_scale),
        size=alt.Size(
            TOTAL.translate(ESCAPE),
            type="quantitative",
            title="Total trade (billion USD)",
            scale=alt.Scale(domain=[float(strength.min()), float(strength.max())], range=[150, 900]),
            legend=alt.Legend(**legend_style, symbolFillColor=INK_SOFT),
        ),
        color=alt.Color(
            REGION.translate(ESCAPE),
            type="nominal",
            title=REGION,
            sort=None,
            scale=alt.Scale(domain=regions, range=IMPRINT_PALETTE),
            legend=alt.Legend(**legend_style, symbolSize=200),
        ),
        tooltip=[alt.Tooltip(NODE.translate(ESCAPE), title=NODE), alt.Tooltip(REGION.translate(ESCAPE), title=REGION)],
    )
)

label_layer = (
    alt.Chart(node_df)
    .mark_text(fontSize=11, fontWeight="bold", dy=-17, align="center", color=INK)
    .encode(
        x=alt.X("x", type="quantitative", axis=None, scale=x_scale),
        y=alt.Y("y", type="quantitative", axis=None, scale=y_scale),
        text=alt.Text(NODE.translate(ESCAPE), type="nominal"),
    )
)

chart = (
    (edge_layer + node_layer + label_layer)
    .resolve_scale(size="independent", strokeWidth="independent", color="independent")
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "International trade flows · network-weighted · python · altair · anyplot.ai",
            fontSize=15,
            anchor="middle",
            color=INK,
            subtitle="Edge thickness shows bilateral trade volume; node size shows total trade",
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair render {img.width}x{img.height} exceeds target {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
