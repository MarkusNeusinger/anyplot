""" pyplots.ai
line-stock-comparison: Stock Price Comparison Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import datetime

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulated daily stock prices for ~1 year (252 trading days)
np.random.seed(42)
n_days = 252

# Generate business days using numpy/datetime (no pandas needed)
start_date = datetime.date(2024, 1, 2)
dates = []
current_date = start_date
while len(dates) < n_days:
    if current_date.weekday() < 5:  # Monday=0 to Friday=4
        dates.append(current_date)
    current_date += datetime.timedelta(days=1)

# Simulate cumulative returns with different trends
# Individual stocks should generally outperform the broad market benchmark (SPY)
returns_aapl = np.random.normal(0.0012, 0.018, n_days)  # Strong growth (tech leader)
returns_googl = np.random.normal(0.0015, 0.022, n_days)  # Highest growth (volatile tech)
returns_msft = np.random.normal(-0.0002, 0.016, n_days)  # Underperformer this period
returns_spy = np.random.normal(0.0004, 0.010, n_days)  # Broad market (lower vol, moderate return)

# Convert to price series (starting at arbitrary prices, then rebase to 100)
price_aapl = 100 * np.cumprod(1 + returns_aapl)
price_googl = 100 * np.cumprod(1 + returns_googl)
price_msft = 100 * np.cumprod(1 + returns_msft)
price_spy = 100 * np.cumprod(1 + returns_spy)

# Rebase all series to 100 at start (already done since we start at 100)
rebased_aapl = price_aapl / price_aapl[0] * 100
rebased_googl = price_googl / price_googl[0] * 100
rebased_msft = price_msft / price_msft[0] * 100
rebased_spy = price_spy / price_spy[0] * 100

# Create custom style with colorblind-friendly palette
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#0072B2", "#E69F00", "#CC79A7", "#009E73"),  # 4 colors for 4 stock series
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=42,
    value_font_size=28,
    value_label_font_size=28,
    tooltip_font_size=32,
    stroke_width=5,
    font_family="sans-serif",
)

# Create x-axis labels - select monthly labels as major labels
x_labels_all = [d.strftime("%b %Y") if i == 0 or d.month != dates[i - 1].month else "" for i, d in enumerate(dates)]
x_labels_major = [label for label in x_labels_all if label]

# Create line chart with interactive features
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-stock-comparison · pygal · pyplots.ai",
    x_title="Date",
    y_title="Rebased Price (Start = 100)",
    show_x_guides=False,
    show_y_guides=True,
    dots_size=3,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,  # 4 columns for 4 stock series (reference line hidden from legend)
    legend_box_size=32,
    x_label_rotation=45,
    truncate_label=-1,
    show_minor_x_labels=False,
    x_labels_major=x_labels_major,
    range=(70, 180),
    margin_bottom=120,
)

# Set x-axis labels
chart.x_labels = x_labels_all

# Create data with custom tooltips for interactivity
data_aapl = [
    {"value": val, "label": f"AAPL | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
    for i, val in enumerate(rebased_aapl.tolist())
]
data_googl = [
    {"value": val, "label": f"GOOGL | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
    for i, val in enumerate(rebased_googl.tolist())
]
data_msft = [
    {"value": val, "label": f"MSFT | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
    for i, val in enumerate(rebased_msft.tolist())
]
data_spy = [
    {"value": val, "label": f"SPY | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
    for i, val in enumerate(rebased_spy.tolist())
]

# Add data series with custom tooltips
chart.add("AAPL", data_aapl)
chart.add("GOOGL", data_googl)
chart.add("MSFT", data_msft)
chart.add("SPY (Benchmark)", data_spy)

# Note: Reference line at 100 is indicated by the horizontal grid line passing through y=100
# This is cleaner than adding a separate series that would clutter the legend

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
