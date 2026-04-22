""" pyplots.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: pygal 3.1.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-17
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Stock prices with highlighted recession period
np.random.seed(42)
dates = np.arange(2006, 2016, 0.1)  # 10 years of data
# Simulate stock price with trend and volatility
price = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
# Add a dip during recession period (2008-2009)
recession_mask = (dates >= 2008) & (dates < 2010)
price[recession_mask] -= np.linspace(0, 30, recession_mask.sum())
price[dates >= 2010] -= 30
price = price + np.abs(price.min()) + 50  # Keep positive

# Calculate range for spans
y_min = 40
y_max = price.max() + 20

# Custom style with scaled sizes for 4800x2700 output
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#FFD43B", "#D62728", "#306998"),  # Yellow span, Red span, Blue line
    opacity=".25",  # Semi-transparent for span regions
    opacity_hover=".4",
    title_font_size=60,
    label_font_size=36,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=32,
    stroke_width="4",
)

# Create XY chart with fill enabled for span regions
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="span-basic · pygal · pyplots.ai",
    x_title="Year",
    y_title="Price ($)",
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    range=(y_min, y_max),
    xrange=(2005.5, 2016.5),
    fill=True,  # Enable fill for closed polygons
    stroke=True,
    dots_size=0,
)

# Vertical span: Recession Period (2008-2009) - full height rectangle
# Create closed polygon: bottom-left -> top-left -> top-right -> bottom-right -> close
recession_span = [
    (2008, y_min),
    (2008, y_max),
    (2009, y_max),
    (2009, y_min),
    (2008, y_min),  # Close the polygon
]
chart.add("Recession Period", recession_span)

# Horizontal span: Risk Zone (60-80) - full width rectangle
risk_span = [
    (2005.5, 60),
    (2005.5, 80),
    (2016.5, 80),
    (2016.5, 60),
    (2005.5, 60),  # Close the polygon
]
chart.add("Risk Zone", risk_span)

# Main line data (no fill, just stroke)
main_data = [(float(x), float(y)) for x, y in zip(dates, price, strict=True)]
chart.add("Stock Price", main_data, fill=False, stroke=True)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
