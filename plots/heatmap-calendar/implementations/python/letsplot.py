""" pyplots.ai
heatmap-calendar: Basic Calendar Heatmap
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""
# ruff: noqa: F405

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Data - Generate one year of daily activity data
np.random.seed(42)
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Generate realistic activity data (like GitHub contributions)
# Base activity with weekly pattern (less on weekends)
values = []
for date in dates:
    base = np.random.poisson(5)
    # Lower activity on weekends
    if date.dayofweek >= 5:
        base = int(base * 0.4)
    # Some random high activity days
    if np.random.random() < 0.1:
        base = int(base * 3)
    # Some zero days
    if np.random.random() < 0.15:
        base = 0
    values.append(base)

df = pd.DataFrame({"date": dates, "value": values})

# Extract calendar components
df["weekday"] = df["date"].dt.dayofweek  # 0=Monday, 6=Sunday
df["month"] = df["date"].dt.month

# For proper week positioning, calculate week number from start of year
# This ensures continuous week numbering for the calendar layout
df["week_of_year"] = (df["date"] - start_date).dt.days // 7

# Weekday labels for y-axis
weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Create month labels for x-axis
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Calculate month positions (first week of each month)
month_positions = df.groupby("month")["week_of_year"].min().tolist()

# Plot - reverse y-axis so Monday is at top (like GitHub)
plot = (
    ggplot(df, aes(x="week_of_year", y="weekday", fill="value"))
    + geom_tile(color="white", size=1.0, width=0.9, height=0.9)
    + scale_fill_gradient(low="#ebedf0", high="#306998", name="Activity")
    + scale_y_reverse(breaks=[0, 1, 2, 3, 4, 5, 6], labels=weekday_labels)
    + scale_x_continuous(breaks=month_positions, labels=month_names)
    + labs(title="heatmap-calendar · letsplot · pyplots.ai", x="", y="")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, hjust=0.5),
        axis_title=element_text(size=22),
        axis_text_x=element_text(size=18),
        axis_text_y=element_text(size=18),
        legend_title=element_text(size=20),
        legend_text=element_text(size=16),
        panel_grid=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG and HTML
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")

# Clean up lets-plot-images directory if created
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
