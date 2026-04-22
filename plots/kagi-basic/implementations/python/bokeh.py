""" pyplots.ai
kagi-basic: Basic Kagi Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import Legend, LegendItem
from bokeh.plotting import figure


# Generate synthetic stock price data
np.random.seed(42)
n_days = 250

# Simulate a stock price with trends
base_price = 100.0
returns = np.random.normal(0.001, 0.02, n_days)  # Daily returns
# Add some trending periods
returns[20:60] += 0.003  # Uptrend
returns[80:120] -= 0.004  # Downtrend
returns[150:200] += 0.002  # Uptrend
prices = base_price * np.cumprod(1 + returns)

# Kagi chart algorithm
reversal_pct = 0.04  # 4% reversal threshold

# Start with first price
current_price = prices[0]
direction = 1  # 1 for up, -1 for down
is_yang = True  # Start as yang (thick)
line_index = 0
last_high = prices[0]
last_low = prices[0]

# Store kagi line segments: (x1, y1, x2, y2, is_yang)
segments = []

for i in range(1, len(prices)):
    price = prices[i]
    reversal_amount = current_price * reversal_pct

    if direction == 1:  # Currently going up
        if price > current_price:
            # Continue upward - extend vertical line
            if price > last_high:
                is_yang = True  # Becomes yang when exceeds previous high
            last_high = max(last_high, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price
        elif current_price - price >= reversal_amount:
            # Reversal down - draw horizontal shoulder
            segments.append((line_index, current_price, line_index + 1, current_price, is_yang))
            line_index += 1
            direction = -1
            if price < last_low:
                is_yang = False  # Becomes yin when falls below previous low
            last_low = min(last_low, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price
    else:  # Currently going down
        if price < current_price:
            # Continue downward - extend vertical line
            if price < last_low:
                is_yang = False  # Becomes yin when falls below previous low
            last_low = min(last_low, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price
        elif price - current_price >= reversal_amount:
            # Reversal up - draw horizontal waist
            segments.append((line_index, current_price, line_index + 1, current_price, is_yang))
            line_index += 1
            direction = 1
            if price > last_high:
                is_yang = True  # Becomes yang when exceeds previous high
            last_high = max(last_high, price)
            segments.append((line_index, current_price, line_index, price, is_yang))
            current_price = price

# Prepare data for bokeh multi_line
xs_yang, ys_yang = [], []
xs_yin, ys_yin = [], []

for seg in segments:
    x1, y1, x2, y2, yang = seg
    if yang:
        xs_yang.append([x1, x2])
        ys_yang.append([y1, y2])
    else:
        xs_yin.append([x1, x2])
        ys_yin.append([y1, y2])

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="kagi-basic · bokeh · pyplots.ai",
    x_axis_label="Line Index",
    y_axis_label="Price ($)",
)

# Plot kagi lines - yang (thick blue) and yin (thin red) separately for legend
yang_renderer = p.multi_line(xs=xs_yang, ys=ys_yang, line_color="#306998", line_width=8)

yin_renderer = p.multi_line(xs=xs_yin, ys=ys_yin, line_color="#D62728", line_width=3)

# Styling - scaled for 4800x2700 canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

p.background_fill_color = "#FAFAFA"

# Add legend
legend = Legend(
    items=[
        LegendItem(label="Yang (Uptrend)", renderers=[yang_renderer]),
        LegendItem(label="Yin (Downtrend)", renderers=[yin_renderer]),
    ],
    location="top_left",
    label_text_font_size="24pt",
)

p.add_layout(legend)
p.legend.background_fill_alpha = 0.8

# Save
export_png(p, filename="plot.png")
