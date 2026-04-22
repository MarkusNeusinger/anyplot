""" pyplots.ai
roc-curve: ROC Curve with AUC
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


# Data - simulate binary classification predictions
np.random.seed(42)

# Generate predictions from a "good" model (AUC ~0.89)
n_samples = 500
y_true = np.concatenate([np.zeros(250), np.ones(250)])
y_scores_good = np.concatenate(
    [
        np.random.beta(2, 5, 250),  # Negative class - lower scores
        np.random.beta(5, 2, 250),  # Positive class - higher scores
    ]
)

# Generate predictions from a "moderate" model (AUC ~0.75)
y_scores_moderate = np.concatenate([np.random.beta(2, 3, 250), np.random.beta(3, 2, 250)])


# Calculate ROC curves manually
def calculate_roc(y_true, y_scores):
    thresholds = np.linspace(0, 1, 200)
    tpr_list = []
    fpr_list = []
    for thresh in thresholds:
        y_pred = (y_scores >= thresh).astype(int)
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        tn = np.sum((y_pred == 0) & (y_true == 0))
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        tpr_list.append(tpr)
        fpr_list.append(fpr)
    return np.array(fpr_list), np.array(tpr_list)


# Calculate AUC using trapezoidal rule
def calculate_auc(fpr, tpr):
    sorted_indices = np.argsort(fpr)
    fpr_sorted = fpr[sorted_indices]
    tpr_sorted = tpr[sorted_indices]
    return np.trapezoid(tpr_sorted, fpr_sorted)


fpr_good, tpr_good = calculate_roc(y_true, y_scores_good)
auc_good = calculate_auc(fpr_good, tpr_good)

fpr_moderate, tpr_moderate = calculate_roc(y_true, y_scores_moderate)
auc_moderate = calculate_auc(fpr_moderate, tpr_moderate)

# Create plot
fig = go.Figure()

# Random classifier diagonal reference line
fig.add_trace(
    go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode="lines",
        name="Random Classifier",
        line={"color": "#888888", "width": 3, "dash": "dash"},
        showlegend=True,
    )
)

# Good model ROC curve
fig.add_trace(
    go.Scatter(
        x=fpr_good,
        y=tpr_good,
        mode="lines",
        name=f"Logistic Regression (AUC = {auc_good:.2f})",
        line={"color": "#306998", "width": 4},
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.15)",
    )
)

# Moderate model ROC curve
fig.add_trace(
    go.Scatter(
        x=fpr_moderate,
        y=tpr_moderate,
        mode="lines",
        name=f"Decision Tree (AUC = {auc_moderate:.2f})",
        line={"color": "#FFD43B", "width": 4},
    )
)

# Layout
fig.update_layout(
    title={
        "text": "roc-curve · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "False Positive Rate", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "range": [0, 1],
        "dtick": 0.2,
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.1)",
        "gridwidth": 1,
        "zeroline": False,
        "constrain": "domain",
    },
    yaxis={
        "title": {"text": "True Positive Rate", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "range": [0, 1],
        "dtick": 0.2,
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.1)",
        "gridwidth": 1,
        "zeroline": False,
        "scaleanchor": "x",
        "scaleratio": 1,
        "constrain": "domain",
    },
    template="plotly_white",
    legend={
        "x": 0.98,
        "y": 0.02,
        "xanchor": "right",
        "yanchor": "bottom",
        "font": {"size": 18},
        "bgcolor": "rgba(255, 255, 255, 0.9)",
        "bordercolor": "rgba(0, 0, 0, 0.2)",
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 80, "t": 100, "b": 100},
    plot_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
