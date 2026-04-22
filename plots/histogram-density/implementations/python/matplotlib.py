""" pyplots.ai
histogram-density: Density Histogram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-29
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Generate realistic test score data with a normal distribution
np.random.seed(42)
test_scores = np.random.normal(loc=75, scale=12, size=500)
# Clip to realistic score range
test_scores = np.clip(test_scores, 0, 100)

# Create theoretical normal PDF for overlay (using numpy)
mu, sigma = 75, 12
x_pdf = np.linspace(30, 110, 200)
pdf = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_pdf - mu) / sigma) ** 2)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Density histogram (density=True normalizes so area = 1)
ax.hist(
    test_scores,
    bins=25,
    density=True,
    alpha=0.7,
    color="#306998",
    edgecolor="white",
    linewidth=1.5,
    label="Observed Distribution",
)

# Overlay theoretical normal PDF
ax.plot(x_pdf, pdf, color="#FFD43B", linewidth=3, label="Normal PDF (μ=75, σ=12)")

# Labels and styling
ax.set_xlabel("Test Score (points)", fontsize=20)
ax.set_ylabel("Probability Density", fontsize=20)
ax.set_title("histogram-density · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits for clean display
ax.set_xlim(30, 110)
ax.set_ylim(0, None)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
