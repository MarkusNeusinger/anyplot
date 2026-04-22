""" pyplots.ai
drawdown-basic: Drawdown Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Data - Generate synthetic portfolio value data (2 years of daily data)
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=500, freq="D")
returns = np.random.normal(0.0003, 0.018, len(dates))
price = 100 * np.cumprod(1 + returns)

# Calculate drawdown as percentage decline from running maximum
running_max = np.maximum.accumulate(price)
drawdown = (price - running_max) / running_max * 100

# Find maximum drawdown info
max_dd_idx = np.argmin(drawdown)
max_dd_value = drawdown[max_dd_idx]
max_dd_date = dates[max_dd_idx].strftime("%Y-%m-%d")

# Custom style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#cc3333",),  # Red for drawdown
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
)

# Create line chart with fill for drawdown visualization
chart = pygal.Line(
    width=4800,
    height=2700,
    title="drawdown-basic · pygal · pyplots.ai",
    x_title="Date",
    y_title="Drawdown (%)",
    style=custom_style,
    show_dots=False,
    stroke_style={"width": 4},
    fill=True,
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=45,
    legend_at_bottom=True,
    truncate_legend=-1,
    range=(min(drawdown) * 1.1, 5),  # Set y-axis range (drawdown is negative)
)

# Set x-axis labels (show every ~60 days for readability)
x_labels = []
for i, d in enumerate(dates):
    if i % 60 == 0:
        x_labels.append(d.strftime("%Y-%m"))
    else:
        x_labels.append("")
chart.x_labels = x_labels

# Add drawdown series with max drawdown in legend
chart.add(f"Drawdown (Max: {max_dd_value:.1f}% on {max_dd_date})", list(drawdown))

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
