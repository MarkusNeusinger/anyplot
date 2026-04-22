""" pyplots.ai
line-stock-comparison: Stock Price Comparison Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import HoverTool, Legend, Span
from bokeh.plotting import figure


# Data - Generate synthetic stock price data for comparison
np.random.seed(42)
n_days = 252  # Approximately 1 year of trading days
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days

# Stock symbols and their characteristics (drift, volatility)
stocks = {
    "AAPL": {"drift": 0.0008, "volatility": 0.018, "color": "#306998"},  # Python Blue
    "GOOGL": {"drift": 0.0006, "volatility": 0.020, "color": "#FFD43B"},  # Python Yellow
    "MSFT": {"drift": 0.0007, "volatility": 0.016, "color": "#E24A33"},  # Red
    "SPY": {"drift": 0.0004, "volatility": 0.010, "color": "#7A68A6"},  # Purple
}

# Generate price paths using geometric Brownian motion
price_data = {"date": dates}
for symbol, params in stocks.items():
    returns = np.random.normal(params["drift"], params["volatility"], n_days)
    prices = 100 * np.exp(np.cumsum(returns))  # Start at 100 (already normalized)
    price_data[symbol] = prices

df = pd.DataFrame(price_data)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="line-stock-comparison · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Rebased Price (Starting = 100)",
    x_axis_type="datetime",
)

# Style settings
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Add horizontal reference line at 100
hline = Span(location=100, dimension="width", line_color="#888888", line_dash="dashed", line_width=2)
p.add_layout(hline)

# Plot each stock as a line
legend_items = []
for symbol, params in stocks.items():
    line = p.line(x=df["date"], y=df[symbol], line_width=4, line_color=params["color"], alpha=0.9)
    legend_items.append((symbol, [line]))

# Add legend
legend = Legend(
    items=legend_items,
    location="top_left",
    label_text_font_size="20pt",
    glyph_width=40,
    glyph_height=25,
    spacing=10,
    padding=15,
)
legend.click_policy = "hide"
p.add_layout(legend)

# Add hover tool
hover = HoverTool(tooltips=[("Date", "@x{%F}"), ("Value", "@y{0.2f}")], formatters={"@x": "datetime"}, mode="vline")
p.add_tools(hover)

# Grid styling
p.grid.grid_line_alpha = 0.4
p.grid.grid_line_dash = [6, 4]

# Background and outline
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"
p.outline_line_color = "#cccccc"

# Save as PNG and HTML
export_png(p, filename="plot.png")

# Also save HTML for interactive version
output_file("plot.html")
save(p)
