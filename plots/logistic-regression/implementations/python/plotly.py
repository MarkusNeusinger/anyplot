""" pyplots.ai
logistic-regression: Logistic Regression Curve Plot
Library: plotly 6.5.1 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LogisticRegression


# Data - exam study hours vs pass/fail
np.random.seed(42)
n_samples = 150

# Generate study hours (predictor)
study_hours = np.concatenate(
    [
        np.random.normal(3, 1.5, n_samples // 2),  # Students who failed
        np.random.normal(7, 1.5, n_samples // 2),  # Students who passed
    ]
)
study_hours = np.clip(study_hours, 0, 12)

# Binary outcome (0=fail, 1=pass)
y = np.array([0] * (n_samples // 2) + [1] * (n_samples // 2))

# Shuffle data
shuffle_idx = np.random.permutation(len(study_hours))
study_hours = study_hours[shuffle_idx]
y = y[shuffle_idx]

# Fit logistic regression
X = study_hours.reshape(-1, 1)
model = LogisticRegression()
model.fit(X, y)

# Generate smooth curve for predictions
x_curve = np.linspace(0, 12, 200)
y_proba = model.predict_proba(x_curve.reshape(-1, 1))[:, 1]

# Calculate confidence intervals (approximate using standard error)
# SE = sqrt(p(1-p)/n) for binomial proportion
se = np.sqrt(y_proba * (1 - y_proba) / n_samples) * 1.96
y_upper = np.clip(y_proba + se, 0, 1)
y_lower = np.clip(y_proba - se, 0, 1)

# Jitter y values for visibility
y_jittered = y + np.random.uniform(-0.03, 0.03, len(y))

# Model accuracy
accuracy = model.score(X, y)

# Create figure
fig = go.Figure()

# Confidence interval band
fig.add_trace(
    go.Scatter(
        x=np.concatenate([x_curve, x_curve[::-1]]),
        y=np.concatenate([y_upper, y_lower[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.2)",
        line={"color": "rgba(0,0,0,0)"},
        name="95% CI",
        showlegend=True,
        hoverinfo="skip",
    )
)

# Logistic regression curve
fig.add_trace(
    go.Scatter(x=x_curve, y=y_proba, mode="lines", line={"color": "#306998", "width": 4}, name="Logistic Curve")
)

# Decision threshold line at 0.5
fig.add_trace(
    go.Scatter(
        x=[0, 12],
        y=[0.5, 0.5],
        mode="lines",
        line={"color": "#888888", "width": 2, "dash": "dash"},
        name="Decision Threshold (0.5)",
    )
)

# Data points - Class 0 (Failed)
mask_0 = y == 0
fig.add_trace(
    go.Scatter(
        x=study_hours[mask_0],
        y=y_jittered[mask_0],
        mode="markers",
        marker={"size": 14, "color": "#306998", "opacity": 0.6, "line": {"width": 1, "color": "white"}},
        name="Failed (0)",
    )
)

# Data points - Class 1 (Passed)
mask_1 = y == 1
fig.add_trace(
    go.Scatter(
        x=study_hours[mask_1],
        y=y_jittered[mask_1],
        mode="markers",
        marker={"size": 14, "color": "#FFD43B", "opacity": 0.6, "line": {"width": 1, "color": "#333333"}},
        name="Passed (1)",
    )
)

# Layout
fig.update_layout(
    title={"text": "logistic-regression · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Study Hours", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "range": [-0.5, 12.5],
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Probability of Passing", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "range": [-0.08, 1.08],
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    template="plotly_white",
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "rgba(0,0,0,0.2)",
        "borderwidth": 1,
    },
    annotations=[
        {
            "x": 10.5,
            "y": 0.15,
            "text": f"Accuracy: {accuracy:.1%}",
            "showarrow": False,
            "font": {"size": 20, "color": "#306998"},
            "bgcolor": "rgba(255,255,255,0.8)",
            "bordercolor": "#306998",
            "borderwidth": 1,
            "borderpad": 6,
        }
    ],
    margin={"l": 80, "r": 60, "t": 100, "b": 80},
)

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
