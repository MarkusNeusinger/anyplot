""" pyplots.ai
renko-basic: Basic Renko Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, output_file, save


# Generate synthetic stock price data
np.random.seed(42)
n_days = 200
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
returns = np.random.randn(n_days) * 0.02  # Daily returns ~2% std
price = 100 * np.cumprod(1 + returns)  # Geometric random walk

# Build Renko bricks
brick_size = 2.0  # $2 brick size
bricks = []
current_price = price[0]
brick_start = current_price - (current_price % brick_size)  # Round to nearest brick
direction = None  # None, 'up', or 'down'
brick_index = 0

for close in price:
    while True:
        if direction is None:
            # Initial brick - determine direction
            if close >= brick_start + brick_size:
                # First brick is bullish
                bricks.append(
                    {"index": brick_index, "bottom": brick_start, "top": brick_start + brick_size, "direction": "up"}
                )
                brick_start += brick_size
                direction = "up"
                brick_index += 1
            elif close <= brick_start - brick_size:
                # First brick is bearish
                bricks.append(
                    {"index": brick_index, "bottom": brick_start - brick_size, "top": brick_start, "direction": "down"}
                )
                brick_start -= brick_size
                direction = "down"
                brick_index += 1
            else:
                break
        elif direction == "up":
            if close >= brick_start + brick_size:
                # Continue up
                bricks.append(
                    {"index": brick_index, "bottom": brick_start, "top": brick_start + brick_size, "direction": "up"}
                )
                brick_start += brick_size
                brick_index += 1
            elif close <= brick_start - 2 * brick_size:
                # Reversal down (need 2 bricks for reversal)
                bricks.append(
                    {"index": brick_index, "bottom": brick_start - brick_size, "top": brick_start, "direction": "down"}
                )
                brick_start -= brick_size
                direction = "down"
                brick_index += 1
            else:
                break
        else:  # direction == 'down'
            if close <= brick_start - brick_size:
                # Continue down
                bricks.append(
                    {"index": brick_index, "bottom": brick_start - brick_size, "top": brick_start, "direction": "down"}
                )
                brick_start -= brick_size
                brick_index += 1
            elif close >= brick_start + 2 * brick_size:
                # Reversal up (need 2 bricks for reversal)
                bricks.append(
                    {"index": brick_index, "bottom": brick_start, "top": brick_start + brick_size, "direction": "up"}
                )
                brick_start += brick_size
                direction = "up"
                brick_index += 1
            else:
                break

# Prepare data for plotting
brick_df = pd.DataFrame(bricks)
bullish = brick_df[brick_df["direction"] == "up"]
bearish = brick_df[brick_df["direction"] == "down"]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="renko-basic · bokeh · pyplots.ai",
    x_axis_label="Brick Number",
    y_axis_label="Price ($)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Style settings - scaled for 4800x2700 canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Colors
bullish_color = "#2E7D32"  # Green
bearish_color = "#C62828"  # Red

# Brick width (slightly less than 1 to create small gaps)
brick_width = 0.85

# Draw bullish bricks
if len(bullish) > 0:
    bullish_source = ColumnDataSource(
        data={"x": bullish["index"].values, "bottom": bullish["bottom"].values, "top": bullish["top"].values}
    )
    p.vbar(
        x="x",
        width=brick_width,
        bottom="bottom",
        top="top",
        source=bullish_source,
        color=bullish_color,
        line_color="#1B5E20",
        line_width=2,
        legend_label="Bullish",
    )

# Draw bearish bricks
if len(bearish) > 0:
    bearish_source = ColumnDataSource(
        data={"x": bearish["index"].values, "bottom": bearish["bottom"].values, "top": bearish["top"].values}
    )
    p.vbar(
        x="x",
        width=brick_width,
        bottom="bottom",
        top="top",
        source=bearish_source,
        color=bearish_color,
        line_color="#8B0000",
        line_width=2,
        legend_label="Bearish",
    )

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.location = "top_left"
p.legend.label_text_font_size = "24pt"
p.legend.background_fill_alpha = 0.8
p.legend.glyph_height = 30
p.legend.glyph_width = 30

# Background
p.background_fill_color = "#FAFAFA"

# Save outputs
output_file("plot.html", title="Basic Renko Chart")
save(p)
export_png(p, filename="plot.png")
