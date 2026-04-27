"""anyplot.ai
heatmap-calendar: Basic Calendar Heatmap
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-04-27
"""

import os

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, FixedTicker, LinearColorMapper
from bokeh.palettes import Greens9
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Generate daily values for one year
np.random.seed(42)
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Simulate GitHub-style contributions with realistic patterns
values = []
for date in dates:
    weekday = date.weekday()
    base = 2 if weekday >= 5 else 5
    val = np.random.poisson(base)
    if np.random.random() < 0.05:
        val += np.random.randint(5, 15)
    if np.random.random() < 0.15:
        val = 0
    values.append(val)

df = pd.DataFrame({"date": dates, "value": values})
df["weekday"] = df["date"].dt.weekday
df["week_of_year"] = (df["date"] - start_date).dt.days // 7
df["month"] = df["date"].dt.month

weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

source = ColumnDataSource(
    data={
        "week": df["week_of_year"].tolist(),
        "weekday": [weekday_names[w] for w in df["weekday"]],
        "value": df["value"].tolist(),
        "date": df["date"].dt.strftime("%Y-%m-%d").tolist(),
    }
)

# Color mapper — reversed Greens so low=light, high=dark green
palette = list(reversed(Greens9))
mapper = LinearColorMapper(palette=palette, low=0, high=df["value"].max())

# Month positions for x-axis labels
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_starts = df.groupby("month")["week_of_year"].min().to_dict()
month_ticks = list(month_starts.values())
month_labels = {v: month_names[k - 1] for k, v in month_starts.items()}

# Plot
p = figure(
    width=4800,
    height=2700,
    title="GitHub Contributions 2024 · heatmap-calendar · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Day of Week",
    y_range=list(reversed(weekday_names)),
    tools="hover",
    tooltips=[("Date", "@date"), ("Contributions", "@value")],
)

p.rect(
    x="week",
    y="weekday",
    width=0.9,
    height=0.9,
    source=source,
    fill_color={"field": "value", "transform": mapper},
    line_color=PAGE_BG,
    line_width=2,
)

# Color bar
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=12,
    major_label_text_font_size="18pt",
    major_label_text_color=INK_SOFT,
    title="Contributions",
    title_text_font_size="20pt",
    title_text_color=INK,
    background_fill_color=ELEVATED_BG,
    width=40,
    location=(0, 0),
)
p.add_layout(color_bar, "right")

# Month labels on x-axis
p.xaxis.ticker = FixedTicker(ticks=month_ticks)
p.xaxis.major_label_overrides = month_labels

# Text sizes
p.title.text_font_size = "32pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Chrome colors
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# No grid for heatmap
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
