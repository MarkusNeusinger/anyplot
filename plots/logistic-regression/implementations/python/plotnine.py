"""anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_ribbon,
    ggplot,
    labs,
    position_jitter,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
FAIL_COLOR = "#D55E00"  # Okabe-Ito position 2
PASS_COLOR = "#009E73"  # Okabe-Ito position 1
CURVE_COLOR = "#0072B2"  # Okabe-Ito position 3

# Data - Exam score vs Pass/Fail outcome
np.random.seed(42)
n_samples = 150

# Generate exam scores with different distributions for pass/fail
scores_fail = np.random.normal(45, 12, 60)  # Lower scores tend to fail
scores_pass = np.random.normal(70, 10, 90)  # Higher scores tend to pass
scores = np.concatenate([scores_fail, scores_pass])
outcomes = np.concatenate([np.zeros(60), np.ones(90)])

# Add some noise to outcomes for realism
flip_indices = np.random.choice(n_samples, size=15, replace=False)
outcomes[flip_indices] = 1 - outcomes[flip_indices]

# Clip scores to reasonable range
scores = np.clip(scores, 20, 100)

# Fit logistic regression using statsmodels
X = sm.add_constant(scores)
model = sm.Logit(outcomes, X).fit(disp=0)

# Create smooth curve for predictions with confidence intervals
x_curve = np.linspace(20, 100, 200)
X_curve = sm.add_constant(x_curve)
predictions = model.get_prediction(X_curve)
y_pred = predictions.predicted
conf_int = predictions.conf_int(alpha=0.05)
y_lower = conf_int[:, 0]
y_upper = conf_int[:, 1]

# Create dataframes
df_points = pd.DataFrame(
    {"score": scores, "outcome": outcomes, "class": ["Fail" if o == 0 else "Pass" for o in outcomes]}
)

df_curve = pd.DataFrame({"score": x_curve, "probability": y_pred, "lower": y_lower, "upper": y_upper})

# Theme
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.08),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.04),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=24, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
)

# Create plot
plot = (
    ggplot()
    # Confidence interval ribbon
    + geom_ribbon(data=df_curve, mapping=aes(x="score", ymin="lower", ymax="upper"), alpha=0.25, fill=CURVE_COLOR)
    # Fitted logistic curve
    + geom_line(data=df_curve, mapping=aes(x="score", y="probability"), color=CURVE_COLOR, size=2)
    # Decision threshold line at p=0.5
    + geom_hline(yintercept=0.5, linetype="dashed", color=INK_SOFT, size=1, alpha=0.6)
    # Data points with jitter
    + geom_point(
        data=df_points,
        mapping=aes(x="score", y="outcome", color="class"),
        size=4,
        alpha=0.6,
        position=position_jitter(width=0, height=0.03),
    )
    # Colors
    + scale_color_manual(values={"Fail": FAIL_COLOR, "Pass": PASS_COLOR})
    # Labels
    + labs(
        title="logistic-regression · python · plotnine · anyplot.ai",
        x="Exam Score (points)",
        y="Probability of Passing",
        color="Outcome",
    )
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
