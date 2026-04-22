""" pyplots.ai
histogram-kde: Histogram with KDE Overlay
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data: Simulated daily stock returns (%)
np.random.seed(42)
# Mix of normal returns with occasional larger movements
returns = np.concatenate(
    [
        np.random.normal(0.05, 1.2, 400),  # Regular trading days
        np.random.normal(-0.5, 2.5, 80),  # Volatile periods
        np.random.normal(0.8, 0.8, 20),  # Bullish days
    ]
)
np.random.shuffle(returns)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot histogram
sns.histplot(
    returns, bins=40, kde=False, stat="density", alpha=0.5, color="#306998", edgecolor="white", linewidth=0.8, ax=ax
)

# Plot KDE overlay separately for better color control
sns.kdeplot(returns, color="#FFD43B", linewidth=4, ax=ax)

# Styling
ax.set_xlabel("Daily Return (%)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("histogram-kde · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Clean up spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
