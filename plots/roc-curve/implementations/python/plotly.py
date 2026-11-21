"""anyplot.ai
roc-curve: ROC Curve with AUC
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import auc, roc_curve
from sklearn.tree import DecisionTreeClassifier


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per model in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MODEL = "Model"  # role: extra
FPR = "False Positive Rate"  # role: fpr
TPR = "True Positive Rate"  # role: tpr
AUC = "AUC"  # role: auc

# Data: replace this block with your own table, for example df = pd.read_csv("roc_points.csv")
np.random.seed(42)
X, y = make_classification(n_samples=500, n_features=10, n_informative=8, random_state=42, class_sep=1.5)
classifiers = {
    "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
    "Decision Tree": DecisionTreeClassifier(random_state=42, max_depth=5),
}
frames = []
for name, clf in classifiers.items():
    clf.fit(X, y)
    fpr, tpr, _ = roc_curve(y, clf.predict_proba(X)[:, 1])
    frames.append(pd.DataFrame({MODEL: name, FPR: fpr, TPR: tpr, AUC: auc(fpr, tpr)}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
fig = go.Figure()

# Random classifier baseline
fig.add_trace(
    go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines", name="Random Classifier", line={"color": MUTED, "width": 2, "dash": "dash"}
    )
)

for i, (model, rows) in enumerate(df.groupby(MODEL, sort=False)):
    area = rows[AUC].iloc[0]
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    fig.add_trace(
        go.Scatter(
            x=rows[FPR],
            y=rows[TPR],
            mode="lines",
            name=f"{model} (AUC = {area:.2f})",
            line={"color": color, "width": 3},
            fill="tozeroy" if i == 0 else None,
            fillcolor="rgba(0, 158, 115, 0.15)" if i == 0 else None,
        )
    )

fig.update_layout(
    autosize=False,
    width=600,
    height=600,
    title={
        "text": "roc-curve · python · plotly · anyplot.ai",
        "font": {"size": 17, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": FPR, "font": {"size": 14, "color": INK}},
        "tickfont": {"size": 12, "color": INK_SOFT},
        "range": [0, 1],
        "dtick": 0.2,
        "gridcolor": GRID,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "constrain": "domain",
    },
    yaxis={
        "title": {"text": TPR, "font": {"size": 14, "color": INK}},
        "tickfont": {"size": 12, "color": INK_SOFT},
        "range": [0, 1],
        "dtick": 0.2,
        "gridcolor": GRID,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "scaleanchor": "x",
        "scaleratio": 1,
        "constrain": "domain",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend={
        "x": 0.97,
        "y": 0.03,
        "xanchor": "right",
        "yanchor": "bottom",
        "font": {"size": 11, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 70, "r": 30, "t": 60, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
