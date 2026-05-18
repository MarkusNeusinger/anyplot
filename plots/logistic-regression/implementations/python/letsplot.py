"""anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-01-09
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave
from sklearn.linear_model import LogisticRegression


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first two colors for binary classification)
OKABE_ITO = ["#009E73", "#D55E00"]

# Data - Generate binary classification data with clear sigmoidal relationship
np.random.seed(42)
n_samples = 200

# Feature: Study hours (0 to 10 hours)
x = np.random.uniform(0, 10, n_samples)

# True probability follows a logistic function
true_prob = 1 / (1 + np.exp(-1.5 * (x - 5)))

# Binary outcome (pass/fail exam based on study hours)
y = (np.random.random(n_samples) < true_prob).astype(int)

# Fit logistic regression model using sklearn
X_reshaped = x.reshape(-1, 1)
model = LogisticRegression()
model.fit(X_reshaped, y)

# Get model parameters for annotation
coef = model.coef_[0][0]
intercept = model.intercept_[0]
accuracy = model.score(X_reshaped, y)

# Generate smooth curve for prediction
x_line = np.linspace(0, 10, 200)
X_line = x_line.reshape(-1, 1)
y_prob = model.predict_proba(X_line)[:, 1]

# Calculate confidence intervals using approximate standard error
se = np.sqrt(y_prob * (1 - y_prob) / n_samples) * 2
ci_lower = np.clip(y_prob - 1.96 * se, 0, 1)
ci_upper = np.clip(y_prob + 1.96 * se, 0, 1)

# Add jitter to y values for visibility
y_jittered = y + np.random.normal(0, 0.03, n_samples)
y_jittered = np.clip(y_jittered, -0.1, 1.1)

# Create DataFrames
df_points = pd.DataFrame(
    {"Study Hours": x, "Probability": y_jittered, "Class": ["Pass" if yi == 1 else "Fail" for yi in y]}
)

df_curve = pd.DataFrame({"Study Hours": x_line, "Probability": y_prob})

df_ci = pd.DataFrame({"Study Hours": x_line, "ci_lower": ci_lower, "ci_upper": ci_upper})

# Create plot with theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
)

plot = (
    ggplot()
    # Confidence interval ribbon
    + geom_ribbon(aes(x="Study Hours", ymin="ci_lower", ymax="ci_upper"), data=df_ci, fill=OKABE_ITO[0], alpha=0.15)
    # Logistic curve
    + geom_line(aes(x="Study Hours", y="Probability"), data=df_curve, color=OKABE_ITO[0], size=2.5)
    # Decision threshold line
    + geom_hline(yintercept=0.5, linetype="dashed", color=INK_SOFT, size=1, alpha=0.6)
    # Data points with jitter
    + geom_point(aes(x="Study Hours", y="Probability", color="Class"), data=df_points, size=5, alpha=0.65)
    # Colors for classes using Okabe-Ito
    + scale_color_manual(values=OKABE_ITO)
    # Labels with model annotation
    + labs(
        x="Study Hours",
        y="Probability",
        title="logistic-regression · python · letsplot · anyplot.ai",
        color="Class",
        subtitle=f"Coefficient: {coef:.2f} | Accuracy: {accuracy:.1%}",
    )
    # Y-axis from 0 to 1
    + scale_y_continuous(limits=[-0.1, 1.1])
    # Theme and size
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save as PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images subfolder to current directory
if os.path.exists("lets-plot-images"):
    for filename in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
        src = os.path.join("lets-plot-images", filename)
        if os.path.exists(src):
            shutil.move(src, filename)
