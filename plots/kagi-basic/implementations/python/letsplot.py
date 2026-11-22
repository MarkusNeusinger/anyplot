"""anyplot.ai
kagi-basic: Basic Kagi Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
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
    ggplot,
    ggsize,
    labs,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#E6E4DB" if THEME == "light" else "#2C2C28"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Semantic Kagi colors: green for yang (rising), red for yin (falling)
YANG_COLOR = IMPRINT_PALETTE[0]
YIN_COLOR = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close

# Constants
REVERSAL = 0.04  # a Kagi line turns only after a 4% move against the current direction

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 200
returns = np.random.normal(0.001, 0.02, n_days)
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=n_days), CLOSE: 100 * np.cumprod(1 + returns)})

# Plot: reads only df and the constants above
prices = df[CLOSE].to_numpy()

# Build Kagi segments: vertical runs joined by horizontal shoulders and waists
segments = []
direction = 1  # 1 = up, -1 = down
last_high = prices[0]
last_low = prices[0]
current_price = prices[0]
x_idx = 0

for price in prices[1:]:
    if direction == 1:
        if price > last_high:
            last_high = price
            current_price = price
        elif price <= current_price * (1 - REVERSAL):
            segments.append({"x1": x_idx, "y1": last_low, "x2": x_idx, "y2": last_high, "line_type": "yang"})
            x_idx += 1
            segments.append({"x1": x_idx - 1, "y1": last_high, "x2": x_idx, "y2": last_high, "line_type": "yang"})
            direction = -1
            last_low = price
            current_price = price
    else:
        if price < last_low:
            last_low = price
            current_price = price
        elif price >= current_price * (1 + REVERSAL):
            segments.append({"x1": x_idx, "y1": last_high, "x2": x_idx, "y2": last_low, "line_type": "yin"})
            x_idx += 1
            segments.append({"x1": x_idx - 1, "y1": last_low, "x2": x_idx, "y2": last_low, "line_type": "yin"})
            direction = 1
            last_high = price
            current_price = price

# Last, still open segment
if direction == 1:
    segments.append({"x1": x_idx, "y1": last_low, "x2": x_idx, "y2": current_price, "line_type": "yang"})
else:
    segments.append({"x1": x_idx, "y1": last_high, "x2": x_idx, "y2": current_price, "line_type": "yin"})

kagi_df = pd.DataFrame(segments)
yang_df = kagi_df[kagi_df["line_type"] == "yang"]
yin_df = kagi_df[kagi_df["line_type"] == "yin"]

# Create the plot
plot = (
    ggplot()
    + geom_segment(
        aes(x="x1", y="y1", xend="x2", yend="y2"),
        data=yang_df,
        color=YANG_COLOR,
        size=2.5,  # Thick line for yang
    )
    + geom_segment(
        aes(x="x1", y="y1", xend="x2", yend="y2"),
        data=yin_df,
        color=YIN_COLOR,
        size=0.9,  # Thin line for yin
    )
    + labs(title="kagi-basic · python · letsplot · anyplot.ai", x="Line index", y=CLOSE)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID_COLOR, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
    )
    + ggsize(800, 450)
)

# Save as PNG (scaled 4x for 3200x1800 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)

# Save as HTML for interactive viewing
ggsave(plot, f"plot-{THEME}.html", path=".")
