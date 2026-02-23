""" pyplots.ai
density-basic: Basic Density Plot
Library: seaborn 0.13.2 | Python 3.14
Quality: /100 | Updated: 2026-02-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - bimodal distribution of test scores
np.random.seed(42)
test_scores = np.concatenate(
    [
        np.random.normal(68, 8, 280),  # Main group centered at 68
        np.random.normal(90, 4, 120),  # High achievers group
    ]
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.kdeplot(data=test_scores, ax=ax, fill=True, alpha=0.6, color="#306998", linewidth=3)
sns.rugplot(data=test_scores, ax=ax, color="#306998", alpha=0.3, height=0.03)

# Style
ax.set_xlabel("Test Score (points)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("density-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
