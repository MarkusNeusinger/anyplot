"""anyplot.ai
depth-order-book: Order Book Depth Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 85/100 | Created: 2026-06-15
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
    geom_area,
    geom_vline,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — semantic exception: bid=green (buy/gain), ask=red (sell/loss)
BID_COLOR = "#009E73"  # Imprint position 1 — green for bids
ASK_COLOR = "#AE3030"  # Imprint position 5 — red for asks (semantic: loss/sell)

# Theme-adaptive fill alpha: higher in dark mode keeps ask area legible on near-black bg
FILL_ALPHA = 0.30 if THEME == "light" else 0.42

# Data — synthetic BTC/USD order book snapshot, mid price ~60,000
np.random.seed(42)

MID_PRICE = 60_000.0
SPREAD = 10.0  # $10 bid-ask spread
N_LEVELS = 50  # price levels per side
TICK = 10.0  # price increment per level

best_bid = MID_PRICE - SPREAD / 2
bid_prices = best_bid - np.arange(N_LEVELS) * TICK

best_ask = MID_PRICE + SPREAD / 2
ask_prices = best_ask + np.arange(N_LEVELS) * TICK

# Quantities grow away from mid price; add liquidity walls for realism
bid_quantities = np.random.exponential(scale=1.5, size=N_LEVELS) + 0.3 * np.arange(N_LEVELS) / N_LEVELS * 10
ask_quantities = np.random.exponential(scale=1.5, size=N_LEVELS) + 0.3 * np.arange(N_LEVELS) / N_LEVELS * 10
bid_quantities[12] += 18.0
ask_quantities[8] += 14.0

bid_cumulative = np.cumsum(bid_quantities)
ask_cumulative = np.cumsum(ask_quantities)

# Build staircase (x ascending) by interleaving each price with the next price
# at the same y, creating horizontal steps before y jumps at the next level.
# Pattern: (p[i], c[i]), (p[i+1], c[i]), (p[i+1], c[i+1]), ...

# Asks: prices already ascending (60005 → 60495)
ask_x = np.empty(2 * N_LEVELS - 1)
ask_x[0::2] = ask_prices
ask_x[1::2] = ask_prices[1:]
ask_y = np.empty(2 * N_LEVELS - 1)
ask_y[0::2] = ask_cumulative
ask_y[1::2] = ask_cumulative[:-1]

# Bids: prices are descending (59995 → 59505) — reverse to ascending first
bid_prices_asc = bid_prices[::-1]
bid_cums_asc = bid_cumulative[::-1]
bid_x = np.empty(2 * N_LEVELS - 1)
bid_x[0::2] = bid_prices_asc
bid_x[1::2] = bid_prices_asc[1:]
bid_y = np.empty(2 * N_LEVELS - 1)
bid_y[0::2] = bid_cums_asc
bid_y[1::2] = bid_cums_asc[:-1]

# "side" column maps fill aesthetic to legend entries
bid_df = pd.DataFrame({"price": bid_x, "cum_qty": bid_y, "side": "Bids"})
ask_df = pd.DataFrame({"price": ask_x, "cum_qty": ask_y, "side": "Asks"})

# Title font scaling
title = "depth-order-book · python · letsplot · anyplot.ai"
default_title_size = 16
n_chars = len(title)
title_size = round(default_title_size * 67 / n_chars) if n_chars > 67 else default_title_size
title_size = max(title_size, 11)

mid_label = "BTC/USD — Mid: $60,000  |  Spread: $10"

# Interactive tooltips for HTML export — letsplot-specific feature
bid_tooltip = layer_tooltips().line("Bids").line("Price|@{price}").line("Cum. Vol.|@{cum_qty} BTC")
ask_tooltip = layer_tooltips().line("Asks").line("Price|@{price}").line("Cum. Vol.|@{cum_qty} BTC")

# anyplot theme — panel_border=blank + axis_line gives L-shaped frame (top/right removed)
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_line(color=RULE, size=0.3),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=title_size),
    plot_subtitle=element_text(color=INK_MUTED, size=10),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_blank(),
)

# Plot — fill mapped to "side" drives the legend; fixed color keeps outlines solid
plot = (
    ggplot()
    + geom_area(
        mapping=aes(x="price", y="cum_qty", fill="side"),
        data=bid_df,
        color=BID_COLOR,
        alpha=FILL_ALPHA,
        size=0.8,
        tooltips=bid_tooltip,
    )
    + geom_area(
        mapping=aes(x="price", y="cum_qty", fill="side"),
        data=ask_df,
        color=ASK_COLOR,
        alpha=FILL_ALPHA,
        size=0.8,
        tooltips=ask_tooltip,
    )
    + geom_vline(xintercept=MID_PRICE, color=INK_MUTED, size=0.6, linetype="dashed")
    + scale_fill_manual(values={"Bids": BID_COLOR, "Asks": ASK_COLOR}, breaks=["Bids", "Asks"])
    + scale_x_continuous(name="Price (USD)")
    + scale_y_continuous(name="Cumulative Volume (BTC)", limits=[0, None])
    + labs(title=title, subtitle=mid_label)
    + anyplot_theme
    + ggsize(800, 450)
)

# Save — use path="." so files land in the working directory, not lets-plot-images/
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
