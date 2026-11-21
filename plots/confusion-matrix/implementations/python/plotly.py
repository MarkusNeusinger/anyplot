""" anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: plotly 7.1.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Sequential Imprint colormap: low counts green, high counts blue (same in both themes)
imprint_seq = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Constants
CELL_TEXT_DARK = "#1A1A17"  # annotation color on the lighter half of the scale
CELL_TEXT_LIGHT = "#FFFFFF"  # annotation color on the darker half of the scale
COUNT = "Count"  # colorbar title: cell values are raw counts

# Columns: set these to your table's column names
TRUE_LABEL = "True class"  # role: true_labels
PREDICTED_LABEL = "Predicted class"  # role: predicted_labels
CLASS_NAMES = "Class"  # role: class_names

# Data: replace this block with your own labeled square matrix (rows = true class, columns = predicted class)
# for example df = pd.crosstab(y_true, y_pred)
df = pd.DataFrame(
    [
        [92, 6, 1, 1, 0],  # Defective: almost always caught correctly
        [5, 78, 12, 4, 1],  # Poor: some confusion with Average
        [2, 14, 71, 10, 3],  # Average: scattered confusion across range
        [1, 5, 13, 75, 6],  # Good: mostly correct, some confused with Average/Excellent
        [0, 1, 4, 8, 87],  # Excellent: very reliable classification
    ],
    index=["Defective", "Poor", "Average", "Good", "Excellent"],
    columns=["Defective", "Poor", "Average", "Good", "Excellent"],
).rename_axis(index=CLASS_NAMES, columns=CLASS_NAMES)

# Plot: reads only df and the constants above
top = np.nanmax(df.to_numpy(dtype=float))
annotations = [
    dict(
        x=predicted,
        y=true,
        text=str(df.loc[true, predicted]),
        font=dict(size=15, color=CELL_TEXT_LIGHT if df.loc[true, predicted] > top / 2 else CELL_TEXT_DARK),
        showarrow=False,
    )
    for true in df.index
    for predicted in df.columns
    if pd.notna(df.loc[true, predicted])
]

fig = go.Figure(
    go.Heatmap(
        z=df.to_numpy(),
        x=list(df.columns),
        y=list(df.index),
        colorscale=imprint_seq,
        xgap=2,
        ygap=2,
        colorbar=dict(
            title=dict(text=COUNT, font=dict(size=13, color=INK)),
            tickfont=dict(size=11, color=INK_SOFT),
            thickness=16,
            len=0.75,
            outlinewidth=0,
            tickcolor=INK_SOFT,
        ),
        hovertemplate=f"{TRUE_LABEL}: %{{y}}<br>{PREDICTED_LABEL}: %{{x}}<br>{COUNT}: %{{z}}<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    title=dict(
        text="confusion-matrix · python · plotly · anyplot.ai", font=dict(size=17, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text=PREDICTED_LABEL, font=dict(size=14, color=INK)),
        tickfont=dict(size=12, color=INK_SOFT),
        side="bottom",
        showgrid=False,
        linecolor=INK_SOFT,
        constrain="domain",
    ),
    yaxis=dict(
        title=dict(text=TRUE_LABEL, font=dict(size=14, color=INK)),
        tickfont=dict(size=12, color=INK_SOFT),
        autorange="reversed",
        showgrid=False,
        linecolor=INK_SOFT,
        scaleanchor="x",
        scaleratio=1,
        constrain="domain",
    ),
    annotations=annotations,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=90, r=60, t=70, b=70),
    font=dict(family="Arial, sans-serif", color=INK),
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
