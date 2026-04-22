""" pyplots.ai
point-and-figure-basic: Point and Figure Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Generate synthetic stock price data
np.random.seed(42)
n_days = 300

# Create trending price movement with volatility
returns = np.random.normal(0.001, 0.02, n_days)
# Add some trend periods
returns[50:100] += 0.005  # Uptrend
returns[120:160] -= 0.008  # Downtrend
returns[180:250] += 0.004  # Uptrend

price = 100 * np.cumprod(1 + returns)
close = price

# Point and Figure parameters
box_size = 2.0  # Each box represents $2 price movement
reversal = 3  # 3-box reversal

# Build Point and Figure data
pf_data = []  # List of (column_index, price_level, direction)
current_direction = None  # 'X' (up) or 'O' (down)
current_column = 0

# Initialize with first price (quantize to box level)
start_box = int(np.floor(close[0] / box_size))
current_high_box = start_box
current_low_box = start_box

for i in range(1, len(close)):
    current_box = int(np.floor(close[i] / box_size))

    if current_direction is None:
        # Determine initial direction
        if current_box > current_high_box:
            current_direction = "X"
            for b in range(current_low_box, current_box + 1):
                pf_data.append((current_column, b * box_size, "X"))
            current_high_box = current_box
        elif current_box < current_low_box:
            current_direction = "O"
            for b in range(current_box, current_high_box + 1):
                pf_data.append((current_column, b * box_size, "O"))
            current_low_box = current_box

    elif current_direction == "X":
        # Currently in an X (up) column
        if current_box > current_high_box:
            # Continue up
            for b in range(current_high_box + 1, current_box + 1):
                pf_data.append((current_column, b * box_size, "X"))
            current_high_box = current_box
        elif current_box <= current_high_box - reversal:
            # Reversal - start O column
            current_column += 1
            current_direction = "O"
            current_low_box = current_box
            for b in range(current_box, current_high_box):
                pf_data.append((current_column, b * box_size, "O"))

    elif current_direction == "O":
        # Currently in an O (down) column
        if current_box < current_low_box:
            # Continue down
            for b in range(current_box, current_low_box):
                pf_data.append((current_column, b * box_size, "O"))
            current_low_box = current_box
        elif current_box >= current_low_box + reversal:
            # Reversal - start X column
            current_column += 1
            current_direction = "X"
            current_high_box = current_box
            for b in range(current_low_box + 1, current_box + 1):
                pf_data.append((current_column, b * box_size, "X"))

# Create DataFrame for plotting
df = pd.DataFrame(pf_data, columns=["column", "price", "symbol"])

# Map symbols to display characters
df["display"] = df["symbol"].map({"X": "X", "O": "O"})

# Create plot
plot = (
    ggplot(df, aes(x="column", y="price", color="symbol", label="display"))
    + geom_text(size=12, fontweight="bold")
    + scale_color_manual(
        values={"X": "#2E8B57", "O": "#DC143C"},  # Green for X, Red for O
        labels={"X": "Rising (X)", "O": "Falling (O)"},
    )
    + scale_y_continuous(
        breaks=np.arange(
            int(df["price"].min() / box_size) * box_size, int(df["price"].max() / box_size + 2) * box_size, box_size * 2
        )
    )
    + labs(
        x="Column (Reversals)",
        y="Price Level ($)",
        title="point-and-figure-basic · plotnine · pyplots.ai",
        color="Direction",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#cccccc", size=0.5, alpha=0.5),
    )
)

plot.save("plot.png", dpi=300)
