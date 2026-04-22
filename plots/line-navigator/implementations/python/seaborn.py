""" pyplots.ai
line-navigator: Line Chart with Mini Navigator
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Generate 3 years of daily sensor readings
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=1095, freq="D")  # 3 years of daily data

# Create realistic sensor data with trend, seasonality, and noise
trend = np.linspace(50, 70, 1095)  # gradual upward trend
seasonality = 10 * np.sin(2 * np.pi * np.arange(1095) / 365)  # yearly cycle
noise = np.random.randn(1095) * 3
values = trend + seasonality + noise

df = pd.DataFrame({"date": dates, "value": values})

# Define the selected range for the detail view (approximately 5 months in the middle)
start_idx = 400
end_idx = 550
selected_start = dates[start_idx]
selected_end = dates[end_idx]

# Create figure with GridSpec for precise control
fig = plt.figure(figsize=(16, 9))
gs = fig.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.15)
ax_main = fig.add_subplot(gs[0])
ax_nav = fig.add_subplot(gs[1])

# Style
line_color = "#306998"  # Python blue
selection_color = "#FFD43B"  # Python yellow
bg_color = "#E6E6E6"

# Main chart - detail view (selected range only)
df_selected = df[(df["date"] >= selected_start) & (df["date"] <= selected_end)]
sns.lineplot(data=df_selected, x="date", y="value", ax=ax_main, linewidth=2.5, color=line_color)
ax_main.set_xlabel("")
ax_main.set_ylabel("Sensor Reading (units)", fontsize=20)
ax_main.set_title("line-navigator · seaborn · pyplots.ai", fontsize=24)
ax_main.tick_params(axis="both", labelsize=16)
ax_main.grid(True, alpha=0.3, linestyle="--")

# Add date range label
date_range_text = f"Selected Range: {selected_start.strftime('%Y-%m-%d')} to {selected_end.strftime('%Y-%m-%d')}"
ax_main.text(
    0.98,
    0.98,
    date_range_text,
    transform=ax_main.transAxes,
    fontsize=14,
    verticalalignment="top",
    horizontalalignment="right",
    bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8, "edgecolor": "gray"},
)

# Navigator chart - full data with selection highlight
sns.lineplot(data=df, x="date", y="value", ax=ax_nav, linewidth=1.5, color=line_color, alpha=0.7)

# Shade areas outside selection (grayed out)
ax_nav.axvspan(dates[0], selected_start, color=bg_color, alpha=0.6, zorder=1)
ax_nav.axvspan(selected_end, dates[-1], color=bg_color, alpha=0.6, zorder=1)

# Highlight selection window with yellow border
selection_rect = mpatches.Rectangle(
    (selected_start, ax_nav.get_ylim()[0]),
    selected_end - selected_start,
    ax_nav.get_ylim()[1] - ax_nav.get_ylim()[0],
    linewidth=3,
    edgecolor=selection_color,
    facecolor="none",
    zorder=3,
)
ax_nav.add_patch(selection_rect)

# Draw vertical lines at selection edges (resize handles)
for edge_date in [selected_start, selected_end]:
    ax_nav.axvline(x=edge_date, color=selection_color, linewidth=3, zorder=4)

ax_nav.set_xlabel("Date", fontsize=18)
ax_nav.set_ylabel("")
ax_nav.tick_params(axis="both", labelsize=12)
ax_nav.set_yticks([])  # Hide y-axis ticks for cleaner navigator

# Remove spines from navigator for cleaner look
ax_nav.spines["top"].set_visible(False)
ax_nav.spines["right"].set_visible(False)
ax_nav.spines["left"].set_visible(False)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
