""" pyplots.ai
indicator-rsi: RSI Technical Indicator Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 85/100 | Created: 2026-01-07
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Generate realistic RSI values over 120 trading days
np.random.seed(42)

n_days = 120
lookback = 14

# Generate price changes that produce RSI entering both overbought (>70) and oversold (<30) zones
# Use stronger trending to ensure RSI reaches extreme values
base_changes = np.random.randn(n_days) * 0.8

# Strong uptrend periods (push RSI above 70) - increased magnitude
base_changes[15:32] += 4.0  # Strong bullish phase
base_changes[75:92] += 4.5  # Another strong bullish phase

# Strong downtrend periods (push RSI below 30) - increased magnitude
base_changes[40:57] -= 4.0  # Strong bearish phase
base_changes[100:115] -= 3.5  # Another bearish phase

price_changes = base_changes

# Calculate RSI using exponential moving average
gains = np.where(price_changes > 0, price_changes, 0)
losses = np.where(price_changes < 0, -price_changes, 0)

# Initialize EMA
avg_gain = np.zeros(n_days)
avg_loss = np.zeros(n_days)

# First average
avg_gain[lookback - 1] = np.mean(gains[:lookback])
avg_loss[lookback - 1] = np.mean(losses[:lookback])

# EMA for subsequent values
alpha = 1 / lookback
for i in range(lookback, n_days):
    avg_gain[i] = alpha * gains[i] + (1 - alpha) * avg_gain[i - 1]
    avg_loss[i] = alpha * losses[i] + (1 - alpha) * avg_loss[i - 1]

# Calculate RSI (avoid division by zero)
with np.errstate(divide="ignore", invalid="ignore"):
    rs = np.divide(avg_gain, avg_loss, out=np.full_like(avg_gain, 100.0), where=avg_loss > 0)
rsi = 100 - (100 / (1 + rs))
rsi[:lookback] = 50  # Fill initial values with neutral


# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=(
        "#D04040",  # Overbought line (red)
        "#30A030",  # Oversold line (green)
        "#888888",  # Centerline (gray)
        "#306998",  # RSI line (blue)
    ),
    title_font_size=80,
    label_font_size=52,
    major_label_font_size=46,
    legend_font_size=52,
    value_font_size=40,
    stroke_width=6,
    opacity=0.95,
    opacity_hover=1.0,
)

# Create chart with custom configuration for zone rendering
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="indicator-rsi · pygal · pyplots.ai",
    x_title="Trading Period (120 days, 14-period RSI lookback)",
    y_title="RSI Value (0-100)",
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    range=(0, 100),
    interpolate="cubic",
    legend_at_bottom=True,
    legend_box_size=40,
    margin=60,
    margin_bottom=180,
    show_x_labels=False,
)

# Create RSI data with zone-based coloring approach
# Since pygal doesn't support horizontal bands natively, we'll use secondary value lines
# and visual indication through dashed threshold lines with clear colors

# Add threshold lines (constant values across all days)
overbought_line = [70] * n_days
oversold_line = [30] * n_days
centerline = [50] * n_days

# Add overbought threshold line (red, dashed)
chart.add("Overbought (70)", overbought_line, stroke_style={"width": 5, "dasharray": "20,10"}, show_dots=False)

# Add oversold threshold line (green, dashed)
chart.add("Oversold (30)", oversold_line, stroke_style={"width": 5, "dasharray": "20,10"}, show_dots=False)

# Add centerline (gray, dotted)
chart.add("Centerline (50)", centerline, stroke_style={"width": 3, "dasharray": "10,10"}, show_dots=False)

# Add RSI data last so it appears on top with thicker line
chart.add("RSI (14)", list(rsi), stroke_style={"width": 8}, show_dots=False)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
