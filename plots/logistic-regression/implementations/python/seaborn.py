""" pyplots.ai
logistic-regression: Logistic Regression Curve Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.special import expit
from sklearn.linear_model import LogisticRegression


# Data
np.random.seed(42)
n_samples = 200

# Generate data with clear logistic relationship
x = np.random.uniform(-3, 3, n_samples)
# True probability follows sigmoid
true_prob = expit(1.5 * x + 0.5)
y = (np.random.random(n_samples) < true_prob).astype(int)

# Fit logistic regression
X_train = x.reshape(-1, 1)
model = LogisticRegression()
model.fit(X_train, y)

# Create smooth curve for prediction
x_curve = np.linspace(-3.5, 3.5, 300)
X_curve = x_curve.reshape(-1, 1)
prob_curve = model.predict_proba(X_curve)[:, 1]

# Calculate confidence interval using bootstrap
n_bootstrap = 100
bootstrap_probs = np.zeros((n_bootstrap, len(x_curve)))
for i in range(n_bootstrap):
    idx = np.random.choice(n_samples, n_samples, replace=True)
    X_boot = x[idx].reshape(-1, 1)
    y_boot = y[idx]
    model_boot = LogisticRegression()
    model_boot.fit(X_boot, y_boot)
    bootstrap_probs[i] = model_boot.predict_proba(X_curve)[:, 1]

ci_lower = np.percentile(bootstrap_probs, 2.5, axis=0)
ci_upper = np.percentile(bootstrap_probs, 97.5, axis=0)

# Jitter y values for visibility
y_jittered = y + np.random.uniform(-0.05, 0.05, n_samples)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Confidence interval
ax.fill_between(x_curve, ci_lower, ci_upper, alpha=0.25, color="#306998", label="95% CI")

# Logistic curve
ax.plot(x_curve, prob_curve, color="#306998", linewidth=3, label="Logistic Curve", zorder=5)

# Data points with distinct colors for each class
sns.scatterplot(
    x=x, y=y_jittered, hue=y, palette={0: "#FFD43B", 1: "#306998"}, s=150, alpha=0.6, ax=ax, legend=False, zorder=4
)

# Decision threshold line
ax.axhline(y=0.5, color="#888888", linestyle="--", linewidth=2, label="Decision Threshold (p=0.5)")

# Create custom legend handles
legend_elements = [
    Line2D([0], [0], color="#306998", linewidth=3, label="Logistic Curve"),
    Patch(facecolor="#306998", alpha=0.25, label="95% CI"),
    Line2D([0], [0], color="#888888", linestyle="--", linewidth=2, label="Decision Threshold (p=0.5)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#FFD43B", markersize=12, label="Class 0"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#306998", markersize=12, label="Class 1"),
]
ax.legend(handles=legend_elements, fontsize=16, loc="upper left", framealpha=0.9)

# Model info annotation
accuracy = model.score(X_train, y)
coef = model.coef_[0][0]
intercept = model.intercept_[0]
ax.annotate(
    f"Accuracy: {accuracy:.1%}\nCoef: {coef:.2f}, Intercept: {intercept:.2f}",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    fontsize=14,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
)

# Styling
ax.set_xlabel("Predictor Variable (X)", fontsize=20)
ax.set_ylabel("Probability", fontsize=20)
ax.set_title("logistic-regression · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_ylim(-0.1, 1.1)
ax.set_xlim(-3.5, 3.5)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
