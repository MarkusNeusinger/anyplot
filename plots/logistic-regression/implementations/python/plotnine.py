""" pyplots.ai
logistic-regression: Logistic Regression Curve Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from plotnine import (
    aes,
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

# Create plot
plot = (
    ggplot()
    # Confidence interval ribbon
    + geom_ribbon(data=df_curve, mapping=aes(x="score", ymin="lower", ymax="upper"), alpha=0.25, fill="#306998")
    # Fitted logistic curve
    + geom_line(data=df_curve, mapping=aes(x="score", y="probability"), color="#306998", size=2)
    # Decision threshold line at p=0.5
    + geom_hline(yintercept=0.5, linetype="dashed", color="#666666", size=1)
    # Data points with jitter
    + geom_point(
        data=df_points,
        mapping=aes(x="score", y="outcome", color="class"),
        size=4,
        alpha=0.6,
        position=position_jitter(width=0, height=0.03),
    )
    # Colors
    + scale_color_manual(values={"Fail": "#E74C3C", "Pass": "#27AE60"})
    # Labels
    + labs(
        title="logistic-regression · plotnine · pyplots.ai", x="Exam Score", y="Probability of Passing", color="Outcome"
    )
    # Theme with scaled fonts for 4800x2700 canvas
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
    )
)

# Save
plot.save("plot.png", dpi=300)
