""" pyplots.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Monthly sales with recession period and target threshold
np.random.seed(42)
months = pd.date_range(start="2006-01", periods=60, freq="ME")
base_trend = np.linspace(100, 150, 60)
# Dip during recession period (2008-2009)
recession_effect = np.where((months >= "2008-01") & (months <= "2009-12"), -30 * np.sin(np.linspace(0, np.pi, 60)), 0)
sales = base_trend + recession_effect + np.random.randn(60) * 8

df = pd.DataFrame({"Month": months, "Sales": sales})

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Vertical span - recession period (2008-2009)
ax.axvspan(
    pd.Timestamp("2008-01-01"),
    pd.Timestamp("2009-12-31"),
    alpha=0.25,
    color="#306998",
    label="Recession Period (2008-2009)",
)

# Horizontal span - target sales zone (120-140)
ax.axhspan(120, 140, alpha=0.2, color="#FFD43B", label="Target Zone (120-140)")

# Line plot using seaborn
sns.lineplot(data=df, x="Month", y="Sales", ax=ax, linewidth=3, color="#306998")

# Styling
ax.set_title("span-basic · seaborn · pyplots.ai", fontsize=24)
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Sales (thousands $)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
