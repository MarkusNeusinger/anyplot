""" pyplots.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Simulating monthly product sales with marketing events
np.random.seed(42)

# Create 12 months of sales data
dates = pd.date_range("2024-01-01", periods=365, freq="D")
# Base trend with seasonality and noise
trend = np.linspace(100, 180, 365)
seasonality = 15 * np.sin(np.linspace(0, 4 * np.pi, 365))
noise = np.random.normal(0, 8, 365)
sales = trend + seasonality + noise

df = pd.DataFrame({"date": dates, "sales": sales})

# Events - Key marketing milestones
events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(["2024-02-14", "2024-05-01", "2024-07-15", "2024-09-20", "2024-11-25"]),
        "event_label": ["Valentine's Campaign", "Spring Sale", "Summer Launch", "Fall Promotion", "Black Friday"],
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Main line plot using seaborn
sns.lineplot(data=df, x="date", y="sales", ax=ax, linewidth=2.5, color="#306998")

# Add event markers with alternating heights for readability
y_positions = [0.85, 0.75, 0.85, 0.75, 0.85]  # Alternating label positions
colors_events = ["#FFD43B"] * len(events)  # Use Python Yellow for all events

for i, (_, event) in enumerate(events.iterrows()):
    # Vertical line at event date
    ax.axvline(x=event["event_date"], color=colors_events[i], linestyle="--", linewidth=2, alpha=0.8)

    # Event label with background
    y_pos = ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * y_positions[i]
    ax.annotate(
        event["event_label"],
        xy=(event["event_date"], y_pos),
        fontsize=14,
        fontweight="bold",
        color="#333333",
        ha="center",
        va="bottom",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#FFD43B", "edgecolor": "none", "alpha": 0.9},
        rotation=0,
    )

    # Small marker on the line at event date
    event_sales = df.loc[df["date"] == event["event_date"], "sales"]
    if not event_sales.empty:
        ax.scatter(
            event["event_date"],
            event_sales.values[0],
            color="#FFD43B",
            s=150,
            zorder=5,
            edgecolor="#333333",
            linewidth=2,
        )

# Styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Daily Sales (Units)", fontsize=20)
ax.set_title("line-annotated-events · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
