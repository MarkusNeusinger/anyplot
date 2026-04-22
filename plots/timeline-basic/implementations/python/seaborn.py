""" pyplots.ai
timeline-basic: Event Timeline
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Software project milestones (reduced count to avoid overlap)
events = [
    ("2024-01-15", "Project Kickoff", "Planning"),
    ("2024-02-20", "Requirements Done", "Planning"),
    ("2024-04-01", "Architecture Design", "Design"),
    ("2024-05-15", "UI Mockups", "Design"),
    ("2024-07-01", "Backend MVP", "Development"),
    ("2024-08-15", "Frontend MVP", "Development"),
    ("2024-10-01", "Alpha Release", "Testing"),
    ("2024-11-15", "Beta Testing", "Testing"),
    ("2025-01-10", "Go Live", "Deployment"),
]

df = pd.DataFrame(events, columns=["date", "event", "category"])
df["date"] = pd.to_datetime(df["date"])

# Create y-offset for alternating labels (above/below axis)
df["y_offset"] = [1 if i % 2 == 0 else -1 for i in range(len(df))]

# Define category colors using Python Blue and Yellow as primary
category_order = ["Planning", "Design", "Development", "Testing", "Deployment"]
palette = {
    "Planning": "#306998",
    "Design": "#FFD43B",
    "Development": "#2ca02c",
    "Testing": "#d62728",
    "Deployment": "#9467bd",
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw the main timeline axis
ax.axhline(y=0, color="#888888", linewidth=3, zorder=1)

# Plot events using seaborn scatterplot
sns.scatterplot(
    data=df,
    x="date",
    y=[0] * len(df),
    hue="category",
    hue_order=category_order,
    palette=palette,
    s=500,
    zorder=3,
    ax=ax,
    legend=True,
    edgecolor="white",
    linewidth=2,
)

# Add vertical connector lines and event labels
for _idx, row in df.iterrows():
    y_end = row["y_offset"] * 0.55

    # Connector line
    ax.plot([row["date"], row["date"]], [0, y_end], color=palette[row["category"]], linewidth=2.5, zorder=2)

    # Event label
    va = "bottom" if row["y_offset"] > 0 else "top"
    ax.annotate(
        row["event"],
        xy=(row["date"], y_end),
        ha="center",
        va=va,
        fontsize=15,
        fontweight="bold",
        color="#333333",
        xytext=(0, 10 * row["y_offset"]),
        textcoords="offset points",
    )

# Style the plot - extra padding on right for "Production Launch" label
ax.set_xlim(df["date"].min() - pd.Timedelta(days=40), df["date"].max() + pd.Timedelta(days=60))
ax.set_ylim(-1.1, 1.1)

# Remove y-axis and spines for clean timeline look
ax.set_yticks([])
ax.set_ylabel("")
ax.set_xlabel("")
ax.spines["left"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["bottom"].set_visible(False)

# Format x-axis with quarterly ticks for clarity
ax.tick_params(axis="x", labelsize=16, length=0)
ax.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(interval=2))
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b %Y"))
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

# Title and legend
ax.set_title("timeline-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Place legend at bottom center, horizontal layout
ax.legend(
    title="Phase",
    title_fontsize=16,
    fontsize=14,
    loc="lower center",
    ncol=5,
    framealpha=0.9,
    edgecolor="#cccccc",
    bbox_to_anchor=(0.5, -0.15),
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
