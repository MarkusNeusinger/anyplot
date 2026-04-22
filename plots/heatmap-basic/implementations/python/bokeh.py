""" pyplots.ai
heatmap-basic: Basic Heatmap
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-15
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import BasicTicker, ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.transform import linear_cmap


# Data - Monthly temperature anomalies (°C) by city
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
cities = ["Oslo", "Berlin", "Madrid", "Cairo", "Mumbai", "Tokyo", "Sydney"]

# Generate realistic temperature anomalies with geographic patterns
base_anomalies = np.random.randn(len(cities), len(months)) * 0.6
# Northern cities: colder winters, warmer summers
for i, city in enumerate(cities):
    seasonal = np.sin(np.linspace(-np.pi / 2, 3 * np.pi / 4, len(months)))
    if city in ("Oslo", "Berlin"):
        base_anomalies[i] += seasonal * 1.5 - 0.3
    elif city in ("Madrid", "Cairo"):
        base_anomalies[i] += seasonal * 1.2 + 0.4
    elif city == "Mumbai":
        base_anomalies[i] += 0.8
    elif city == "Sydney":
        base_anomalies[i] -= seasonal * 0.9
    elif city == "Tokyo":
        base_anomalies[i] += seasonal * 0.7

values = np.round(base_anomalies, 1)

# Flatten to DataFrame for ColumnDataSource
records = []
for i, city in enumerate(cities):
    for j, month in enumerate(months):
        val = values[i, j]
        records.append(
            {
                "month": month,
                "city": city,
                "anomaly": val,
                "label": f"{val:+.1f}",
                "text_color": "white" if abs(val) > 1.2 else "#333333",
            }
        )

source = ColumnDataSource(pd.DataFrame(records))

# Color mapping — diverging palette for positive/negative anomalies
blues = ["#2166ac", "#4393c3", "#92c5de", "#d1e5f0"]
reds = ["#fddbc7", "#f4a582", "#d6604d", "#b2182b"]
diverging_palette = blues[::-1] + ["#f7f7f7"] + reds

# Create figure
p = figure(
    width=4800,
    height=2700,
    x_range=months,
    y_range=list(reversed(cities)),
    title="heatmap-basic · bokeh · pyplots.ai",
    x_axis_label="Month (2024)",
    y_axis_label="City",
    toolbar_location=None,
    tools="",
)

# Plot heatmap rectangles with linear_cmap
cmap = linear_cmap("anomaly", diverging_palette, low=-2.5, high=2.5)
r = p.rect(x="month", y="city", width=1, height=1, source=source, fill_color=cmap, line_color="white", line_width=2)

# Add value annotations
labels = LabelSet(
    x="month",
    y="city",
    text="label",
    text_color="text_color",
    source=source,
    text_align="center",
    text_baseline="middle",
    text_font_size="22pt",
)
p.add_layout(labels)

# Color bar from renderer (idiomatic Bokeh pattern)
color_bar = r.construct_color_bar(
    width=40,
    ticker=BasicTicker(desired_num_ticks=10),
    label_standoff=16,
    major_label_text_font_size="18pt",
    border_line_color=None,
    padding=10,
    title="Anomaly (°C)",
    title_text_font_size="20pt",
    title_standoff=20,
)
p.add_layout(color_bar, "right")

# HoverTool for interactive HTML version
hover = HoverTool(tooltips=[("City", "@city"), ("Month", "@month"), ("Anomaly", "@anomaly{+0.0} °C")], renderers=[r])
p.add_tools(hover)

# Styling for 4800x2700 px
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid and axes
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.outline_line_color = None

# Background
p.min_border_right = 120
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Save PNG
export_png(p, filename="plot.png")

# Save HTML with interactive hover
save(p, filename="plot.html", resources=CDN, title="heatmap-basic · bokeh · pyplots.ai")
