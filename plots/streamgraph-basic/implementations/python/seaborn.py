""" pyplots.ai
streamgraph-basic: Basic Stream Graph
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn theme for consistent styling
sns.set_theme(style="whitegrid", context="talk", font_scale=1.2)

# Data - Monthly streaming hours by music genre over 2 years
np.random.seed(42)

months = pd.date_range("2023-01", periods=24, freq="ME")
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Classical", "Jazz"]

# Generate realistic streaming data with seasonal patterns
data = {}
for i, genre in enumerate(genres):
    base = [40, 35, 50, 30, 15, 12][i]
    trend = np.linspace(0, [10, -5, 15, 8, 2, 5][i], 24)
    seasonal = 5 * np.sin(np.linspace(0, 4 * np.pi, 24) + i)
    noise = np.random.randn(24) * 3
    data[genre] = np.maximum(base + trend + seasonal + noise, 5)

df = pd.DataFrame(data, index=months)

# Create long-form data for seaborn
df_long = df.reset_index().melt(id_vars="index", var_name="Genre", value_name="Hours")
df_long.rename(columns={"index": "Month"}, inplace=True)

# Pivot to wide format for stackplot calculation
df_pivot = df_long.pivot(index="Month", columns="Genre", values="Hours")
df_pivot = df_pivot[genres]  # Ensure consistent order

# Create stacked values for streamgraph (centered baseline)
values = df_pivot.values
cumsum = np.cumsum(values, axis=1)
total = cumsum[:, -1]
baseline = -total / 2  # Center around x-axis

# Create upper and lower bounds for each genre
lowers = np.column_stack([baseline + cumsum[:, i] - values[:, i] for i in range(len(genres))])
uppers = np.column_stack([baseline + cumsum[:, i] for i in range(len(genres))])

# Create figure using seaborn-styled matplotlib
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn color palette - Python colors first, then colorblind-safe
palette = ["#306998", "#FFD43B"] + sns.color_palette("colorblind", n_colors=4).as_hex()

# Fill between for each genre layer
for i in range(len(genres)):
    ax.fill_between(
        df_pivot.index,
        lowers[:, i],
        uppers[:, i],
        label=genres[i],
        color=palette[i],
        alpha=0.85,
        edgecolor="white",
        linewidth=0.5,
    )

# Styling with seaborn aesthetics
ax.set_xlabel("Month", fontsize=20)
ax.set_title("streamgraph-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Remove y-axis ticks (streamgraph focuses on relative proportions)
ax.set_yticks([])
ax.set_ylabel("")

# Format x-axis dates
ax.set_xlim(df_pivot.index[0], df_pivot.index[-1])
fig.autofmt_xdate(rotation=45)

# Legend using seaborn styling
ax.legend(loc="upper left", fontsize=14, framealpha=0.9, title="Genre", title_fontsize=16)

# Use seaborn's despine for cleaner look
sns.despine(ax=ax, left=True, bottom=False)

# Subtle grid on x-axis only
ax.grid(True, axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
