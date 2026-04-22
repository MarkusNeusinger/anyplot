""" pyplots.ai
heatmap-calendar: Basic Calendar Heatmap
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_gradient,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data - One year of daily activity (GitHub-style contribution data)
np.random.seed(42)

# Generate dates for 2024
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Generate realistic activity data with patterns
# Higher activity on weekdays, lower on weekends
# Some periods of high activity, some gaps
values = []
for date in dates:
    # Base activity
    base = np.random.poisson(5)
    # Weekend reduction
    if date.dayofweek >= 5:
        base = int(base * 0.3)
    # Some high-activity periods (like project sprints)
    if date.month in [3, 4, 9, 10]:  # Q2 and Q4 sprints
        base = int(base * 1.5)
    # Summer slowdown
    if date.month in [7, 8]:
        base = int(base * 0.5)
    # Random zero days (no activity)
    if np.random.random() < 0.15:
        base = 0
    values.append(max(0, base))

# Create DataFrame
df = pd.DataFrame({"date": dates, "value": values})

# Calculate week number within year and day of week
df["week"] = df["date"].dt.isocalendar().week
df["year"] = df["date"].dt.year
df["day_of_week"] = df["date"].dt.dayofweek  # Monday=0, Sunday=6
df["month"] = df["date"].dt.month

# Handle year boundary (week 52/53 at start of year)
# Adjust week numbers so they flow continuously
df["week_adjusted"] = df["week"].astype(int)
mask = (df["month"] == 1) & (df["week"] > 50)
df.loc[mask, "week_adjusted"] = 0
mask = (df["month"] == 12) & (df["week"] == 1)
df.loc[mask, "week_adjusted"] = 53

# Create weekday labels (Sun at top, Mon at bottom for GitHub-style)
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
df["weekday"] = df["day_of_week"].map(lambda x: weekday_labels[x])
df["weekday"] = pd.Categorical(df["weekday"], categories=weekday_labels[::-1], ordered=True)

# Calculate month label positions (first week of each month)
month_labels = df.groupby("month")["week_adjusted"].min().reset_index()
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_labels["month_name"] = month_labels["month"].map(lambda x: month_names[x - 1])

# Plot
plot = (
    ggplot(df, aes(x="week_adjusted", y="weekday", fill="value"))
    + geom_tile(color="white", size=0.5)
    + scale_fill_gradient(
        low="#ebedf0",  # Light gray for no activity
        high="#306998",  # Python Blue for high activity
        name="Contributions",
    )
    + scale_x_continuous(breaks=month_labels["week_adjusted"].tolist(), labels=month_labels["month_name"].tolist())
    + labs(x="", y="", title="Daily Activity 2024 · heatmap-calendar · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text_x=element_text(size=18),
        axis_text_y=element_text(size=18),
        plot_title=element_text(size=26, weight="bold"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
