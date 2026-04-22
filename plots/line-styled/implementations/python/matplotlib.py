""" pyplots.ai
line-styled: Styled Line Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - CPU performance benchmarks over time
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Simulated performance scores for different processors
base_score = 100
processor_a = base_score + np.cumsum(np.random.randn(12) * 3 + 2)  # Steady improvement
processor_b = base_score + np.cumsum(np.random.randn(12) * 4 + 1.5)  # Variable improvement
processor_c = base_score + np.cumsum(np.random.randn(12) * 2 + 2.5)  # Faster improvement
processor_d = base_score + np.cumsum(np.random.randn(12) * 3 + 0.5)  # Slower improvement

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot lines with different styles
ax.plot(months, processor_a, linestyle="-", linewidth=3, color="#306998", label="Processor A", marker="o", markersize=8)
ax.plot(
    months, processor_b, linestyle="--", linewidth=3, color="#FFD43B", label="Processor B", marker="s", markersize=8
)
ax.plot(months, processor_c, linestyle=":", linewidth=3, color="#4B8BBE", label="Processor C", marker="^", markersize=8)
ax.plot(
    months, processor_d, linestyle="-.", linewidth=3, color="#646464", label="Processor D", marker="D", markersize=8
)

# Labels and styling
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Performance Score", fontsize=20)
ax.set_title("line-styled · matplotlib · pyplots.ai", fontsize=24)
ax.set_xticks(months)
ax.set_xticklabels(month_labels)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
