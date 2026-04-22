""" pyplots.ai
line-basic: Basic Line Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Monthly temperature readings over a year
np.random.seed(42)
months = np.arange(1, 13)
# Realistic temperature pattern (warmer in summer, cooler in winter)
base_temp = 15 + 12 * np.sin((months - 4) * np.pi / 6)
temperature = base_temp + np.random.randn(12) * 2

df = pd.DataFrame({"Month": months, "Temperature (°C)": temperature})

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
sns.lineplot(data=df, x="Month", y="Temperature (°C)", ax=ax, linewidth=3, color="#306998", marker="o", markersize=12)

# Style
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("line-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xticks(months)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
