"""anyplot.ai
line-loss-training: Training Loss Curve
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-14
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EPOCH = "Epoch"  # role: epoch
TRAIN_LOSS = "Training Loss"  # role: train_loss
VAL_LOSS = "Validation Loss"  # role: val_loss
LOSS_NAME = "Cross-Entropy Loss"  # extra: loss function shown as the y-axis title

# Data: replace this block with your own table, for example df = pd.read_csv("history.csv")
np.random.seed(42)
epochs = np.arange(1, 71)
train_base = 2.0 - 0.025 * epochs + np.random.normal(0, 0.025, len(epochs))
val_base = 2.0 - 0.020 * epochs + np.random.normal(0, 0.04, len(epochs))
divergence = np.where(epochs > 45, 0.015 * np.sqrt(np.maximum(epochs - 45, 0)), 0)
df = pd.DataFrame(
    {EPOCH: epochs, TRAIN_LOSS: np.maximum(train_base, 0.1), VAL_LOSS: np.maximum(val_base + divergence, 0.15)}
)

# Plot: reads only df and the constants above
best = df.loc[df[VAL_LOSS].idxmin()]
best_epoch, best_loss = int(best[EPOCH]), best[VAL_LOSS]
top = max(df[TRAIN_LOSS].max(), df[VAL_LOSS].max())

fig = go.Figure()
for i, column in enumerate([TRAIN_LOSS, VAL_LOSS]):
    fig.add_trace(
        go.Scatter(
            x=df[EPOCH],
            y=df[column],
            mode="lines",
            name=column,
            line={"color": IMPRINT_PALETTE[i], "width": 3},
            hovertemplate=f"Epoch %{{x}}<br>{column}: %{{y:.3f}}<extra></extra>",
        )
    )

# Minimum validation loss: dashed guide plus a marker on the curve
fig.add_shape(
    type="line",
    x0=best_epoch,
    x1=best_epoch,
    y0=0,
    y1=top,
    line={"color": IMPRINT_PALETTE[1], "width": 1.5, "dash": "dash"},
    opacity=0.5,
)
fig.add_trace(
    go.Scatter(
        x=[best_epoch],
        y=[best_loss],
        mode="markers",
        name=f"Best epoch ({best_epoch})",
        marker={"color": IMPRINT_PALETTE[1], "size": 11, "symbol": "diamond", "line": {"color": INK, "width": 1.5}},
        hovertemplate="Best epoch: %{x}<br>Min validation loss: %{y:.3f}<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 70, "r": 30, "t": 60, "b": 55},
    title={"text": "line-loss-training · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5},
    xaxis={
        "title": {"text": EPOCH, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "range": [df[EPOCH].min() - 1, df[EPOCH].max() + 1],
    },
    yaxis={
        "title": {"text": LOSS_NAME, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "range": [0, top * 1.05],
    },
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.98,
        "y": 0.97,
        "xanchor": "right",
        "yanchor": "top",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    hovermode="x unified",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
