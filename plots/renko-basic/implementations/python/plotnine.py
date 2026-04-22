""" pyplots.ai
renko-basic: Basic Renko Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_rect, ggplot, labs, scale_fill_manual, theme, theme_minimal


# Data - Generate stock price data
np.random.seed(42)
n_days = 250
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
returns = np.random.normal(0.0005, 0.018, n_days)
prices = 100 * np.cumprod(1 + returns)
price_data = pd.DataFrame({"date": dates, "close": prices})

# Renko brick calculation
brick_size = 2.0  # $2 brick size
bricks = []
current_price = price_data["close"].iloc[0]
brick_start = (current_price // brick_size) * brick_size
direction = None  # None initially, then 'up' or 'down'

for close_price in price_data["close"]:
    while True:
        if direction is None:
            # First brick - determine initial direction
            if close_price >= brick_start + brick_size:
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start,
                        "top": brick_start + brick_size,
                        "direction": "up",
                    }
                )
                brick_start += brick_size
                direction = "up"
            elif close_price <= brick_start - brick_size:
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start - brick_size,
                        "top": brick_start,
                        "direction": "down",
                    }
                )
                brick_start -= brick_size
                direction = "down"
            else:
                break
        elif direction == "up":
            if close_price >= brick_start + brick_size:
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start,
                        "top": brick_start + brick_size,
                        "direction": "up",
                    }
                )
                brick_start += brick_size
            elif close_price <= brick_start - 2 * brick_size:
                # Reversal requires 2x brick size
                brick_start -= brick_size
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start - brick_size,
                        "top": brick_start,
                        "direction": "down",
                    }
                )
                brick_start -= brick_size
                direction = "down"
            else:
                break
        else:  # direction == 'down'
            if close_price <= brick_start - brick_size:
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start - brick_size,
                        "top": brick_start,
                        "direction": "down",
                    }
                )
                brick_start -= brick_size
            elif close_price >= brick_start + 2 * brick_size:
                # Reversal requires 2x brick size
                brick_start += brick_size
                bricks.append(
                    {
                        "brick_num": len(bricks),
                        "bottom": brick_start,
                        "top": brick_start + brick_size,
                        "direction": "up",
                    }
                )
                brick_start += brick_size
                direction = "up"
            else:
                break

brick_df = pd.DataFrame(bricks)

# Create rectangle coordinates for geom_rect
brick_df["xmin"] = brick_df["brick_num"] + 0.1
brick_df["xmax"] = brick_df["brick_num"] + 0.9
brick_df["ymin"] = brick_df["bottom"]
brick_df["ymax"] = brick_df["top"]

# Plot
plot = (
    ggplot(brick_df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="direction"))
    + geom_rect(color="#333333", size=0.3)
    + scale_fill_manual(values={"up": "#26A69A", "down": "#EF5350"}, labels={"up": "Bullish", "down": "Bearish"})
    + labs(x="Brick Index", y="Price ($)", title="renko-basic · plotnine · pyplots.ai", fill="Direction")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        panel_grid_major=element_line(color="#E0E0E0", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#E0E0E0", size=0.3, alpha=0.2),
    )
)

plot.save("plot.png", dpi=300, width=16, height=9)
