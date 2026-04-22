""" pyplots.ai
ridgeline-basic: Basic Ridgeline Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Monthly temperature distributions (realistic seasonal pattern)
np.random.seed(42)

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Base temperatures (Celsius) with realistic seasonal variation
base_temps = [2, 4, 8, 13, 17, 21, 24, 23, 19, 13, 7, 3]

# Generate temperature data with variation for each month
data = []
for month, base_temp in zip(months, base_temps, strict=True):
    temps = np.random.normal(base_temp, 3.5, 150)
    for temp in temps:
        data.append({"month": month, "temperature": temp})

df = pd.DataFrame(data)

# Create figure with seaborn FacetGrid for ridgeline effect
sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})

# Initialize the FacetGrid with reversed month order (January at top)
g = sns.FacetGrid(
    df,
    row="month",
    hue="month",
    aspect=15,
    height=0.6,
    palette=sns.color_palette("coolwarm", n_colors=12),
    row_order=months[::-1],
    hue_order=months[::-1],
)

# Draw the densities
g.map(sns.kdeplot, "temperature", bw_adjust=0.8, clip_on=False, fill=True, alpha=0.8, linewidth=2.5)

# Add outline for each ridge
g.map(sns.kdeplot, "temperature", bw_adjust=0.8, clip_on=False, color="w", linewidth=3)

# Add horizontal line at y=0
g.map(plt.axhline, y=0, linewidth=2.5, linestyle="-", color="w", clip_on=False)


# Define label function for row names
def label(x, color, label):
    ax = plt.gca()
    ax.text(
        -0.02, 0.2, label, fontsize=20, fontweight="bold", color=color, ha="right", va="center", transform=ax.transAxes
    )


g.map(label, "temperature")

# Adjust overlap between ridges
g.figure.subplots_adjust(hspace=-0.5)

# Remove axes details
g.set_titles("")
g.set(yticks=[], ylabel="")
g.despine(bottom=True, left=True)

# Add x-axis label and title
g.axes[-1, 0].set_xlabel("Temperature (°C)", fontsize=22)
g.axes[-1, 0].tick_params(axis="x", labelsize=18)

# Add title at the top
g.figure.suptitle("ridgeline-basic · seaborn · pyplots.ai", fontsize=26, y=0.98, fontweight="bold")

# Set figure size for 4800x2700 output
g.figure.set_size_inches(16, 9)

plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
