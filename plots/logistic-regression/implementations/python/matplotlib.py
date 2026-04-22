""" pyplots.ai
logistic-regression: Logistic Regression Curve Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


# Data - Credit risk scoring example: probability of loan approval based on credit score
np.random.seed(42)
n_points = 200

# Generate credit scores (300-850 range, typical credit score range)
credit_scores = np.concatenate(
    [
        np.random.normal(550, 80, n_points // 2),  # Lower scores (more rejections)
        np.random.normal(700, 60, n_points // 2),  # Higher scores (more approvals)
    ]
)
credit_scores = np.clip(credit_scores, 300, 850)

# Generate binary outcomes with logistic probability
true_probs = 1 / (1 + np.exp(-0.02 * (credit_scores - 620)))
y = (np.random.random(n_points) < true_probs).astype(int)

# Fit logistic regression model
X = credit_scores.reshape(-1, 1)
model = LogisticRegression()
model.fit(X, y)

# Generate smooth curve for predictions
x_curve = np.linspace(300, 850, 300)
y_probs = model.predict_proba(x_curve.reshape(-1, 1))[:, 1]

# Calculate confidence intervals (using standard error approximation)
# SE for logistic regression at each point
p = y_probs
se = np.sqrt(p * (1 - p) / n_points) * 2  # Approximate SE
ci_lower = np.clip(y_probs - 1.96 * se, 0, 1)
ci_upper = np.clip(y_probs + 1.96 * se, 0, 1)

# Calculate accuracy
y_pred = model.predict(X)
accuracy = accuracy_score(y, y_pred)

# Jitter y values for visibility
y_jittered = y + np.random.uniform(-0.03, 0.03, n_points)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Confidence interval band
ax.fill_between(x_curve, ci_lower, ci_upper, alpha=0.25, color="#306998", label="95% CI")

# Logistic curve
ax.plot(x_curve, y_probs, color="#306998", linewidth=3.5, label="Logistic Fit", zorder=3)

# Decision threshold line
ax.axhline(y=0.5, color="#888888", linestyle="--", linewidth=2, label="Decision Threshold (0.5)")

# Data points - class 0 (rejected)
mask_0 = y == 0
ax.scatter(
    credit_scores[mask_0],
    y_jittered[mask_0],
    s=120,
    alpha=0.6,
    color="#E74C3C",
    label="Rejected (0)",
    edgecolors="white",
    linewidth=0.5,
    zorder=2,
)

# Data points - class 1 (approved)
mask_1 = y == 1
ax.scatter(
    credit_scores[mask_1],
    y_jittered[mask_1],
    s=120,
    alpha=0.6,
    color="#FFD43B",
    label="Approved (1)",
    edgecolors="#666666",
    linewidth=0.5,
    zorder=2,
)

# Model annotation
coef = model.coef_[0][0]
intercept = model.intercept_[0]
annotation_text = f"Accuracy: {accuracy:.1%}\nCoef: {coef:.4f}\nIntercept: {intercept:.2f}"
ax.annotate(
    annotation_text,
    xy=(0.03, 0.97),
    xycoords="axes fraction",
    fontsize=14,
    verticalalignment="top",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "alpha": 0.8, "edgecolor": "#cccccc"},
)

# Labels and styling
ax.set_xlabel("Credit Score", fontsize=20)
ax.set_ylabel("Probability of Approval", fontsize=20)
ax.set_title("logistic-regression · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(300, 850)
ax.set_ylim(-0.08, 1.08)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.legend(fontsize=14, loc="lower right", framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
