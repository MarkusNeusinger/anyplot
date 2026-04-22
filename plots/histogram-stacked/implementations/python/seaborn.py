""" pyplots.ai
histogram-stacked: Stacked Histogram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Response times (ms) from three different server regions
np.random.seed(42)

# Generate response times for three server regions with different characteristics
region_a = np.random.normal(loc=45, scale=12, size=150)  # US East - faster
region_b = np.random.normal(loc=60, scale=15, size=180)  # Europe - medium
region_c = np.random.normal(loc=75, scale=18, size=120)  # Asia Pacific - slower

# Combine into DataFrame
df = pd.DataFrame(
    {
        "Response Time (ms)": np.concatenate([region_a, region_b, region_c]),
        "Region": (["US East"] * len(region_a) + ["Europe"] * len(region_b) + ["Asia Pacific"] * len(region_c)),
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Stacked histogram using histplot with multiple='stack'
sns.histplot(
    data=df,
    x="Response Time (ms)",
    hue="Region",
    hue_order=["US East", "Europe", "Asia Pacific"],
    multiple="stack",
    bins=20,
    palette=["#306998", "#FFD43B", "#4DAF4A"],
    edgecolor="white",
    linewidth=0.8,
    alpha=0.9,
    ax=ax,
)

# Styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Frequency", fontsize=20)
ax.set_title("histogram-stacked · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Adjust legend styling
legend = ax.get_legend()
legend.set_title("Server Region")
legend.get_title().set_fontsize(16)
for text in legend.get_texts():
    text.set_fontsize(14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
