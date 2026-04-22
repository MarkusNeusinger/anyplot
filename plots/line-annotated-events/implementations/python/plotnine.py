""" pyplots.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Data - Simulated website traffic with product release events
np.random.seed(42)

# Generate daily data for one year
dates = pd.date_range("2024-01-01", periods=365, freq="D")
base = 50000 + np.cumsum(np.random.randn(365) * 500)
seasonal = 5000 * np.sin(2 * np.pi * np.arange(365) / 365)
weekly = 3000 * np.sin(2 * np.pi * np.arange(365) / 7)
values = base + seasonal + weekly

df = pd.DataFrame({"date": dates, "value": values})

# Event markers - product releases and major updates
events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(["2024-02-15", "2024-05-01", "2024-07-20", "2024-10-10", "2024-12-01"]),
        "event_label": ["v2.0 Release", "Mobile App Launch", "API Update", "Enterprise Tier", "Holiday Campaign"],
        "y_offset": [0.92, 0.85, 0.92, 0.85, 0.92],  # Alternating heights to avoid overlap
    }
)

# Calculate y positions for labels (as fraction of y range)
y_min, y_max = df["value"].min(), df["value"].max()
y_range = y_max - y_min
events["y_pos"] = y_min + events["y_offset"] * y_range

# Create the plot
plot = (
    ggplot(df, aes(x="date", y="value"))
    + geom_line(color="#306998", size=1.2, alpha=0.9)
    + geom_vline(aes(xintercept="event_date"), data=events, color="#FFD43B", linetype="dashed", size=1.0, alpha=0.8)
    + geom_point(aes(x="event_date", y="y_pos"), data=events, color="#FFD43B", size=4, shape="D")
    + geom_text(
        aes(x="event_date", y="y_pos", label="event_label"),
        data=events,
        color="#333333",
        size=10,
        ha="center",
        va="bottom",
        nudge_y=1000,
        fontweight="bold",
    )
    + labs(x="Date", y="Daily Visitors", title="line-annotated-events · plotnine · pyplots.ai")
    + scale_x_datetime(date_breaks="2 months", date_labels="%b %Y")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, ha="right"),
        plot_title=element_text(size=24, weight="bold"),
        panel_grid_major=element_line(color="#cccccc", size=0.3, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.2, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
