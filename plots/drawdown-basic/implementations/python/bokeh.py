""" pyplots.ai
drawdown-basic: Drawdown Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure


# Data - simulate 3 years of daily stock prices
np.random.seed(42)
n_days = 750  # ~3 years of trading days
dates = pd.date_range("2022-01-01", periods=n_days, freq="B")

# Generate price series with realistic trends and volatility
returns = np.random.normal(0.0003, 0.015, n_days)  # daily returns
# Add some market stress periods
returns[200:250] = np.random.normal(-0.005, 0.025, 50)  # drawdown period 1
returns[450:520] = np.random.normal(-0.008, 0.030, 70)  # larger drawdown period 2
returns[600:630] = np.random.normal(-0.004, 0.020, 30)  # smaller drawdown

prices = 100 * np.exp(np.cumsum(returns))

# Calculate drawdown
running_max = np.maximum.accumulate(prices)
drawdown = (prices - running_max) / running_max * 100

# Create dataframe
df = pd.DataFrame({"date": dates, "price": prices, "running_max": running_max, "drawdown": drawdown})

# Find maximum drawdown point
max_dd_idx = np.argmin(drawdown)
max_dd_value = drawdown[max_dd_idx]
max_dd_date = dates[max_dd_idx]

# Create ColumnDataSource
source = ColumnDataSource(data={"date": df["date"], "drawdown": df["drawdown"], "zero": np.zeros(len(df))})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="drawdown-basic · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Drawdown (%)",
    x_axis_type="datetime",
)

# Fill area between zero and drawdown (red for negative)
p.varea(x="date", y1="zero", y2="drawdown", source=source, fill_color="#DC3545", fill_alpha=0.4)

# Drawdown line
p.line(x="date", y="drawdown", source=source, line_color="#DC3545", line_width=2, legend_label="Drawdown")

# Zero reference line
zero_line = Span(location=0, dimension="width", line_color="#333333", line_width=2, line_dash="solid")
p.add_layout(zero_line)

# Mark maximum drawdown point
p.scatter(
    x=[max_dd_date],
    y=[max_dd_value],
    size=20,
    color="#306998",
    marker="circle",
    legend_label=f"Max Drawdown: {max_dd_value:.1f}%",
)

# Add annotation for max drawdown
max_dd_label = Label(
    x=max_dd_date,
    y=max_dd_value,
    text=f"  Max DD: {max_dd_value:.1f}%",
    text_font_size="20pt",
    text_color="#306998",
    x_offset=10,
    y_offset=-10,
)
p.add_layout(max_dd_label)

# Style the figure
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Legend styling
p.legend.location = "bottom_left"
p.legend.label_text_font_size = "18pt"
p.legend.background_fill_alpha = 0.7

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#FAFAFA"

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html", title="Drawdown Chart")
save(p)
