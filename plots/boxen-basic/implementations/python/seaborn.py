""" pyplots.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Server response times by endpoint (realistic scenario for large datasets)
np.random.seed(42)

# Create large dataset with different distributions per endpoint
endpoints = ["API Gateway", "Auth Service", "Data Query", "File Upload"]
n_per_group = 5000

data = []
for endpoint in endpoints:
    if endpoint == "API Gateway":
        # Fast with occasional spikes
        values = np.concatenate(
            [
                np.random.exponential(scale=50, size=int(n_per_group * 0.9)),
                np.random.uniform(200, 500, size=int(n_per_group * 0.1)),
            ]
        )
    elif endpoint == "Auth Service":
        # Consistent, low latency
        values = np.random.normal(loc=80, scale=15, size=n_per_group)
    elif endpoint == "Data Query":
        # Bimodal - cached vs uncached
        values = np.concatenate(
            [
                np.random.normal(loc=30, scale=10, size=int(n_per_group * 0.6)),
                np.random.normal(loc=150, scale=30, size=int(n_per_group * 0.4)),
            ]
        )
    else:  # File Upload
        # Right-skewed with heavy tail (file size dependent)
        values = np.random.lognormal(mean=4.5, sigma=0.8, size=n_per_group)

    # Ensure positive values
    values = np.clip(values, 1, None)
    data.extend([(endpoint, v) for v in values])

df = pd.DataFrame(data, columns=["Endpoint", "Response Time (ms)"])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.boxenplot(
    data=df,
    x="Endpoint",
    y="Response Time (ms)",
    hue="Endpoint",
    palette=["#306998", "#FFD43B", "#4B8BBE", "#646464"],
    legend=False,
    width=0.7,
    linewidth=1.5,
    ax=ax,
)

# Styling
ax.set_title("boxen-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Endpoint", fontsize=20)
ax.set_ylabel("Response Time (ms)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
