""" pyplots.ai
count-basic: Basic Count Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Survey responses with varying frequencies
np.random.seed(42)
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
# Generate realistic survey data with different frequencies
weights = [0.15, 0.35, 0.25, 0.18, 0.07]
responses = np.random.choice(categories, size=200, p=weights)

# Count occurrences
unique, counts = np.unique(responses, return_counts=True)

# Sort by frequency (descending)
sort_idx = np.argsort(counts)[::-1]
unique = unique[sort_idx]
counts = counts[sort_idx]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
bars = ax.bar(unique, counts, color="#306998", edgecolor="#1e4a6e", linewidth=2, width=0.7)

# Add count labels on top of bars
for bar, count in zip(bars, counts, strict=True):
    ax.annotate(
        f"{count}",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=18,
        fontweight="bold",
        color="#306998",
    )

# Styling
ax.set_xlabel("Survey Response", fontsize=20)
ax.set_ylabel("Count", fontsize=20)
ax.set_title("count-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Adjust y-axis to give room for labels
ax.set_ylim(0, max(counts) * 1.15)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
