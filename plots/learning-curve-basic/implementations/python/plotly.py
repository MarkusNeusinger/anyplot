""" anyplot.ai
learning-curve-basic: Model Learning Curve
Library: plotly 7.1.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-20
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TRAIN_SIZE = "Training set size (samples)"  # role: train_sizes
FOLD = "Cross-validation fold"  # role: extra
TRAIN_SCORE = "Training score"  # role: train_scores
VALIDATION_SCORE = "Validation score"  # role: validation_scores
METRIC = "Accuracy"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# One row per training size and cross-validation fold, as sklearn's learning_curve returns them
rng = np.random.default_rng(42)
sizes = np.array([50, 100, 200, 400, 600, 800, 1000, 1500, 2000, 3000])
n_folds = 5
size_grid = np.repeat(sizes, n_folds)
train_base = 0.96 - 0.04 * np.log10(size_grid / 50)
validation_base = 0.68 + 0.20 * (1 - np.exp(-size_grid / 800))
df = pd.DataFrame(
    {
        TRAIN_SIZE: size_grid,
        FOLD: np.tile(np.arange(1, n_folds + 1), len(sizes)),
        TRAIN_SCORE: train_base + rng.normal(0, 0.01, len(size_grid)),
        VALIDATION_SCORE: validation_base + rng.normal(0, 0.02, len(size_grid)),
    }
)

# Plot: reads only df and the constants above
stats = df.groupby(TRAIN_SIZE, sort=False).agg(
    train_mean=(TRAIN_SCORE, "mean"),
    train_std=(TRAIN_SCORE, lambda s: s.std(ddof=0)),
    val_mean=(VALIDATION_SCORE, "mean"),
    val_std=(VALIDATION_SCORE, lambda s: s.std(ddof=0)),
)
x = stats.index.to_numpy()

series = [
    (TRAIN_SCORE, "train_mean", "train_std", IMPRINT_PALETTE[0]),
    (VALIDATION_SCORE, "val_mean", "val_std", IMPRINT_PALETTE[1]),
]

fig = go.Figure()
for name, mean_col, std_col, color in series:
    mean, std = stats[mean_col].to_numpy(), stats[std_col].to_numpy()
    red, green, blue = (int(color[i : i + 2], 16) for i in (1, 3, 5))
    # ±1 std band across folds
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([x, x[::-1]]),
            y=np.concatenate([mean + std, (mean - std)[::-1]]),
            fill="toself",
            fillcolor=f"rgba({red}, {green}, {blue}, 0.2)",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=mean,
            mode="lines+markers",
            name=name,
            line={"color": color, "width": 3},
            marker={"size": 9, "color": color},
            hovertemplate=f"<b>{name}</b><br>Size: %{{x}}<br>{METRIC}: %{{y:.3f}}<extra></extra>",
        )
    )

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={"text": "learning-curve-basic · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}},
    xaxis={
        "title": {"text": TRAIN_SIZE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": True,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": f"{METRIC} (mean ± 1 std across folds)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": True,
        "zeroline": False,
    },
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.98,
        "y": 0.04,
        "xanchor": "right",
        "yanchor": "bottom",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
