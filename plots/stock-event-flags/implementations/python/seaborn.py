""" pyplots.ai
stock-event-flags: Stock Chart with Event Flags
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Generate stock price data
np.random.seed(42)
n_days = 180
dates = pd.date_range("2025-01-02", periods=n_days, freq="B")

# Create realistic stock price movement
returns = np.random.normal(0.0005, 0.018, n_days)
price = 150 * np.cumprod(1 + returns)
close = price

# Create DataFrame
df = pd.DataFrame({"date": dates, "close": close})

# Define events with different types
events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(
            [
                "2025-01-28",
                "2025-02-14",
                "2025-03-15",
                "2025-04-22",
                "2025-05-08",
                "2025-05-28",
                "2025-06-18",
                "2025-07-24",
            ]
        ),
        "event_type": ["earnings", "dividend", "news", "earnings", "split", "dividend", "news", "earnings"],
        "event_label": [
            "Q4 Earnings",
            "Div $0.50",
            "Product Launch",
            "Q1 Earnings",
            "2:1 Split",
            "Div $0.55",
            "Partnership",
            "Q2 Earnings",
        ],
    }
)

# Event type styling
event_colors = {
    "earnings": "#306998",  # Python Blue - earnings reports
    "dividend": "#2E8B57",  # Sea Green - dividends
    "split": "#9932CC",  # Purple - stock splits
    "news": "#FF8C00",  # Dark Orange - news events
}

event_markers = {
    "earnings": "s",  # square for earnings
    "dividend": "D",  # diamond for dividends
    "split": "^",  # triangle up for splits
    "news": "o",  # circle for news
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Plot stock price line
sns.lineplot(data=df, x="date", y="close", ax=ax, color="#306998", linewidth=2.5, label="Stock Price")

# Get price range for flag positioning
price_min, price_max = df["close"].min(), df["close"].max()
price_range = price_max - price_min
flag_offset_base = price_range * 0.12

# Plot events with flags
for idx, (_, event) in enumerate(events.iterrows()):
    event_date = event["event_date"]
    event_type = event["event_type"]
    event_label = event["event_label"]

    # Find closest date in our data
    closest_idx = np.abs(df["date"] - event_date).argmin()
    actual_date = df["date"].iloc[closest_idx]
    price_at_event = df["close"].iloc[closest_idx]

    # Alternate flag position above/below with varying heights to avoid overlap
    if idx % 2 == 0:
        flag_y = price_at_event + flag_offset_base * (1 + (idx % 3) * 0.3)
        va = "bottom"
    else:
        flag_y = price_at_event - flag_offset_base * (1 + (idx % 3) * 0.3)
        va = "top"

    color = event_colors[event_type]
    marker = event_markers[event_type]

    # Draw vertical dashed line from price to flag
    ax.plot([actual_date, actual_date], [price_at_event, flag_y], color=color, linestyle="--", linewidth=1.5, alpha=0.7)

    # Draw flag marker at event position on price line
    ax.scatter(
        [actual_date], [price_at_event], color=color, s=120, marker=marker, zorder=5, edgecolors="white", linewidths=1.5
    )

    # Draw flag label with background box
    ax.annotate(
        event_label,
        xy=(actual_date, flag_y),
        fontsize=11,
        fontweight="bold",
        color=color,
        ha="center",
        va=va,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": color, "linewidth": 1.5, "alpha": 0.9},
    )

# Create custom legend for event types
legend_elements = []
for etype, color in event_colors.items():
    marker = event_markers[etype]
    legend_elements.append(
        plt.scatter(
            [], [], color=color, marker=marker, s=150, label=etype.capitalize(), edgecolors="white", linewidths=1.5
        )
    )

ax.legend(
    handles=legend_elements, loc="upper left", fontsize=14, framealpha=0.9, title="Event Types", title_fontsize=15
)

# Styling
ax.set_title("stock-event-flags · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Stock Price ($)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

# Add subtle price range shading
ax.fill_between(df["date"], df["close"].min(), df["close"], alpha=0.1, color="#306998")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
