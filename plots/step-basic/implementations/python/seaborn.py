""" pyplots.ai
step-basic: Basic Step Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Monthly cumulative sales figures
np.random.seed(42)
months = np.arange(1, 13)
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Realistic cumulative sales pattern with seasonal growth
monthly_sales = np.array([45, 52, 68, 75, 82, 95, 88, 92, 105, 115, 130, 155])
cumulative_sales = np.cumsum(monthly_sales)

df = pd.DataFrame({"Month": months, "Month Name": month_names, "Cumulative Sales ($K)": cumulative_sales})

# Plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))

# Step plot using matplotlib's step function with seaborn styling
ax.step(df["Month"], df["Cumulative Sales ($K)"], where="post", linewidth=3, color="#306998", label="Cumulative Sales")

# Add markers at data points
ax.scatter(df["Month"], df["Cumulative Sales ($K)"], s=150, color="#FFD43B", edgecolor="#306998", linewidth=2, zorder=5)

# Style
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Cumulative Sales ($K)", fontsize=20)
ax.set_title("step-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xticks(months)
ax.set_xticklabels(month_names)
ax.grid(True, alpha=0.3, linestyle="--")

# Set y-axis to start from 0 for cumulative data
ax.set_ylim(0, ax.get_ylim()[1] * 1.05)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
