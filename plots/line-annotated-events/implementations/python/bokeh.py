""" pyplots.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=365, freq="D")
base_trend = np.linspace(100, 180, 365)
seasonal = 15 * np.sin(np.arange(365) * 2 * np.pi / 365)
noise = np.cumsum(np.random.randn(365) * 0.8)
values = base_trend + seasonal + noise

# Event data (product milestones)
event_dates = pd.to_datetime(["2024-02-15", "2024-05-01", "2024-07-20", "2024-09-10", "2024-11-25"])
event_labels = ["Product Launch", "Feature Update", "Server Upgrade", "API v2 Release", "Mobile App Launch"]
event_heights = [0.92, 0.84, 0.92, 0.84, 0.92]

# Create data source
source = ColumnDataSource(data={"date": dates, "value": values})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-annotated-events · bokeh · pyplots.ai",
    x_axis_type="datetime",
    x_axis_label="Date",
    y_axis_label="Active Users (thousands)",
)

# Main line plot
p.line("date", "value", source=source, line_width=4, color="#306998", legend_label="Daily Active Users")

# Add event markers
for event_date, label, h in zip(event_dates, event_labels, event_heights, strict=True):
    # Vertical span line
    vline = Span(location=event_date, dimension="height", line_color="#FFD43B", line_width=3, line_dash="dashed")
    p.add_layout(vline)

    # Event label
    y_range = values.max() - values.min()
    y_pos = values.min() + y_range * h
    event_label = Label(
        x=event_date,
        y=y_pos,
        text=label,
        text_font_size="16pt",
        text_color="#333333",
        text_font_style="bold",
        x_offset=5,
        y_offset=0,
    )
    p.add_layout(event_label)

# Styling
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.legend.label_text_font_size = "18pt"
p.legend.location = "bottom_right"
p.legend.background_fill_alpha = 0.7
p.legend.border_line_color = "#cccccc"

p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Hide toolbar for PNG export
p.toolbar_location = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="line-annotated-events · bokeh · pyplots.ai")
