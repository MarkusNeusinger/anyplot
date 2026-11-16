"""anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-16
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

# Imprint palette: sequential ramp (single polarity) runs brand green -> blue
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Columns: set these to your table's column names
RESEARCHER = "Researcher"  # role: source
PARTNER = "Co-author"  # role: target
STRENGTH = "Collaboration strength"  # role: weight

# Data: replace this block with your own table, e.g. df = edges.pivot(index=..., columns=..., values=...)
# Academic co-authorship network: 3 departments with 8 members each, nodes ordered by department
rng = np.random.default_rng(42)
n_per_dept = 8
nodes = [f"{dept}{i + 1:02d}" for dept in ("Ph", "Bi", "Ch") for i in range(n_per_dept)]
adj = np.zeros((len(nodes), len(nodes)))
for i in range(len(nodes)):
    for j in range(i + 1, len(nodes)):
        if i // n_per_dept == j // n_per_dept:
            weight = rng.uniform(0.45, 1.0) if rng.random() > 0.18 else 0.0
        else:
            weight = rng.uniform(0.08, 0.38) if rng.random() > 0.74 else 0.0
        adj[i, j] = adj[j, i] = weight  # undirected: both triangles filled
df = pd.DataFrame(adj, index=nodes, columns=nodes)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
order = list(df.index)
long = (
    df.rename_axis(index=RESEARCHER, columns=PARTNER)
    .stack()
    .rename(STRENGTH)
    .reset_index()
    .assign(**{STRENGTH: lambda t: t[STRENGTH].where(t[STRENGTH] > 0)})  # absent edge -> missing
)
present = long.dropna(subset=[STRENGTH])

x_enc = alt.X(PARTNER.translate(ESCAPE), type="ordinal", scale=alt.Scale(domain=order), title=PARTNER)
y_enc = alt.Y(RESEARCHER.translate(ESCAPE), type="ordinal", scale=alt.Scale(domain=order), title=RESEARCHER)

# Layer 1: every cell as a neutral tile, so an absent edge reads as "no edge", never as a weak one
base = alt.Chart(long).mark_rect(fill=ELEVATED_BG, stroke=PAGE_BG, strokeWidth=0.5).encode(x=x_enc, y=y_enc)

# Layer 2: present edges, colour intensity = weight
edges = (
    alt.Chart(present)
    .mark_rect(stroke=PAGE_BG, strokeWidth=0.5)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            STRENGTH.translate(ESCAPE),
            type="quantitative",
            title=STRENGTH,
            scale=alt.Scale(range=IMPRINT_SEQ, domain=[0, float(np.nanmax(df.to_numpy()))]),
            legend=alt.Legend(gradientLength=300, gradientThickness=18),
        ),
        tooltip=[
            alt.Tooltip(RESEARCHER.translate(ESCAPE), type="ordinal", title=RESEARCHER),
            alt.Tooltip(PARTNER.translate(ESCAPE), type="ordinal", title=PARTNER),
            alt.Tooltip(STRENGTH.translate(ESCAPE), type="quantitative", title=STRENGTH, format=".2f"),
        ],
    )
)

# Group boundaries between departments, derived from the node-name prefixes
groups = pd.Series([str(name).rstrip("0123456789") for name in order])
cuts = groups.index[groups != groups.shift()][1:].tolist()
cut_df = pd.DataFrame({"at": [order[c] for c in cuts]})
vlines = (
    alt.Chart(cut_df)
    .mark_rule(color=INK, strokeDash=[6, 4], strokeWidth=1.2, opacity=0.7, xOffset=-0.5)
    .encode(x=alt.X("at:O", scale=alt.Scale(domain=order), bandPosition=0, title=PARTNER))
)
hlines = (
    alt.Chart(cut_df)
    .mark_rule(color=INK, strokeDash=[6, 4], strokeWidth=1.2, opacity=0.7, yOffset=-0.5)
    .encode(y=alt.Y("at:O", scale=alt.Scale(domain=order), bandPosition=0, title=RESEARCHER))
)

title = "heatmap-adjacency · python · altair · anyplot.ai"
chart = (
    alt.layer(base, edges, vlines, hlines)
    .properties(width=368, height=368, title=alt.Title(title, fontSize=16), background=PAGE_BG)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=False,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_axisX(labelAngle=-45)
    .configure_title(color=INK)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=12,
        labelFontSize=10,
        padding=8,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the 2400 x 2400 square target
TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, exceeds {TARGET}x{TARGET}; shrink width/height")
if img.size != (TARGET, TARGET):
    canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
    canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
