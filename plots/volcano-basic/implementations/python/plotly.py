""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_UP = IMPRINT_PALETTE[4]  # semantic: red for up-regulated
COLOR_DOWN = IMPRINT_PALETTE[2]  # semantic: blue for down-regulated

# Constants
FC_THRESHOLD = 1.0  # |log2 fold change| cutoff (2-fold change)
P_THRESHOLD = 0.05  # significance cutoff on the p-value
N_LABELED = 5  # how many top significant features get a name

# Columns: set these to your table's column names
FOLD_CHANGE = "log₂ fold change"  # role: log2_fold_change
SIGNIFICANCE = "-log₁₀(p-value)"  # role: neg_log10_pvalue
GENE = "Gene"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("results.csv")
rng = np.random.default_rng(42)
n_genes = 500
fold_change = rng.normal(0, 1.5, n_genes)
base_p = rng.beta(1, 3, n_genes)
p_values = np.clip(base_p * np.exp(-np.abs(fold_change) / 5 * 3), 1e-20, 1)
df = pd.DataFrame(
    {FOLD_CHANGE: fold_change, SIGNIFICANCE: -np.log10(p_values), GENE: [f"Gene_{i}" for i in range(n_genes)]}
)

# Plot: reads only df and the constants above
y_cut = -np.log10(P_THRESHOLD)
is_sig = df[SIGNIFICANCE] > y_cut
groups = [
    ("Not significant", ~(is_sig & (df[FOLD_CHANGE].abs() > FC_THRESHOLD)), INK_SOFT, 5, 0.4),
    ("Down-regulated", is_sig & (df[FOLD_CHANGE] < -FC_THRESHOLD), COLOR_DOWN, 7, 0.8),
    ("Up-regulated", is_sig & (df[FOLD_CHANGE] > FC_THRESHOLD), COLOR_UP, 7, 0.8),
]

fig = go.Figure()
for name, mask, color, size, opacity in groups:
    rows = df[mask]
    fig.add_trace(
        go.Scatter(
            x=rows[FOLD_CHANGE],
            y=rows[SIGNIFICANCE],
            mode="markers",
            marker=dict(size=size, color=color, opacity=opacity),
            name=name,
            text=rows[GENE],
            hovertemplate="%{text}<br>log₂FC: %{x:.2f}<br>-log₁₀(p): %{y:.2f}<extra></extra>",
        )
    )

# Threshold lines
line_style = dict(color=INK_SOFT, width=1.5, dash="dash")
fig.add_hline(y=y_cut, line=line_style)
fig.add_vline(x=-FC_THRESHOLD, line=line_style)
fig.add_vline(x=FC_THRESHOLD, line=line_style)

# Label offsets in points, cycled so neighbouring names do not collide
LABEL_OFFSETS = [(18, -18), (-45, -18), (40, -8)]

# Name the most significant features among the colored ones
colored = df[groups[1][1] | groups[2][1]]
annotations = [
    dict(
        x=row[FOLD_CHANGE],
        y=row[SIGNIFICANCE],
        text=row[GENE],
        showarrow=True,
        arrowhead=2,
        arrowwidth=1,
        arrowcolor=INK_SOFT,
        ax=LABEL_OFFSETS[i % len(LABEL_OFFSETS)][0],
        ay=LABEL_OFFSETS[i % len(LABEL_OFFSETS)][1],
        font=dict(size=10, color=INK),
    )
    for i, (_, row) in enumerate(colored.nlargest(N_LABELED, SIGNIFICANCE).iterrows())
]

# Style
title = "volcano-basic · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=70, r=30, t=60, b=60),
    title=dict(text=title, font=dict(size=16, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text=FOLD_CHANGE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        zeroline=False,
        gridcolor=GRID,
        linecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text=SIGNIFICANCE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        zeroline=False,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        range=[0, df[SIGNIFICANCE].max() * 1.08],
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        font=dict(size=10, color=INK_SOFT),
        x=0.02,
        y=0.98,
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        itemsizing="constant",
    ),
    annotations=annotations,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
