""" pyplots.ai
heatmap-calendar: Basic Calendar Heatmap
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, FixedTicker, LinearColorMapper
from bokeh.palettes import Greens9
from bokeh.plotting import figure


# Data - Generate daily values for one year
np.random.seed(42)
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Simulate GitHub-style contributions with realistic patterns
values = []
for date in dates:
    weekday = date.weekday()
    # Lower activity on weekends
    base = 2 if weekday >= 5 else 5
    # Random variation
    val = np.random.poisson(base)
    # Occasional bursts of high activity
    if np.random.random() < 0.05:
        val += np.random.randint(5, 15)
    # Some days with no activity
    if np.random.random() < 0.15:
        val = 0
    values.append(val)

df = pd.DataFrame({"date": dates, "value": values})

# Extract calendar components
df["weekday"] = df["date"].dt.weekday

# Compute continuous week index from start of year
df["week_of_year"] = (df["date"] - start_date).dt.days // 7

# Weekday names for y-axis
weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Create ColumnDataSource
source = ColumnDataSource(
    data={
        "week": df["week_of_year"].tolist(),
        "weekday": [weekday_names[w] for w in df["weekday"]],
        "value": df["value"].tolist(),
        "date": df["date"].dt.strftime("%Y-%m-%d").tolist(),
    }
)

# Color mapper - Greens palette from light to dark
colors = list(reversed(Greens9))
mapper = LinearColorMapper(palette=colors, low=0, high=df["value"].max())

# Get month start positions for x-axis labels
df["month"] = df["date"].dt.month
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_starts = df.groupby("month")["week_of_year"].min().to_dict()
month_ticks = list(month_starts.values())
month_labels = {v: months[k - 1] for k, v in month_starts.items()}

# Create figure with categorical y-axis (weekdays)
p = figure(
    width=4800,
    height=2700,
    title="GitHub Contributions 2024 · heatmap-calendar · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Day of Week",
    y_range=list(reversed(weekday_names)),  # Mon at top, Sun at bottom
    tools="hover",
    tooltips=[("Date", "@date"), ("Contributions", "@value")],
)

# Draw rectangles for each day
p.rect(
    x="week",
    y="weekday",
    width=0.9,
    height=0.9,
    source=source,
    fill_color={"field": "value", "transform": mapper},
    line_color="white",
    line_width=2,
)

# Add color bar
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=12,
    major_label_text_font_size="18pt",
    title="Contributions",
    title_text_font_size="20pt",
    width=40,
    location=(0, 0),
)
p.add_layout(color_bar, "right")

# Configure x-axis to show month labels
p.xaxis.ticker = FixedTicker(ticks=month_ticks)
p.xaxis.major_label_overrides = month_labels

# Styling for 4800x2700 px
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Grid styling - disable grid for heatmap
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Axis styling
p.xaxis.axis_line_color = "#cccccc"
p.yaxis.axis_line_color = "#cccccc"

# Save as PNG and HTML
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
