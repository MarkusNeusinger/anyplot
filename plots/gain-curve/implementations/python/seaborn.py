""" pyplots.ai
gain-curve: Cumulative Gains Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seed for reproducibility
np.random.seed(42)

# Generate synthetic classification data (customer churn scenario)
# y_true: actual churn (1) or not (0)
# y_score: model's predicted probability of churn
n_samples = 1000

# Create synthetic true labels with ~30% positive class (churners)
y_true = np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3])

# Create correlated prediction scores (simulating a reasonably good model)
# Higher scores for true positives, lower for true negatives, with noise
noise = np.random.normal(0, 0.15, n_samples)
y_score = np.clip(0.3 + 0.4 * y_true + noise, 0, 1)

# Calculate cumulative gains curve
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

total_positives = np.sum(y_true)
cum_positives = np.cumsum(y_true_sorted)
gains = cum_positives / total_positives * 100

# Population percentage (x-axis)
population_pct = np.arange(1, len(y_true) + 1) / len(y_true) * 100

# Add origin point for complete curve
population_pct = np.insert(population_pct, 0, 0)
gains = np.insert(gains, 0, 0)

# Calculate perfect model curve
positive_rate = total_positives / len(y_true) * 100
perfect_gains = np.minimum(population_pct / positive_rate * 100, 100)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot model gain curve using seaborn
sns.lineplot(x=population_pct, y=gains, ax=ax, color="#306998", linewidth=3.5, label="Churn Prediction Model")

# Plot random baseline (diagonal)
sns.lineplot(
    x=[0, 100], y=[0, 100], ax=ax, color="#888888", linewidth=2.5, linestyle="--", label="Random Selection (Baseline)"
)

# Plot perfect model curve
sns.lineplot(
    x=population_pct, y=perfect_gains, ax=ax, color="#FFD43B", linewidth=2.5, linestyle=":", label="Perfect Model"
)

# Fill area between model and baseline to show model lift
ax.fill_between(
    population_pct,
    gains,
    population_pct,  # baseline is y = x
    alpha=0.2,
    color="#306998",
)

# Styling
ax.set_xlabel("Customers Targeted (%)", fontsize=20)
ax.set_ylabel("Churners Captured (%)", fontsize=20)
ax.set_title("gain-curve · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits
ax.set_xlim(0, 100)
ax.set_ylim(0, 105)

# Legend
ax.legend(fontsize=16, loc="lower right")

# Grid styling
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
