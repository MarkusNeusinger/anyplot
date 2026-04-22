""" pyplots.ai
precision-recall: Precision-Recall Curve
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go
from sklearn.metrics import average_precision_score, precision_recall_curve


# Data - Simulate a binary classification scenario (fraud detection)
np.random.seed(42)
n_samples = 1000

# Imbalanced dataset: 10% positive class (fraud cases)
y_true = np.zeros(n_samples, dtype=int)
y_true[:100] = 1
np.random.shuffle(y_true)

# Generate prediction scores - good classifier with some noise
y_scores = np.where(
    y_true == 1,
    np.random.beta(5, 2, n_samples),  # Higher scores for positive class
    np.random.beta(2, 5, n_samples),  # Lower scores for negative class
)

# Calculate precision-recall curve
precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
average_precision = average_precision_score(y_true, y_scores)

# Calculate baseline (random classifier performance)
positive_class_ratio = np.mean(y_true)

# Create figure
fig = go.Figure()

# Add precision-recall curve (stepped style for accuracy)
fig.add_trace(
    go.Scatter(
        x=recall,
        y=precision,
        mode="lines",
        name=f"Classifier (AP = {average_precision:.3f})",
        line={"color": "#306998", "width": 4, "shape": "hv"},
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.15)",
    )
)

# Add baseline reference line (random classifier)
fig.add_trace(
    go.Scatter(
        x=[0, 1],
        y=[positive_class_ratio, positive_class_ratio],
        mode="lines",
        name=f"Random Baseline ({positive_class_ratio:.2f})",
        line={"color": "#FFD43B", "width": 3, "dash": "dash"},
    )
)

# Add iso-F1 curves
f1_values = [0.2, 0.4, 0.6, 0.8]
for f1 in f1_values:
    # Iso-F1: precision = f1 * recall / (2 * recall - f1) for valid recall range
    x_iso = np.linspace(f1 / 2 + 0.01, 1, 100)  # Start above f1/2 to avoid division issues
    y_iso = f1 * x_iso / (2 * x_iso - f1)
    # Only keep valid values within [0, 1] range
    mask = (y_iso > 0) & (y_iso <= 1)
    fig.add_trace(
        go.Scatter(
            x=x_iso[mask],
            y=y_iso[mask],
            mode="lines",
            name=f"F1 = {f1}",
            line={"color": "gray", "width": 1.5, "dash": "dot"},
            opacity=0.5,
            showlegend=True if f1 == 0.2 else False,
            legendgroup="iso-f1",
        )
    )

# Update layout for 4800x2700 px
fig.update_layout(
    title={"text": "precision-recall · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Recall (Sensitivity)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "range": [0, 1.02],
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.1)",
        "gridwidth": 1,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Precision (Positive Predictive Value)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "range": [0, 1.05],
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.1)",
        "gridwidth": 1,
        "zeroline": False,
    },
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.02,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": "rgba(255, 255, 255, 0.9)",
        "bordercolor": "rgba(0, 0, 0, 0.3)",
        "borderwidth": 1,
    },
    template="plotly_white",
    margin={"l": 100, "r": 60, "t": 100, "b": 100},
)

# Add annotation for iso-F1 curves
fig.add_annotation(
    x=0.92, y=0.92, text="Iso-F1 curves", font={"size": 16, "color": "gray"}, showarrow=False, xanchor="right"
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
