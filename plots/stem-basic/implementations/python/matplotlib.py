""" pyplots.ai
stem-basic: Basic Stem Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Discrete signal samples (simulating a damped oscillation)
np.random.seed(42)
x = np.arange(0, 30)
y = np.exp(-x / 10) * np.cos(x * 0.8) + np.random.randn(30) * 0.05

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Stem plot with custom styling
markerline, stemlines, baseline = ax.stem(x, y, basefmt="k-")
plt.setp(stemlines, linewidth=2, color="#306998", alpha=0.8)
plt.setp(markerline, markersize=12, color="#306998", markeredgecolor="white", markeredgewidth=2)
plt.setp(baseline, linewidth=2, color="#333333")

# Labels and styling (scaled font sizes for 4800x2700)
ax.set_xlabel("Sample Index", fontsize=20)
ax.set_ylabel("Amplitude", fontsize=20)
ax.set_title("stem-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
