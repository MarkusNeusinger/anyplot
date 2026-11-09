""" anyplot.ai
silhouette-basic: Silhouette Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SAMPLE = "Flower"  # role: samples
CLUSTER = "Cluster"  # role: cluster_labels
SILHOUETTE = "Silhouette coefficient"  # role: silhouette_values

# Data: replace this block with your own table, for example df = pd.read_csv("clustered.csv")
# The 150 iris flowers (four measurements in cm), clustered by k-means into three groups
iris = load_iris()
labels = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(iris.data)
df = pd.DataFrame(
    {
        SAMPLE: [f"Iris {number}" for number in range(1, len(labels) + 1)],
        CLUSTER: labels,
        SILHOUETTE: silhouette_samples(iris.data, labels),
    }
)

# Plot: reads only df and the constants above; a sample with a missing value has no bar to draw
samples = df.dropna(subset=[CLUSTER, SILHOUETTE])
overall_mean = samples[SILHOUETTE].mean()
gap = max(2, len(samples) // 15)

fig = go.Figure()
block_centres, block_labels = [], []
block_start = 0
for i, (cluster, block) in enumerate(samples.sort_values([CLUSTER, SILHOUETTE]).groupby(CLUSTER, sort=True)):
    rows = block_start + np.arange(len(block))
    fig.add_trace(
        go.Bar(
            x=block[SILHOUETTE],
            y=rows,
            width=1,
            orientation="h",
            marker={"color": IMPRINT_PALETTE[i], "line": {"width": 0}},
            name=f"{CLUSTER} {cluster}",
            customdata=block[SAMPLE],
            hovertemplate="%{customdata}: %{x:.3f}<extra>%{fullData.name}</extra>",
        )
    )
    block_centres.append(rows.mean())
    block_labels.append(f"{CLUSTER} {cluster} · avg {block[SILHOUETTE].mean():.2f}")
    block_start += len(block) + gap

# Mean silhouette over all samples, labelled above the plot so no bar sits under the text
fig.add_vline(x=overall_mean, line={"color": INK, "width": 2, "dash": "dash"})
fig.add_annotation(
    x=overall_mean,
    y=1,
    yref="paper",
    yanchor="bottom",
    yshift=4,
    text=f"Average silhouette {overall_mean:.2f}",
    showarrow=False,
    font={"size": 10, "color": INK},
)

# Bars run from zero; the axis spans every score, zero and the mean line, padded on both sides
lowest = min(samples[SILHOUETTE].min(), 0)
highest = max(samples[SILHOUETTE].max(), overall_mean)
pad = 0.04 * (highest - lowest)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 150, "r": 40, "t": 80, "b": 60},
    title={"text": "silhouette-basic · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    bargap=0,
    showlegend=False,
    xaxis={
        "title": {"text": SILHOUETTE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [lowest - pad, highest + pad],
        "showgrid": True,
        "gridcolor": GRID,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 1,
        "showline": True,
        "linecolor": INK_SOFT,
        "ticks": "",
    },
    yaxis={
        "title": {"text": "Samples, sorted within each cluster", "font": {"size": 12, "color": INK}},
        "tickmode": "array",
        "tickvals": block_centres,
        "ticktext": block_labels,
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [-gap / 2, block_start - gap / 2],
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "ticks": "",
    },
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
