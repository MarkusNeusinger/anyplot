""" pyplots.ai
stock-event-flags: Stock Chart with Event Flags
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_shape_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Generate stock price data
np.random.seed(42)
n_days = 180
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days

# Simulate stock price with random walk
returns = np.random.normal(0.0005, 0.018, n_days)
price = 150 * np.cumprod(1 + returns)

df_price = pd.DataFrame({"date": dates, "close": price})

# Define events
events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(
            [
                "2024-01-25",
                "2024-02-15",
                "2024-04-02",
                "2024-04-25",
                "2024-05-20",
                "2024-06-10",
                "2024-07-25",
                "2024-08-15",
            ]
        ),
        "event_type": ["Earnings", "Dividend", "News", "Earnings", "Split", "Dividend", "Earnings", "News"],
        "event_label": [
            "Q4 Beat",
            "Div $0.50",
            "New Product",
            "Q1 Miss",
            "2:1 Split",
            "Div $0.55",
            "Q2 Beat",
            "Partnership",
        ],
    }
)

# Match events to price data (find closest trading date)
events["matched_date"] = events["event_date"].apply(
    lambda x: df_price.loc[(df_price["date"] - x).abs().idxmin(), "date"]
)
events["price_at_event"] = events["matched_date"].apply(
    lambda x: df_price.loc[df_price["date"] == x, "close"].values[0]
)

# Calculate flag positions - alternate above/below to avoid overlap
max_price = df_price["close"].max()
min_price = df_price["close"].min()
price_range = max_price - min_price

# Position flags with alternating heights
flag_offsets = []
for i, (_, row) in enumerate(events.iterrows()):
    if i % 2 == 0:
        flag_offsets.append(row["price_at_event"] + price_range * 0.15 + (i % 3) * price_range * 0.08)
    else:
        flag_offsets.append(row["price_at_event"] - price_range * 0.15 - (i % 3) * price_range * 0.08)

events["flag_y"] = flag_offsets

# Color mapping for event types
color_map = {
    "Earnings": "#306998",  # Python Blue
    "Dividend": "#2E8B57",  # Sea Green
    "News": "#FFD43B",  # Python Yellow
    "Split": "#DC143C",  # Crimson
}

events["color"] = events["event_type"].map(color_map)

# Build the plot
plot = (
    ggplot()
    # Stock price line
    + geom_line(data=df_price, mapping=aes(x="date", y="close"), color="#306998", size=1.5, alpha=0.9)
    # Vertical dashed lines at event dates
    + geom_vline(
        data=events, mapping=aes(xintercept="matched_date"), linetype="dashed", color="#888888", alpha=0.5, size=0.5
    )
    # Connector lines from price to flag
    + geom_segment(
        data=events,
        mapping=aes(x="matched_date", xend="matched_date", y="price_at_event", yend="flag_y", color="event_type"),
        size=0.8,
        linetype="solid",
    )
    # Flag markers (points at flag position)
    + geom_point(
        data=events,
        mapping=aes(x="matched_date", y="flag_y", color="event_type", shape="event_type"),
        size=6,
        fill="white",
        stroke=2,
    )
    # Event labels
    + geom_text(
        data=events,
        mapping=aes(x="matched_date", y="flag_y", label="event_label", color="event_type"),
        size=11,
        ha="center",
        va="bottom",
        nudge_y=price_range * 0.03,
        fontweight="bold",
    )
    # Styling
    + scale_color_manual(values=color_map, name="Event Type")
    + scale_shape_manual(values={"Earnings": "s", "Dividend": "D", "News": "^", "Split": "o"}, name="Event Type")
    + scale_x_datetime(date_labels="%b %Y", date_breaks="1 month")
    + labs(title="stock-event-flags · plotnine · pyplots.ai", x="Date", y="Stock Price ($)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=14),
        axis_text_x=element_text(rotation=45, ha="right"),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_line(color="#E0E0E0", size=0.5),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
