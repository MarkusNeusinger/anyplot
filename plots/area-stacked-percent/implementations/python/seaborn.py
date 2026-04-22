""" pyplots.ai
area-stacked-percent: 100% Stacked Area Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch


# Data: Market share evolution of renewable energy sources
np.random.seed(42)
years = np.arange(2015, 2025)

# Generate synthetic data that shows interesting transitions
solar = np.array([10, 12, 15, 18, 22, 26, 30, 35, 40, 45])
wind = np.array([20, 22, 24, 26, 28, 30, 32, 33, 34, 35])
hydro = np.array([50, 48, 45, 42, 38, 34, 30, 27, 23, 18])
other = np.array([20, 18, 16, 14, 12, 10, 8, 5, 3, 2])

# Create DataFrame and normalize to 100%
df_wide = pd.DataFrame({"Year": years, "Solar": solar, "Wind": wind, "Hydro": hydro, "Other": other})

# Calculate percentages (normalize to 100%)
total = df_wide[["Solar", "Wind", "Hydro", "Other"]].sum(axis=1)
for col in ["Solar", "Wind", "Hydro", "Other"]:
    df_wide[col] = df_wide[col] / total * 100

# Calculate cumulative values for stacking
df_wide["Other_top"] = df_wide["Other"]
df_wide["Hydro_top"] = df_wide["Other"] + df_wide["Hydro"]
df_wide["Wind_top"] = df_wide["Other"] + df_wide["Hydro"] + df_wide["Wind"]
df_wide["Solar_top"] = 100  # Always 100%

# Bottom positions
df_wide["Other_bottom"] = 0
df_wide["Hydro_bottom"] = df_wide["Other"]
df_wide["Wind_bottom"] = df_wide["Other"] + df_wide["Hydro"]
df_wide["Solar_bottom"] = df_wide["Other"] + df_wide["Hydro"] + df_wide["Wind"]

# Prepare data for seaborn - long format with boundaries
categories = ["Other", "Hydro", "Wind", "Solar"]
colors = {"Other": "#95A5A6", "Hydro": "#4ECDC4", "Wind": "#FFD43B", "Solar": "#306998"}

# Set seaborn style
sns.set_theme(style="whitegrid")
sns.set_context("talk", font_scale=1.1)

# Create plot (4800x2700 at 300 dpi)
fig, ax = plt.subplots(figsize=(16, 9))

# Use fill_between for stacked areas (with seaborn styling)
for cat in categories:
    ax.fill_between(
        df_wide["Year"],
        df_wide[f"{cat}_bottom"],
        df_wide[f"{cat}_top"],
        label=cat,
        color=colors[cat],
        alpha=0.85,
        linewidth=0,
    )

# Add subtle lines at boundaries using seaborn lineplot for library usage
df_long = df_wide.melt(
    id_vars=["Year"], value_vars=["Other_top", "Hydro_top", "Wind_top"], var_name="Boundary", value_name="Percentage"
)

sns.lineplot(
    data=df_long,
    x="Year",
    y="Percentage",
    hue="Boundary",
    palette=["#7f8c8d", "#3bb3a3", "#e6c135"],
    linewidth=1.5,
    legend=False,
    ax=ax,
)

# Style the plot
ax.set_xlabel("Year", fontsize=20)
ax.set_ylabel("Share (%)", fontsize=20)
ax.set_title("area-stacked-percent · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set y-axis to 0-100%
ax.set_ylim(0, 100)
ax.set_xlim(2015, 2024)

# Customize grid
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.grid(False, axis="x")

# Create custom legend with proper order (bottom to top in stack)
legend_elements = [
    Patch(facecolor=colors["Solar"], alpha=0.85, label="Solar"),
    Patch(facecolor=colors["Wind"], alpha=0.85, label="Wind"),
    Patch(facecolor=colors["Hydro"], alpha=0.85, label="Hydro"),
    Patch(facecolor=colors["Other"], alpha=0.85, label="Other"),
]
ax.legend(handles=legend_elements, loc="upper left", fontsize=14, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
