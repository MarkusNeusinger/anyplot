"""anyplot.ai
renko-basic: Basic Renko Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")
BULLISH = IMPRINT_PALETTE[0]  # brand green: price moved up
BEARISH = IMPRINT_PALETTE[4]  # Imprint red: price moved down

# Constants
BRICK_SIZE = 2.0  # price move that draws one brick
MAX_BRICKS = 40  # bricks shown
LABEL_EVERY = 5  # one x label per this many bricks

DATE = "Date"  # role: date
CLOSE = "Price ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 180
returns = np.random.normal(0.001, 0.02, n_days)
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=n_days), CLOSE: 100 * np.cumprod(1 + returns)})

# Plot
prices = df[CLOSE].to_numpy()

# Build Renko bricks from the closing prices
bricks = []
current_brick_price = round(prices[0] / BRICK_SIZE) * BRICK_SIZE
direction = None

for price in prices:
    while True:
        if direction is None:
            if price >= current_brick_price + BRICK_SIZE:
                bricks.append({"price": current_brick_price, "direction": "up"})
                current_brick_price += BRICK_SIZE
                direction = "up"
            elif price <= current_brick_price - BRICK_SIZE:
                bricks.append({"price": current_brick_price - BRICK_SIZE, "direction": "down"})
                current_brick_price -= BRICK_SIZE
                direction = "down"
            else:
                break
        elif direction == "up":
            if price >= current_brick_price + BRICK_SIZE:
                bricks.append({"price": current_brick_price, "direction": "up"})
                current_brick_price += BRICK_SIZE
            elif price <= current_brick_price - 2 * BRICK_SIZE:
                current_brick_price -= BRICK_SIZE
                bricks.append({"price": current_brick_price - BRICK_SIZE, "direction": "down"})
                current_brick_price -= BRICK_SIZE
                direction = "down"
            else:
                break
        else:
            if price <= current_brick_price - BRICK_SIZE:
                bricks.append({"price": current_brick_price - BRICK_SIZE, "direction": "down"})
                current_brick_price -= BRICK_SIZE
            elif price >= current_brick_price + 2 * BRICK_SIZE:
                current_brick_price += BRICK_SIZE
                bricks.append({"price": current_brick_price, "direction": "up"})
                current_brick_price += BRICK_SIZE
                direction = "up"
            else:
                break

bricks = bricks[:MAX_BRICKS]

# Price range
min_price = min(b["price"] for b in bricks)
max_price = max(b["price"] for b in bricks) + BRICK_SIZE
y_min = min_price - BRICK_SIZE
y_max = max_price + BRICK_SIZE

# Style: spacer layer takes the page color so only the bricks show
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(PAGE_BG, BULLISH, BEARISH),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.StackedBar(
    width=3200,
    height=1800,
    title="renko-basic · python · pygal · anyplot.ai",
    x_title="Brick index",
    y_title=CLOSE,
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    spacing=6,
)

chart.x_labels = [str(i) if i % LABEL_EVERY == 0 else "" for i in range(len(bricks))]
chart.y_labels = [f"${y}" for y in range(int(y_min), int(y_max) + 1, int(BRICK_SIZE * 2))]

# Stacked layers: invisible spacer lifts each brick to its price level
spacer_values = [brick["price"] - y_min for brick in bricks]
up_values = [BRICK_SIZE if brick["direction"] == "up" else None for brick in bricks]
down_values = [BRICK_SIZE if brick["direction"] == "down" else None for brick in bricks]

chart.add("", spacer_values)
chart.add("Bullish (up)", up_values)
chart.add("Bearish (down)", down_values)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
