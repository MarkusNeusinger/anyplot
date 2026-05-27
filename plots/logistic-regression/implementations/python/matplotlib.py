""" anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os
import sys


sys.path = [p for p in sys.path if "implementations" not in p]  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import accuracy_score  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is brand green)
BRAND = "#009E73"
SECONDARY = "#C475FD"

# Data - Credit risk scoring: probability of loan approval based on credit score
np.random.seed(42)
n_points = 200

# Generate credit scores (300-850 range, typical credit score range)
credit_scores = np.concatenate([np.random.normal(550, 80, n_points // 2), np.random.normal(700, 60, n_points // 2)])
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
p = y_probs
se = np.sqrt(p * (1 - p) / n_points) * 2
ci_lower = np.clip(y_probs - 1.96 * se, 0, 1)
ci_upper = np.clip(y_probs + 1.96 * se, 0, 1)

# Calculate accuracy
y_pred = model.predict(X)
accuracy = accuracy_score(y, y_pred)

# Jitter y values for visibility
y_jittered = y + np.random.uniform(-0.03, 0.03, n_points)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Confidence interval band
ax.fill_between(x_curve, ci_lower, ci_upper, alpha=0.25, color=BRAND, label="95% CI")

# Logistic curve
ax.plot(x_curve, y_probs, color=BRAND, linewidth=3.5, label="Logistic Fit", zorder=3)

# Decision threshold line
ax.axhline(y=0.5, color=INK_SOFT, linestyle="--", linewidth=2, label="Decision Threshold (0.5)")

# Data points - class 0 (rejected)
mask_0 = y == 0
ax.scatter(
    credit_scores[mask_0],
    y_jittered[mask_0],
    s=120,
    alpha=0.6,
    color=SECONDARY,
    label="Rejected (0)",
    edgecolors=PAGE_BG,
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
    color=BRAND,
    label="Approved (1)",
    edgecolors=PAGE_BG,
    linewidth=0.5,
    zorder=2,
)

# Model annotation with theme-adaptive styling
coef = model.coef_[0][0]
intercept = model.intercept_[0]
annotation_text = f"Accuracy: {accuracy:.1%}\nCoef: {coef:.4f}\nIntercept: {intercept:.2f}"
ax.annotate(
    annotation_text,
    xy=(0.03, 0.97),
    xycoords="axes fraction",
    fontsize=14,
    color=INK,
    verticalalignment="top",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": ELEVATED_BG, "alpha": 0.9, "edgecolor": INK_SOFT},
)

# Labels and styling
ax.set_xlabel("Credit Score", fontsize=20, color=INK)
ax.set_ylabel("Probability of Approval", fontsize=20, color=INK)
ax.set_title("logistic-regression · python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xlim(300, 850)
ax.set_ylim(-0.08, 1.08)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid styling
ax.grid(True, alpha=0.15, linestyle="-", linewidth=0.8, color=INK_SOFT)
ax.set_axisbelow(True)

# Legend styling
leg = ax.legend(fontsize=16, loc="lower right")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
