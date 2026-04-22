# ruff: noqa: F405
"""pyplots.ai
logistic-regression: Logistic Regression Curve Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()


# Simple logistic regression using gradient descent
def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -500, 500)))


def fit_logistic(X, y, lr=0.1, n_iter=1000):
    """Fit logistic regression using gradient descent."""
    n = len(X)
    # Add intercept term
    X_b = np.column_stack([np.ones(n), X])
    # Initialize weights
    w = np.zeros(2)
    for _ in range(n_iter):
        z = X_b @ w
        p = sigmoid(z)
        gradient = X_b.T @ (p - y) / n
        w -= lr * gradient
    return w[0], w[1]  # intercept, coefficient


# Data - Generate binary classification data with clear sigmoidal relationship
np.random.seed(42)
n_samples = 200

# Feature: Study hours (0 to 10 hours)
x = np.random.uniform(0, 10, n_samples)

# True probability follows a logistic function
true_prob = 1 / (1 + np.exp(-1.5 * (x - 5)))

# Binary outcome (pass/fail exam based on study hours)
y = (np.random.random(n_samples) < true_prob).astype(int)

# Fit logistic regression model
intercept, coef = fit_logistic(x, y)

# Generate smooth curve for prediction
x_line = np.linspace(0, 10, 200)
y_prob = sigmoid(intercept + coef * x_line)

# Calculate confidence intervals using approximate standard error
se = np.sqrt(y_prob * (1 - y_prob) / n_samples) * 2
ci_lower = np.clip(y_prob - 1.96 * se, 0, 1)
ci_upper = np.clip(y_prob + 1.96 * se, 0, 1)

# Add jitter to y values for visibility
y_jittered = y + np.random.normal(0, 0.03, n_samples)
y_jittered = np.clip(y_jittered, -0.1, 1.1)

# Create DataFrames
df_points = pd.DataFrame(
    {"Study Hours": x, "Outcome": y_jittered, "Class": ["Pass" if yi == 1 else "Fail" for yi in y]}
)

df_curve = pd.DataFrame({"Study Hours": x_line, "Probability": y_prob})

df_ci = pd.DataFrame({"Study Hours": x_line, "ci_lower": ci_lower, "ci_upper": ci_upper})

# Decision threshold line
df_threshold = pd.DataFrame({"y": [0.5]})

# Create plot
plot = (
    ggplot()
    # Confidence interval ribbon
    + geom_ribbon(aes(x="Study Hours", ymin="ci_lower", ymax="ci_upper"), data=df_ci, fill="#306998", alpha=0.2)
    # Logistic curve
    + geom_line(aes(x="Study Hours", y="Probability"), data=df_curve, color="#306998", size=2.5)
    # Decision threshold line
    + geom_hline(yintercept=0.5, linetype="dashed", color="#666666", size=1.5)
    # Data points with jitter
    + geom_point(aes(x="Study Hours", y="Outcome", color="Class"), data=df_points, size=4, alpha=0.6)
    # Colors for classes
    + scale_color_manual(values=["#DC2626", "#FFD43B"])
    # Labels
    + labs(x="Study Hours", y="Probability", title="logistic-regression · letsplot · pyplots.ai", color="Outcome")
    # Y-axis from 0 to 1
    + scale_y_continuous(limits=[0, 1])
    # Theme
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
    )
    # Size for 4800x2700 at scale=3
    + ggsize(1600, 900)
)

# Save as PNG and HTML in current directory
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
