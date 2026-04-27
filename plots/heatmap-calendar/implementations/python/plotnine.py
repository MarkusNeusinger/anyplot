"""anyplot.ai
heatmap-calendar: Basic Calendar Heatmap
Library: plotnine 0.15.3 | Python 3.14.4
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    ggsave,
    labs,
    scale_fill_cmap,
    scale_x_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - One year of daily activity (GitHub-style contribution data)
np.random.seed(42)

start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

values = []
for date in dates:
    base = np.random.poisson(5)
    if date.dayofweek >= 5:
        base = int(base * 0.3)
    if date.month in [3, 4, 9, 10]:
        base = int(base * 1.5)
    if date.month in [7, 8]:
        base = int(base * 0.5)
    if np.random.random() < 0.15:
        base = 0
    values.append(max(0, base))

df = pd.DataFrame({"date": dates, "value": values})

df["week"] = df["date"].dt.isocalendar().week
df["day_of_week"] = df["date"].dt.dayofweek
df["month"] = df["date"].dt.month

df["week_adjusted"] = df["week"].astype(int)
mask = (df["month"] == 1) & (df["week"] > 50)
df.loc[mask, "week_adjusted"] = 0
mask = (df["month"] == 12) & (df["week"] == 1)
df.loc[mask, "week_adjusted"] = 53

weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
df["weekday"] = df["day_of_week"].map(lambda x: weekday_labels[x])
df["weekday"] = pd.Categorical(df["weekday"], categories=weekday_labels[::-1], ordered=True)

# Zero-activity days rendered as NA so they blend with the panel background
df["value_display"] = df["value"].where(df["value"] > 0, other=None)

month_labels = df.groupby("month")["week_adjusted"].min().reset_index()
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_labels["month_name"] = month_labels["month"].map(lambda x: month_names[x - 1])

plot = (
    ggplot(df, aes(x="week_adjusted", y="weekday", fill="value_display"))
    + geom_tile(color=PAGE_BG, size=0.5)
    + scale_fill_cmap(cmap_name="viridis", na_value=PAGE_BG, name="Contributions")
    + scale_x_continuous(breaks=month_labels["week_adjusted"].tolist(), labels=month_labels["month_name"].tolist())
    + labs(x="", y="", title="Daily Activity 2024 · heatmap-calendar · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color=INK_SOFT),
        axis_title=element_text(size=20, color=INK),
        axis_text_x=element_text(size=18, color=INK_SOFT),
        axis_text_y=element_text(size=18, color=INK_SOFT),
        plot_title=element_text(size=26, weight="bold", color=INK),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
)

ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9, verbose=False)
