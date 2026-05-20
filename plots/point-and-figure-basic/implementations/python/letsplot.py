""" anyplot.ai
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
    geom_abline,
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

# Data
np.random.seed(42)
n_days = 300

returns = np.random.normal(0.001, 0.02, n_days)
returns[50:100] += 0.005  # Uptrend
returns[150:200] -= 0.004  # Downtrend
returns[250:280] += 0.006  # Uptrend

prices = 100 * np.cumprod(1 + returns)

# Point and Figure algorithm (box_size=$2, 3-box reversal)
box_size = 2.0
reversal = 3

pnf_rows = []
current_box = int(prices[0] / box_size) * box_size
direction = None
column_idx = 0

for price in prices:
    price_box = int(price / box_size) * box_size

    if direction is None:
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
            for b in range(int(current_box / box_size) + 1, int(price_box / box_size) + 1):
                pnf_rows.append((column_idx, b * box_size, "X", "up"))
            current_box = price_box
        elif price_box <= current_box - reversal * box_size:
            column_idx += 1
            for b in range(int(price_box / box_size), int(current_box / box_size)):
                pnf_rows.append((column_idx, b * box_size, "O", "down"))
            current_box = price_box
            direction = "down"

    elif direction == "down":
        if price_box < current_box:
            for b in range(int(price_box / box_size), int(current_box / box_size)):
                pnf_rows.append((column_idx, b * box_size, "O", "down"))
            current_box = price_box
        elif price_box >= current_box + reversal * box_size:
            column_idx += 1
            for b in range(int(current_box / box_size) + 1, int(price_box / box_size) + 1):
                pnf_rows.append((column_idx, b * box_size, "X", "up"))
            current_box = price_box
            direction = "up"

df_pnf = pd.DataFrame(pnf_rows, columns=["column", "price", "symbol", "direction"])
df_pnf = df_pnf.drop_duplicates(subset=["column", "price"])

# 45-degree trend lines: 1 box per column in chart coordinates
min_idx = df_pnf["price"].idxmin()
min_price_val = df_pnf.loc[min_idx, "price"]
min_col_val = df_pnf.loc[min_idx, "column"]

max_idx = df_pnf["price"].idxmax()
max_price_val = df_pnf.loc[max_idx, "price"]
max_col_val = df_pnf.loc[max_idx, "column"]

# Ascending support: anchored at chart minimum, slope = +box_size
support_intercept = min_price_val - box_size * min_col_val
# Descending resistance: anchored at chart maximum, slope = -box_size
resistance_intercept = max_price_val + box_size * max_col_val

# Plot
plot = (
    ggplot(df_pnf, aes(x="column", y="price", label="symbol", color="direction"))
    + geom_abline(slope=box_size, intercept=support_intercept, color=INK_SOFT, linetype="dashed", size=0.8)
    + geom_abline(slope=-box_size, intercept=resistance_intercept, color=INK_SOFT, linetype="dashed", size=0.8)
    + geom_text(
        size=12,
        fontface="bold",
        tooltips=layer_tooltips().line("Column: @column").line("Price: $@price").line("Signal: @symbol"),
    )
    + scale_color_manual(values={"up": "#009E73", "down": "#D55E00"})
    + scale_x_continuous(name="Column (Reversal Number)")
    + scale_y_continuous(name="Price ($)")
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
