"""anyplot.ai
line-stepwise: Step Line Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-13
"""

import os

import pandas as pd
from plotnine import aes, element_line, element_rect, element_text, geom_step, ggplot, labs, theme, theme_minimal


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first position is the single series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DAY = "Day of month"  # role: x
BALANCE = "Account balance (USD)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("balance.csv")
# Checking account balance: it changes only when a transaction posts, at irregular days
df = pd.DataFrame(
    {
        DAY: [1, 2, 5, 6, 9, 12, 13, 15, 16, 19, 21, 22, 26, 28, 30],
        BALANCE: [1850, 1790, 1330, 1415, 1280, 1195, 1020, 3560, 2740, 2655, 2310, 2395, 1630, 1485, 1485],
    }
)

# Plot
title = "line-stepwise · python · plotnine · anyplot.ai"
anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.12),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.04),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=12, color=INK),
)

plot = (
    ggplot(df, aes(x=DAY, y=BALANCE))
    + geom_step(color=IMPRINT_PALETTE[0], size=1.2, direction="hv")
    + labs(title=title)
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
