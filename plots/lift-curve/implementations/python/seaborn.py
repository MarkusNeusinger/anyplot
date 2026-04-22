""" pyplots.ai
lift-curve: Model Lift Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn style
sns.set_theme(style="whitegrid")

# Data - simulate customer response prediction for marketing campaign
np.random.seed(42)
n_samples = 1000
base_response_rate = 0.10  # 10% overall response rate

# Create a model with good predictive power
# True propensity is a latent variable
latent_propensity = np.random.normal(0, 1, n_samples)

# Model score approximates the latent propensity with some noise
y_score = latent_propensity + np.random.normal(0, 0.3, n_samples)
y_score = (y_score - y_score.min()) / (y_score.max() - y_score.min())  # Normalize to 0-1

# Actual responses based on latent propensity (strong correlation)
response_threshold = np.percentile(latent_propensity, 100 * (1 - base_response_rate))
y_true = (latent_propensity >= response_threshold).astype(int)

# Calculate lift curve data
# Sort by predicted scores descending
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative gains
n_positives = y_true.sum()
cumulative_positives = np.cumsum(y_true_sorted)
population_percentages = np.arange(1, n_samples + 1) / n_samples * 100

# Calculate lift: (cumulative positive rate) / (overall positive rate)
cumulative_positive_rate = cumulative_positives / np.arange(1, n_samples + 1)
baseline_rate = n_positives / n_samples
lift = cumulative_positive_rate / baseline_rate

# Create dataframe for seaborn
df = pd.DataFrame({"Population Targeted (%)": population_percentages, "Cumulative Lift": lift})

# Create plot (16:9 landscape format - 4800x2700 at 300 dpi)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot lift curve using seaborn lineplot
sns.lineplot(
    data=df,
    x="Population Targeted (%)",
    y="Cumulative Lift",
    ax=ax,
    color="#306998",  # Python Blue
    linewidth=3,
    label="Model Lift",
)

# Add baseline reference line (random selection = lift of 1)
ax.axhline(y=1, color="#FFD43B", linestyle="--", linewidth=2.5, label="Random (No Lift)", zorder=3)

# Add decile markers
decile_indices = [int(n_samples * p / 100) - 1 for p in [10, 20, 30, 40, 50]]
for idx in decile_indices:
    pct = population_percentages[idx]
    lift_val = lift[idx]
    ax.plot(pct, lift_val, "o", color="#306998", markersize=12, zorder=5)
    ax.annotate(
        f"{lift_val:.2f}x",
        (pct, lift_val),
        textcoords="offset points",
        xytext=(0, 15),
        ha="center",
        fontsize=14,
        fontweight="bold",
        color="#306998",
    )

# Styling
ax.set_xlabel("Population Targeted (%)", fontsize=20)
ax.set_ylabel("Cumulative Lift", fontsize=20)
ax.set_title("lift-curve · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)

# Configure grid
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits
ax.set_xlim(0, 100)
ax.set_ylim(0, max(lift) * 1.15)

# Legend
ax.legend(fontsize=16, loc="upper right")

# Tight layout
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
