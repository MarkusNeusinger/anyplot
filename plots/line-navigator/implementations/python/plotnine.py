""" pyplots.ai
line-navigator: Line Chart with Mini Navigator
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_rect,
    geom_vline,
    ggplot,
    labs,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - 3 years of daily sensor readings (1095+ data points)
np.random.seed(42)
n_days = 1100
dates = pd.date_range("2021-01-01", periods=n_days, freq="D")

# Generate realistic sensor data with seasonal patterns and noise
# Base signal with seasonal component (temperature-like pattern)
day_of_year = np.arange(n_days) % 365
seasonal = 20 * np.sin(2 * np.pi * day_of_year / 365)  # Seasonal cycle

# Add trend component
trend = np.linspace(0, 8, n_days)  # Gradual upward drift

# Add random noise with varying volatility
noise = np.random.normal(0, 3, n_days)

# Add some anomalies/spikes
anomalies = np.zeros(n_days)
anomaly_indices = [150, 420, 680, 950]
for idx in anomaly_indices:
    if idx < n_days:
        anomalies[idx : idx + 5] = np.random.uniform(8, 15, min(5, n_days - idx))

# Combine components with base value
base_value = 50
value = base_value + seasonal + trend + noise + anomalies

df = pd.DataFrame({"date": dates, "value": value})

# Define selected range for detail view (simulating user selection of ~4 months)
range_start = pd.Timestamp("2022-06-01")
range_end = pd.Timestamp("2022-10-15")

# Data for detail view (selected range only)
df_detail = df[(df["date"] >= range_start) & (df["date"] <= range_end)].copy()

# Data for range highlight in navigator
range_highlight = pd.DataFrame({"xmin": [range_start], "xmax": [range_end]})

# Navigator y-axis range for annotation positioning
nav_y_min = df["value"].min()
nav_y_max = df["value"].max()

# Shared theme settings for large canvas (4800x2700 px)
shared_theme = theme_minimal() + theme(
    text=element_text(size=14),
    axis_title=element_text(size=18),
    axis_text=element_text(size=14),
    axis_text_x=element_text(angle=0),
    panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
    panel_grid_minor=element_blank(),
    plot_margin=0.02,
)

# Detail View - Main chart showing selected range in full detail
p_detail = (
    ggplot(df_detail, aes(x="date", y="value"))
    + geom_line(color="#306998", size=1.2)
    + scale_x_datetime(date_labels="%d %b", date_breaks="2 weeks")
    + scale_y_continuous(labels=lambda x: [f"{v:.0f}" for v in x])
    + labs(x="", y="Sensor Reading", title="")
    + shared_theme
    + theme(axis_text_x=element_text(angle=45, ha="right"))
)

# Navigator - Mini chart showing full data extent with selection window
p_navigator = (
    ggplot(df, aes(x="date", y="value"))
    # Selection highlight (shaded region)
    + geom_rect(
        data=range_highlight,
        mapping=aes(xmin="xmin", xmax="xmax"),
        ymin=-np.inf,
        ymax=np.inf,
        fill="#306998",
        alpha=0.25,
        inherit_aes=False,
    )
    # Selection boundary lines (resize handles visualization)
    + geom_vline(data=range_highlight, mapping=aes(xintercept="xmin"), color="#1a4971", size=1.5, linetype="solid")
    + geom_vline(data=range_highlight, mapping=aes(xintercept="xmax"), color="#1a4971", size=1.5, linetype="solid")
    # Full data line
    + geom_line(color="#306998", size=0.8)
    # Annotation for selected range
    + annotate(
        "text",
        x=range_start + (range_end - range_start) / 2,
        y=nav_y_max - (nav_y_max - nav_y_min) * 0.08,
        label="Selected Range",
        size=12,
        color="#1a4971",
        fontweight="bold",
    )
    + scale_x_datetime(date_labels="%b %Y", date_breaks="6 months")
    + scale_y_continuous(labels=lambda x: [f"{v:.0f}" for v in x])
    + labs(x="Date", y="", title="Navigator")
    + shared_theme
    + theme(plot_title=element_text(size=14, weight="bold", ha="left"))
)

# Compose plots vertically: detail on top, navigator below
# Using plotnine's composition operator
grid = p_detail / p_navigator

# Draw and customize for different panel heights
fig = grid.draw()
fig.set_size_inches(16, 10)

# Adjust heights: main chart larger, navigator smaller (~25% of total)
fig.subplots_adjust(top=0.85, bottom=0.10, hspace=0.30)

# Add main title
fig.suptitle("line-navigator · plotnine · pyplots.ai", fontsize=26, fontweight="bold", y=0.98)

# Adjust axes heights (detail ~75%, navigator ~25%)
axes = fig.axes
if len(axes) >= 2:
    # Get positions
    pos0 = axes[0].get_position()
    pos1 = axes[1].get_position()

    # Total height available
    total_height = pos0.y1 - pos1.y0
    nav_height_ratio = 0.25
    detail_height_ratio = 0.75
    gap = 0.06

    # New positions
    nav_height = total_height * nav_height_ratio
    detail_height = total_height * detail_height_ratio - gap

    # Set navigator position (bottom)
    axes[1].set_position([pos1.x0, pos1.y0, pos1.width, nav_height])

    # Set detail position (top)
    detail_y0 = pos1.y0 + nav_height + gap
    axes[0].set_position([pos0.x0, detail_y0, pos0.width, detail_height])

# Save
fig.savefig("plot.png", dpi=300, bbox_inches="tight")
