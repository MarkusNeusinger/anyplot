""" pyplots.ai
indicator-macd: MACD Technical Indicator Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Legend, Span
from bokeh.plotting import figure


# Data - Generate synthetic stock price data and calculate MACD
np.random.seed(42)
n_days = 150

# Generate realistic price movement with trend and volatility
returns = np.random.normal(0.001, 0.02, n_days)
price = 100 * np.cumprod(1 + returns)

# Calculate EMAs
df = pd.DataFrame({"date": pd.date_range("2025-06-01", periods=n_days, freq="D"), "close": price})

# Calculate 12-day and 26-day EMA
df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()

# Calculate MACD line (12-day EMA - 26-day EMA)
df["macd"] = df["ema12"] - df["ema26"]

# Calculate signal line (9-day EMA of MACD)
df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()

# Calculate histogram (MACD - Signal)
df["histogram"] = df["macd"] - df["signal"]

# Use data from day 35 onwards for meaningful MACD values
df = df.iloc[35:].reset_index(drop=True)

# Separate positive and negative histogram values for coloring
df["hist_positive"] = df["histogram"].where(df["histogram"] >= 0, 0)
df["hist_negative"] = df["histogram"].where(df["histogram"] < 0, 0)

# Create ColumnDataSource
source = ColumnDataSource(
    data={
        "date": df["date"],
        "macd": df["macd"],
        "signal": df["signal"],
        "histogram": df["histogram"],
        "hist_positive": df["hist_positive"],
        "hist_negative": df["hist_negative"],
    }
)

# Create figure with 4800x2700 dimensions
p = figure(
    width=4800,
    height=2700,
    x_axis_type="datetime",
    title="indicator-macd · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="MACD Value",
)

# Calculate bar width (1 day in milliseconds, slightly narrower for gaps)
bar_width = 0.8 * 24 * 60 * 60 * 1000

# Plot histogram bars - positive (green)
hist_pos = p.vbar(
    x="date",
    top="hist_positive",
    width=bar_width,
    source=source,
    fill_color="#2ECC71",
    line_color="#27AE60",
    line_width=1,
    alpha=0.8,
)

# Plot histogram bars - negative (red)
hist_neg = p.vbar(
    x="date",
    top="hist_negative",
    width=bar_width,
    source=source,
    fill_color="#E74C3C",
    line_color="#C0392B",
    line_width=1,
    alpha=0.8,
)

# Plot MACD line (Python Blue)
macd_line = p.line(x="date", y="macd", source=source, line_color="#306998", line_width=4, alpha=0.9)

# Plot signal line (Python Yellow)
signal_line = p.line(x="date", y="signal", source=source, line_color="#FFD43B", line_width=4, alpha=0.9)

# Add zero reference line
zero_line = Span(location=0, dimension="width", line_color="#7F8C8D", line_dash="dashed", line_width=2, line_alpha=0.7)
p.add_layout(zero_line)

# Create legend
legend = Legend(
    items=[
        ("MACD Line (12-26)", [macd_line]),
        ("Signal Line (9)", [signal_line]),
        ("Histogram (+)", [hist_pos]),
        ("Histogram (-)", [hist_neg]),
    ],
    location="top_left",
)
legend.label_text_font_size = "22pt"
legend.spacing = 10
legend.background_fill_alpha = 0.7
p.add_layout(legend)

# Styling for large canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Output toolbar configuration
p.toolbar_location = None

# Save as PNG
export_png(p, filename="plot.png")
