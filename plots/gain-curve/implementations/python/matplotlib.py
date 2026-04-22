""" pyplots.ai
gain-curve: Cumulative Gains Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-29
"""

import matplotlib.pyplot as plt
import numpy as np


# Generate synthetic classification data (customer response model)
np.random.seed(42)
n_samples = 1000

# Create customer features that influence response
customer_value = np.random.randn(n_samples)
customer_engagement = np.random.randn(n_samples)

# True underlying probability (strong signal)
latent_score = 1.5 * customer_value + 1.0 * customer_engagement
true_prob = 1 / (1 + np.exp(-latent_score))
y_true = (np.random.rand(n_samples) < true_prob).astype(int)

# Model predicted probabilities (captures signal well with some noise)
# A good model that shows clear lift over random
y_score = 1 / (1 + np.exp(-(latent_score + np.random.randn(n_samples) * 0.5)))

# Calculate cumulative gains curve
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Cumulative gains: percentage of population vs percentage of positives captured
total_positives = np.sum(y_true)
cumulative_positives = np.cumsum(y_true_sorted)
gains = cumulative_positives / total_positives * 100

# Percentage of population targeted
n_samples = len(y_true)
population_percentage = np.arange(1, n_samples + 1) / n_samples * 100

# Add origin point (0, 0) for proper plotting
population_percentage = np.insert(population_percentage, 0, 0)
gains = np.insert(gains, 0, 0)

# Create perfect model curve (captures all positives immediately)
positive_rate = total_positives / n_samples * 100
perfect_x = np.array([0, positive_rate, 100])
perfect_y = np.array([0, 100, 100])

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot model gains curve
ax.plot(population_percentage, gains, color="#306998", linewidth=3, label="Model", zorder=3)

# Plot random baseline (diagonal)
ax.plot([0, 100], [0, 100], color="#888888", linewidth=2, linestyle="--", label="Random (Baseline)", zorder=2)

# Plot perfect model
ax.plot(perfect_x, perfect_y, color="#FFD43B", linewidth=2, linestyle=":", label="Perfect Model", zorder=2)

# Fill area between model and random baseline
ax.fill_between(population_percentage, gains, population_percentage, alpha=0.2, color="#306998", zorder=1)

# Styling
ax.set_xlabel("Population Targeted (%)", fontsize=20)
ax.set_ylabel("Positive Cases Captured (%)", fontsize=20)
ax.set_title("gain-curve · matplotlib · pyplots.ai", fontsize=24)

ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_aspect("equal")

ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="lower right")

# Add annotation showing key insight
# Find where 20% of population is targeted
idx_20 = np.searchsorted(population_percentage, 20)
gain_at_20 = gains[idx_20]
ax.annotate(
    f"Top 20% captures {gain_at_20:.0f}%\nof positive cases",
    xy=(20, gain_at_20),
    xytext=(35, gain_at_20 - 15),
    fontsize=14,
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 2},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#306998", "alpha": 0.9},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
