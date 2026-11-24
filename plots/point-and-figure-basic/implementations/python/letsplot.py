"""anyplot.ai
point-and-figure-basic: Point and Figure Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: X columns take position 1 (bullish), O columns the red (bearish)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]
DOWN_COLOR = IMPRINT_PALETTE[4]

# Constants
BOX_SIZE = 2.0  # price increment per X or O
REVERSAL = 3  # boxes needed to start a column in the opposite direction

# Columns: set these to your table's column names
DATE = "Date"  # role: date
HIGH = "High price ($)"  # role: high
LOW = "Low price ($)"  # role: low
CLOSE = "Close price ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 300
returns = np.random.normal(0.001, 0.02, n_days)
returns[50:100] += 0.005  # uptrend
returns[150:200] -= 0.004  # downtrend
returns[250:280] += 0.006  # uptrend
close = 100 * np.cumprod(1 + returns)
df = pd.DataFrame(
    {DATE: pd.bdate_range("2024-01-02", periods=n_days), HIGH: close * 1.005, LOW: close * 0.995, CLOSE: close}
)

# Plot: Point and Figure construction from the closing prices
COLUMN = "Column (Reversal Number)"
PRICE = "Price ($)"
SYMBOL = "Signal"
DIRECTION = "Direction"

closes = df[CLOSE].dropna().to_numpy()
current_box = int(closes[0] / BOX_SIZE)  # price level counted in boxes
direction = None
column_idx = 0
pnf_rows = []

for price in closes:
    price_box = int(price / BOX_SIZE)

    if direction is None:
        if price_box > current_box:
            direction = "up"
            for b in range(current_box, price_box + 1):
                pnf_rows.append((column_idx, b * BOX_SIZE, "X", "up"))
            current_box = price_box
        elif price_box < current_box:
            direction = "down"
            for b in range(price_box, current_box + 1):
                pnf_rows.append((column_idx, b * BOX_SIZE, "O", "down"))
            current_box = price_box

    elif direction == "up":
        if price_box > current_box:
            for b in range(current_box + 1, price_box + 1):
                pnf_rows.append((column_idx, b * BOX_SIZE, "X", "up"))
            current_box = price_box
        elif price_box <= current_box - REVERSAL:
            column_idx += 1
            for b in range(price_box, current_box):
                pnf_rows.append((column_idx, b * BOX_SIZE, "O", "down"))
            current_box = price_box
            direction = "down"

    elif direction == "down":
        if price_box < current_box:
            for b in range(price_box, current_box):
                pnf_rows.append((column_idx, b * BOX_SIZE, "O", "down"))
            current_box = price_box
        elif price_box >= current_box + REVERSAL:
            column_idx += 1
            for b in range(current_box + 1, price_box + 1):
                pnf_rows.append((column_idx, b * BOX_SIZE, "X", "up"))
            current_box = price_box
            direction = "up"

pnf = pd.DataFrame(pnf_rows, columns=[COLUMN, PRICE, SYMBOL, DIRECTION])
pnf = pnf.drop_duplicates(subset=[COLUMN, PRICE])

# 45-degree trend lines (one box per column), clipped to the span of the data
low_row = pnf.loc[pnf[PRICE].idxmin()]
high_row = pnf.loc[pnf[PRICE].idxmax()]
last_col = pnf[COLUMN].max()
price_span = pnf[PRICE].max() - pnf[PRICE].min()

# Support rises from the lowest box until it meets the highest price or the last column
support_end = min(last_col, low_row[COLUMN] + price_span / BOX_SIZE)
# Resistance falls from the highest box until it meets the lowest price or the last column
resistance_end = min(last_col, high_row[COLUMN] + price_span / BOX_SIZE)
trend = pd.DataFrame(
    {
        "x": [low_row[COLUMN], high_row[COLUMN]],
        "xend": [support_end, resistance_end],
        "y": [low_row[PRICE], high_row[PRICE]],
        "yend": [
            low_row[PRICE] + BOX_SIZE * (support_end - low_row[COLUMN]),
            high_row[PRICE] - BOX_SIZE * (resistance_end - high_row[COLUMN]),
        ],
    }
)

# Gridlines on box boundaries, labelled every fifth box
first_level = np.floor(pnf[PRICE].min() / (5 * BOX_SIZE)) * 5 * BOX_SIZE
price_breaks = np.arange(first_level, pnf[PRICE].max() + 5 * BOX_SIZE, 5 * BOX_SIZE)

plot = (
    ggplot(pnf, aes(x=COLUMN, y=PRICE, label=SYMBOL, color=DIRECTION))
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=trend,
        color=INK_SOFT,
        linetype="dashed",
        size=0.8,
        inherit_aes=False,
    )
    + geom_text(
        size=12,
        fontface="bold",
        tooltips=layer_tooltips().line(f"Column: @{{{COLUMN}}}").line(f"Price: $@{{{PRICE}}}").line("Signal: @Signal"),
    )
    + scale_color_manual(values={"up": UP_COLOR, "down": DOWN_COLOR})
    + scale_x_continuous(name=COLUMN)
    + scale_y_continuous(name=PRICE, breaks=list(price_breaks))
    + labs(title="point-and-figure-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_position="none",
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
