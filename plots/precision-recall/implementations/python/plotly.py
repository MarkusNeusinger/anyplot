"""anyplot.ai
precision-recall: Precision-Recall Curve
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import average_precision_score, precision_recall_curve


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
F1_LEVELS = [0.2, 0.4, 0.6, 0.8]  # iso-F1 reference contours

# Columns: set these to your table's column names
Y_TRUE = "Fraud label (1 = fraud)"  # role: y_true
Y_SCORE = ["Classifier score"]  # role: y_scores

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# Fraud detection: 1000 transactions, 10% fraudulent, scored by one classifier
np.random.seed(42)
n_samples = 1000
labels = np.zeros(n_samples, dtype=int)
labels[:100] = 1
np.random.shuffle(labels)
scores = np.where(
    labels == 1,
    np.random.beta(5, 2, n_samples),  # higher scores for fraud
    np.random.beta(2, 5, n_samples),  # lower scores for legitimate
)
df = pd.DataFrame({Y_TRUE: labels, Y_SCORE[0]: scores})

# Plot: reads only df and the constants above
valid = df[[Y_TRUE, *Y_SCORE]].dropna()
y_true = (valid[Y_TRUE] > valid[Y_TRUE].min()).astype(int)  # any two-level label column becomes 0/1
y_score = valid[Y_SCORE[0]]
precision, recall, _ = precision_recall_curve(y_true, y_score)
average_precision = average_precision_score(y_true, y_score)
positive_ratio = y_true.mean()

fig = go.Figure()

# Iso-F1 contours first so they sit behind the curve
for f1 in F1_LEVELS:
    x_iso = np.linspace(f1 / 2 + 0.005, 1, 200)
    y_iso = f1 * x_iso / (2 * x_iso - f1)
    keep = (y_iso > 0) & (y_iso <= 1)
    fig.add_trace(
        go.Scatter(
            x=x_iso[keep],
            y=y_iso[keep],
            mode="lines",
            name=f"F1 = {f1}",
            line={"color": INK_SOFT, "width": 1.2, "dash": "dot"},
            opacity=0.55,
            hovertemplate="<b>Iso-F1 %{fullData.name}</b><br>Recall: %{x:.3f}<br>Precision: %{y:.3f}<extra></extra>",
        )
    )

# Random-classifier baseline: horizontal at the positive class ratio
fig.add_trace(
    go.Scatter(
        x=[0, 1],
        y=[positive_ratio, positive_ratio],
        mode="lines",
        name=f"Random baseline ({positive_ratio:.2f})",
        line={"color": IMPRINT_PALETTE[3], "width": 2, "dash": "dash"},
        hovertemplate="<b>Random baseline</b><br>Precision: %{y:.3f}<extra></extra>",
    )
)

# Stepped precision-recall curve
fig.add_trace(
    go.Scatter(
        x=recall,
        y=precision,
        mode="lines",
        name=f"Classifier (AP = {average_precision:.3f})",
        line={"color": IMPRINT_PALETTE[0], "width": 2.5, "shape": "hv"},
        fill="tozeroy",
        fillcolor="rgba(0, 158, 115, 0.15)",
        hovertemplate="<b>Classifier</b><br>Recall: %{x:.3f}<br>Precision: %{y:.3f}<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={
        "text": "precision-recall · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Recall (sensitivity)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [0, 1.02],
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "linewidth": 1,
    },
    yaxis={
        "title": {"text": "Precision (positive predictive value)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [0, 1.05],
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "linewidth": 1,
    },
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 1.01,
        "y": 1.0,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "traceorder": "reversed",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 190, "t": 60, "b": 60},
    hovermode="closest",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
