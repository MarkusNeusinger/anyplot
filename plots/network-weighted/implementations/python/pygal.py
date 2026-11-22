"""anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: pygal 3.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os
import re
import sys
from pathlib import Path


# Work around filename/module name conflict
script_dir = Path(__file__).parent
while str(script_dir) in sys.path:
    sys.path.remove(str(script_dir))

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per region in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WEIGHT_BINS = 4  # edge thickness classes, thinnest to thickest
EDGE_WIDTHS = [4, 9, 15, 22]  # stroke width in px per class

# Columns: set these to your table's column names
ENDPOINTS = ["Exporter", "Importer"]  # role: edges
WEIGHT = "Trade volume (billion USD)"  # role: weight
COUNTRY = "Country"  # role: nodes
REGION = "Region"  # role: extra

# Data: replace this block with your own edge list, for example df = pd.read_csv("edges.csv")
np.random.seed(42)
regions = {
    "Americas": ["USA", "CAN", "MEX", "BRA"],
    "Europe": ["DEU", "FRA", "GBR", "ITA"],
    "Asia": ["CHN", "JPN", "KOR", "IND"],
    "Oceania": ["AUS"],
}
nodes = pd.DataFrame(
    [(country, region) for region, members in regions.items() for country in members], columns=[COUNTRY, REGION]
)
df = pd.DataFrame(
    [
        ("USA", "CAN", 650),
        ("USA", "MEX", 580),
        ("USA", "CHN", 520),
        ("USA", "JPN", 180),
        ("USA", "DEU", 200),
        ("USA", "GBR", 130),
        ("USA", "KOR", 140),
        ("USA", "BRA", 80),
        ("CAN", "CHN", 75),
        ("CAN", "MEX", 40),
        ("MEX", "CHN", 90),
        ("DEU", "FRA", 170),
        ("DEU", "GBR", 120),
        ("DEU", "ITA", 130),
        ("DEU", "CHN", 200),
        ("FRA", "GBR", 90),
        ("FRA", "ITA", 80),
        ("FRA", "CHN", 65),
        ("GBR", "CHN", 95),
        ("CHN", "JPN", 280),
        ("CHN", "KOR", 250),
        ("CHN", "AUS", 180),
        ("CHN", "IND", 100),
        ("JPN", "KOR", 70),
        ("JPN", "AUS", 55),
        ("IND", "AUS", 30),
        ("BRA", "DEU", 20),
    ],
    columns=[*ENDPOINTS, WEIGHT],
)

# Plot: reads only df, nodes and the constants above
node_list = list(pd.unique(df[ENDPOINTS].to_numpy().ravel()))
n = len(node_list)
node_idx = {name: i for i, name in enumerate(node_list)}
src_idx = df[ENDPOINTS[0]].map(node_idx).to_numpy()
tgt_idx = df[ENDPOINTS[1]].map(node_idx).to_numpy()
weights = df[WEIGHT].to_numpy(dtype=float)

# Force-directed layout: pairwise repulsion, weighted attraction along edges
pos = np.random.rand(n, 2) * 2 - 1
k = 1.5 / np.sqrt(n)
t = 0.5
for _ in range(300):
    delta = pos[:, None, :] - pos[None, :, :]
    dist = np.maximum(np.linalg.norm(delta, axis=2), 0.01)
    np.fill_diagonal(dist, np.inf)
    disp = (delta / dist[:, :, None] * (k * k / dist * 1.5)[:, :, None]).sum(axis=1)

    edge_delta = pos[src_idx] - pos[tgt_idx]
    edge_dist = np.maximum(np.linalg.norm(edge_delta, axis=1), 0.01)
    pull = (edge_delta / edge_dist[:, None]) * (edge_dist**2 / k * (0.8 + weights / 400))[:, None]
    np.subtract.at(disp, src_idx, pull)
    np.add.at(disp, tgt_idx, pull)

    disp_norm = np.maximum(np.linalg.norm(disp, axis=1), 0.01)
    pos += disp / disp_norm[:, None] * np.minimum(disp_norm, t)[:, None]
    t *= 0.97

# Normalize positions into the chart's 0-12 range, with a margin for the node discs
pos = (pos - pos.min(axis=0)) / (pos.max(axis=0) - pos.min(axis=0) + 1e-6) * 8 + 2

# Node size encodes weighted degree (sum of connected edge weights)
degree = np.bincount(src_idx, weights, minlength=n) + np.bincount(tgt_idx, weights, minlength=n)
degree_norm = (degree - degree.min()) / max(degree.max() - degree.min(), 1e-6)
radius = 20 + degree_norm * 34

# Edge classes: equal-width weight bins, thicker line for a heavier class
lo, hi = weights.min(), weights.max()
edge_class = np.minimum(((weights - lo) / max(hi - lo, 1e-6) * WEIGHT_BINS).astype(int), WEIGHT_BINS - 1)

region_of = nodes.set_index(COUNTRY)[REGION]
node_regions = region_of.reindex(node_list).fillna("Other")
region_order = list(pd.unique(node_regions))
point_order = np.concatenate([np.flatnonzero(node_regions.to_numpy() == r) for r in region_order])
bounds = [lo + c * (hi - lo) / WEIGHT_BINS for c in range(WEIGHT_BINS + 1)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=40,
    value_font_size=44,
    value_label_font_size=44,
    value_colors=(INK,) * len(region_order),
    stroke_opacity=0.75,
    stroke_opacity_hover=0.75,
    opacity=0.95,
    opacity_hover=1,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="network-weighted · python · pygal · anyplot.ai",
    x_title="Node size = total trade volume · node color = region",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(region_order),
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    stroke=False,
    range=(0, 12),
    xrange=(0, 12),
    print_labels=True,
    print_values=False,
    margin=60,
    margin_bottom=140,
)
for region in region_order:
    points = [
        {"value": tuple(pos[j]), "label": node_list[j], "node": {"r": radius[j]}}
        for j in np.flatnonzero(node_regions.to_numpy() == region)
    ]
    chart.add(region, points, dots_size=40)

svg = chart.render().decode("utf-8")

# Map data coordinates to SVG pixels with a linear fit over the rendered node discs
discs = np.array(re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)"', svg), dtype=float)[: len(point_order)]
placed = pos[point_order]
fit_x = np.polyfit(placed[:, 0], discs[:, 0], 1)
fit_y = np.polyfit(placed[:, 1], discs[:, 1], 1)
pix = np.column_stack([np.polyval(fit_x, pos[:, 0]), np.polyval(fit_y, pos[:, 1])])

# Edges: one line per row of df, thicker for a heavier weight class, drawn beneath the nodes
edge_lines = "".join(
    f'<line x1="{pix[s, 0]:.1f}" y1="{pix[s, 1]:.1f}" x2="{pix[t_, 0]:.1f}" y2="{pix[t_, 1]:.1f}" '
    f'stroke="{INK_MUTED}" stroke-width="{EDGE_WIDTHS[c]}" stroke-linecap="round" opacity="0.7"/>'
    for s, t_, c in zip(src_idx, tgt_idx, edge_class, strict=True)
)

# Edge-width key: one sample line per weight class, labeled with its range
key_y = 1800 - 340
key_x = 120
key = f'<text x="{key_x}" y="{key_y + 14}" font-size="40" font-weight="bold" fill="{INK}">Edge width = trade volume:</text>'
key_x += 640
for c in range(WEIGHT_BINS):
    if not (edge_class == c).any():
        continue
    key += (
        f'<line x1="{key_x}" y1="{key_y}" x2="{key_x + 90}" y2="{key_y}" stroke="{INK_MUTED}" '
        f'stroke-width="{EDGE_WIDTHS[c]}" stroke-linecap="round"/>'
        f'<text x="{key_x + 110}" y="{key_y + 14}" font-size="38" fill="{INK_SOFT}">'
        f"${bounds[c]:.0f}–{bounds[c + 1]:.0f}B</text>"
    )
    key_x += 520

first_series = svg.index('<g class="series')
svg = svg[:first_series] + f'<g class="edges">{edge_lines}</g>' + svg[first_series:]
svg = svg.replace("</svg>", f'<g class="edge-key" font-family="monospace">{key}</g></svg>')

cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg)
