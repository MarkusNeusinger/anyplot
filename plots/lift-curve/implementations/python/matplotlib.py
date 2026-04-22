""" pyplots.ai
lift-curve: Model Lift Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-27
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Simulate realistic customer response model predictions
np.random.seed(42)
n_samples = 1000
base_rate = 0.15  # 15% baseline response rate

# Generate true labels with base rate
y_true = np.random.binomial(1, base_rate, n_samples)

# Generate model scores - correlated with true outcomes for realistic model
# Good responders get higher scores, non-responders get lower scores
y_score = np.where(
    y_true == 1,
    np.clip(np.random.beta(5, 2, n_samples), 0, 1),  # Responders: higher scores
    np.clip(np.random.beta(2, 5, n_samples), 0, 1),  # Non-responders: lower scores
)

# Calculate lift curve
# Sort by predicted score (descending)
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative response rate and lift
n_total = len(y_true)
n_positive = y_true.sum()
baseline_rate = n_positive / n_total

# Calculate cumulative lift at each percentage
percentages = np.arange(1, 101)
lift_values = []

for pct in percentages:
    n_selected = int(np.ceil(n_total * pct / 100))
    n_responders = y_true_sorted[:n_selected].sum()
    response_rate = n_responders / n_selected
    lift = response_rate / baseline_rate
    lift_values.append(lift)

lift_values = np.array(lift_values)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot lift curve
ax.plot(percentages, lift_values, color="#306998", linewidth=3, label="Model Lift", zorder=3)

# Reference line at y=1 (random selection)
ax.axhline(y=1, color="#FFD43B", linestyle="--", linewidth=2.5, label="Random (Lift = 1)", zorder=2)

# Add markers at key deciles
decile_pcts = [10, 20, 30, 40, 50]
for pct in decile_pcts:
    idx = pct - 1
    ax.scatter(pct, lift_values[idx], color="#306998", s=150, zorder=4, edgecolors="white", linewidth=2)
    ax.annotate(
        f"{lift_values[idx]:.2f}x",
        (pct, lift_values[idx]),
        xytext=(0, 15),
        textcoords="offset points",
        ha="center",
        fontsize=14,
        fontweight="bold",
        color="#306998",
    )

# Fill area under curve for visual emphasis
ax.fill_between(percentages, 1, lift_values, where=(lift_values > 1), alpha=0.15, color="#306998", zorder=1)

# Styling
ax.set_xlabel("Population Targeted (%)", fontsize=20)
ax.set_ylabel("Cumulative Lift", fontsize=20)
ax.set_title("lift-curve · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits
ax.set_xlim(0, 100)
ax.set_ylim(0, max(lift_values) * 1.15)

# Grid
ax.grid(True, alpha=0.3, linestyle="--", zorder=0)

# Legend
ax.legend(fontsize=16, loc="upper right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
