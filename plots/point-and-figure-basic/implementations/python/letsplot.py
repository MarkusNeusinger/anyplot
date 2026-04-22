""" pyplots.ai
point-and-figure-basic: Point and Figure Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Generate synthetic stock price data
np.random.seed(42)
n_days = 300

# Create realistic price movement with trends
returns = np.random.normal(0.001, 0.02, n_days)
returns[50:100] += 0.005  # Uptrend
returns[150:200] -= 0.004  # Downtrend
returns[250:280] += 0.006  # Uptrend

prices = 100 * np.cumprod(1 + returns)

# Point and Figure parameters
box_size = 2.0  # Each box represents $2
reversal = 3  # 3-box reversal

# Build Point and Figure chart data (inline)
pnf_rows = []  # List of (column_index, price_level, symbol, direction)
current_box = int(prices[0] / box_size) * box_size
direction = None
column_idx = 0

for price in prices:
    price_box = int(price / box_size) * box_size

    if direction is None:
        # First move determines direction
        if price_box > current_box:
            direction = "up"
            for b in range(int(current_box / box_size), int(price_box / box_size) + 1):
                pnf_rows.append((column_idx, b * box_size, "X", "up"))
            current_box = price_box
        elif price_box < current_box:
            direction = "down"
            for b in range(int(price_box / box_size), int(current_box / box_size) + 1):
                pnf_rows.append((column_idx, b * box_size, "O", "down"))
            current_box = price_box

    elif direction == "up":
        if price_box > current_box:
            # Continue up
            for b in range(int(current_box / box_size) + 1, int(price_box / box_size) + 1):
                pnf_rows.append((column_idx, b * box_size, "X", "up"))
            current_box = price_box
        elif price_box <= current_box - reversal * box_size:
            # Reversal down
            column_idx += 1
            for b in range(int(price_box / box_size), int(current_box / box_size)):
                pnf_rows.append((column_idx, b * box_size, "O", "down"))
            current_box = price_box
            direction = "down"

    elif direction == "down":
        if price_box < current_box:
            # Continue down
            for b in range(int(price_box / box_size), int(current_box / box_size)):
                pnf_rows.append((column_idx, b * box_size, "O", "down"))
            current_box = price_box
        elif price_box >= current_box + reversal * box_size:
            # Reversal up
            column_idx += 1
            for b in range(int(current_box / box_size) + 1, int(price_box / box_size) + 1):
                pnf_rows.append((column_idx, b * box_size, "X", "up"))
            current_box = price_box
            direction = "up"

# Convert to DataFrame for plotting
df_pnf = pd.DataFrame(pnf_rows, columns=["column", "price", "symbol", "direction"])
df_pnf = df_pnf.drop_duplicates(subset=["column", "price"])

# Create the plot using geom_text to display X and O symbols
plot = (
    ggplot(df_pnf, aes(x="column", y="price", label="symbol", color="direction"))
    + geom_text(size=16, fontface="bold")
    + scale_color_manual(values={"up": "#16a34a", "down": "#dc2626"})
    + scale_x_continuous(name="Column (Reversal Number)")
    + scale_y_continuous(name="Price ($)")
    + labs(title="point-and-figure-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
