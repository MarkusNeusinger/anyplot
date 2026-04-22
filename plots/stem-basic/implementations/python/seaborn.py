""" pyplots.ai
stem-basic: Basic Stem Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Discrete signal samples (damped sinusoidal impulse response)
np.random.seed(42)
n_samples = 30
x = np.arange(n_samples)
y = np.exp(-0.1 * x) * np.sin(0.5 * x) * 2.5

# Create DataFrame for seaborn
df = pd.DataFrame({"Sample Index": x, "Amplitude": y})

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Draw stems (thin vertical lines from baseline y=0 to data values)
ax.vlines(x=df["Sample Index"], ymin=0, ymax=df["Amplitude"], color="#306998", linewidth=2.5, alpha=0.8)

# Draw markers at top of stems using seaborn
sns.scatterplot(
    data=df, x="Sample Index", y="Amplitude", s=300, color="#FFD43B", edgecolor="#306998", linewidth=2, ax=ax, zorder=3
)

# Draw baseline at y=0
ax.axhline(y=0, color="#306998", linewidth=1.5, alpha=0.5)

# Styling
ax.set_xlabel("Sample Index (n)", fontsize=20)
ax.set_ylabel("Amplitude", fontsize=20)
ax.set_title("stem-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
