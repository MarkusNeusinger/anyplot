""" anyplot.ai
heatmap-calendar: Basic Calendar Heatmap
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 85/100 | Updated: 2026-04-27
"""
# ruff: noqa: F405

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Generate one year of daily activity data
np.random.seed(42)
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Generate realistic activity data (like GitHub contributions)
values = []
for date in dates:
    base = np.random.poisson(5)
    if date.dayofweek >= 5:
        base = int(base * 0.4)
    if np.random.random() < 0.1:
        base = int(base * 3)
    if np.random.random() < 0.15:
        base = 0
    values.append(base)

df = pd.DataFrame({"date": dates, "value": values})
df["date_str"] = df["date"].dt.strftime("%b %d, %Y")
df["weekday"] = df["date"].dt.dayofweek  # 0=Monday, 6=Sunday
df["month"] = df["date"].dt.month
df["week_of_year"] = (df["date"] - start_date).dt.days // 7

weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_positions = df.groupby("month")["week_of_year"].min().tolist()

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=24, hjust=0.5),
    axis_title=element_text(color=INK_SOFT, size=18),
    axis_text_x=element_text(size=18, color=INK_SOFT),
    axis_text_y=element_text(size=18, color=INK_SOFT),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
)

plot = (
    ggplot(df, aes(x="week_of_year", y="weekday", fill="value"))
    + geom_tile(
        tooltips=layer_tooltips().line("@date_str").line("Activity: @value"),
        color=PAGE_BG,
        size=0.8,
        width=0.9,
        height=0.9,
    )
    + scale_fill_viridis(name="Activity")
    + scale_y_reverse(breaks=[0, 1, 2, 3, 4, 5, 6], labels=weekday_labels)
    + scale_x_continuous(breaks=month_positions, labels=month_names)
    + labs(title="heatmap-calendar · letsplot · anyplot.ai", x="Month (2024)", y="Day of Week")
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save as PNG and HTML
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")

# Clean up lets-plot-images directory if created
if os.path.exists("lets-plot-images"):
    shutil.rmtree("lets-plot-images")
