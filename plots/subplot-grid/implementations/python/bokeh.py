""" pyplots.ai
subplot-grid: Subplot Grid Layout
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, Title
from bokeh.plotting import figure, output_file, save


# Data - Financial dashboard with multiple metrics
np.random.seed(42)

# Time series data for price and volume (trading days)
n_days = 60
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
date_strings = [d.strftime("%b %d") for d in dates]

# Price data (cumulative returns creating realistic price movement)
returns = np.random.normal(0.001, 0.02, n_days)
price = 100 * np.cumprod(1 + returns)

# Volume data (with some correlation to price movement)
base_volume = np.random.uniform(0.8, 1.2, n_days) * 1_000_000
volume = base_volume * (1 + np.abs(returns) * 10)

# Scatter data for risk vs return
n_assets = 40
asset_returns = np.random.normal(8, 4, n_assets)
asset_risk = np.abs(asset_returns) * 0.3 + np.random.uniform(2, 8, n_assets)

# Histogram data - daily returns distribution
daily_returns = np.random.normal(0.1, 2.5, 200)

# Colors
python_blue = "#306998"
python_yellow = "#FFD43B"
accent_green = "#2E7D32"
accent_red = "#C62828"

# ========== SUBPLOT 1: Price Line Chart (top-left) ==========
source_price = ColumnDataSource(data={"x": list(range(n_days)), "y": price, "date": date_strings})

p1 = figure(
    width=2400,
    height=1350,
    title="Stock Price Over Time",
    x_axis_label="Trading Day",
    y_axis_label="Price ($)",
    tools="",
    toolbar_location=None,
)
p1.line("x", "y", source=source_price, line_width=4, color=python_blue, alpha=0.9)
p1.scatter("x", "y", source=source_price, size=8, color=python_blue, alpha=0.6)

# Styling for p1
p1.title.text_font_size = "24pt"
p1.xaxis.axis_label_text_font_size = "20pt"
p1.yaxis.axis_label_text_font_size = "20pt"
p1.xaxis.major_label_text_font_size = "16pt"
p1.yaxis.major_label_text_font_size = "16pt"
p1.xaxis.major_label_orientation = 0.7
p1.grid.grid_line_alpha = 0.3
p1.grid.grid_line_dash = "dashed"

# ========== SUBPLOT 2: Volume Bar Chart (top-right) ==========
source_volume = ColumnDataSource(data={"x": list(range(n_days)), "y": volume / 1_000_000, "date": date_strings})

p2 = figure(
    width=2400,
    height=1350,
    title="Daily Trading Volume",
    x_axis_label="Trading Day",
    y_axis_label="Volume (Millions)",
    tools="",
    toolbar_location=None,
)
p2.vbar(x="x", top="y", source=source_volume, width=0.7, color=python_yellow, alpha=0.8)

# Styling for p2
p2.title.text_font_size = "24pt"
p2.xaxis.axis_label_text_font_size = "20pt"
p2.yaxis.axis_label_text_font_size = "20pt"
p2.xaxis.major_label_text_font_size = "16pt"
p2.yaxis.major_label_text_font_size = "16pt"
p2.xaxis.major_label_orientation = 0.7
p2.grid.grid_line_alpha = 0.3
p2.grid.grid_line_dash = "dashed"

# ========== SUBPLOT 3: Risk vs Return Scatter (bottom-left) ==========
# Color by performance (positive vs negative returns)
colors = [accent_green if r > 8 else (accent_red if r < 5 else python_blue) for r in asset_returns]

source_scatter = ColumnDataSource(data={"x": asset_risk, "y": asset_returns, "color": colors})

p3 = figure(
    width=2400,
    height=1350,
    title="Risk vs Return Analysis",
    x_axis_label="Risk (Volatility %)",
    y_axis_label="Annual Return (%)",
    tools="",
    toolbar_location=None,
)
p3.scatter("x", "y", source=source_scatter, size=18, color="color", alpha=0.7)

# Styling for p3
p3.title.text_font_size = "24pt"
p3.xaxis.axis_label_text_font_size = "20pt"
p3.yaxis.axis_label_text_font_size = "20pt"
p3.xaxis.major_label_text_font_size = "16pt"
p3.yaxis.major_label_text_font_size = "16pt"
p3.grid.grid_line_alpha = 0.3
p3.grid.grid_line_dash = "dashed"

# ========== SUBPLOT 4: Returns Distribution Histogram (bottom-right) ==========
# Create histogram bins
hist, edges = np.histogram(daily_returns, bins=25)

source_hist = ColumnDataSource(data={"top": hist, "left": edges[:-1], "right": edges[1:]})

p4 = figure(
    width=2400,
    height=1350,
    title="Daily Returns Distribution",
    x_axis_label="Daily Return (%)",
    y_axis_label="Frequency",
    tools="",
    toolbar_location=None,
)
p4.quad(
    top="top",
    bottom=0,
    left="left",
    right="right",
    source=source_hist,
    fill_color=python_blue,
    line_color="white",
    alpha=0.8,
    line_width=2,
)

# Styling for p4
p4.title.text_font_size = "24pt"
p4.xaxis.axis_label_text_font_size = "20pt"
p4.yaxis.axis_label_text_font_size = "20pt"
p4.xaxis.major_label_text_font_size = "16pt"
p4.yaxis.major_label_text_font_size = "16pt"
p4.grid.grid_line_alpha = 0.3
p4.grid.grid_line_dash = "dashed"

# ========== CREATE GRID LAYOUT ==========
grid = gridplot([[p1, p2], [p3, p4]], merge_tools=False, toolbar_location=None)

# Add main title using the first plot's add_layout
main_title = Title(text="subplot-grid · bokeh · pyplots.ai", text_font_size="32pt", align="center")
p1.add_layout(main_title, "above")

# Save as PNG
export_png(grid, filename="plot.png")

# Save as HTML for interactive viewing
output_file("plot.html", title="subplot-grid · bokeh · pyplots.ai")
save(grid)
