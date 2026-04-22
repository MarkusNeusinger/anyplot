""" pyplots.ai
count-basic: Basic Count Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Survey responses about preferred programming languages
np.random.seed(42)
languages = ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "Ruby"]

# Generate realistic survey data with varying frequencies
weights = [0.28, 0.22, 0.15, 0.10, 0.08, 0.07, 0.06, 0.04]
n_responses = 500
responses = np.random.choice(languages, size=n_responses, p=weights)

df = pd.DataFrame({"language": responses})

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Count plot with seaborn - sorted by frequency (descending)
order = df["language"].value_counts().index.tolist()
sns.countplot(data=df, x="language", order=order, color="#306998", ax=ax)

# Add count labels on top of bars
for container in ax.containers:
    ax.bar_label(container, fontsize=16, padding=5)

# Styling for large canvas (4800x2700 px at 300 dpi)
ax.set_xlabel("Programming Language", fontsize=20)
ax.set_ylabel("Number of Responses", fontsize=20)
ax.set_title("count-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Subtle grid
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
