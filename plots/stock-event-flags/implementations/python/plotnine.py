"""anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-27
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_label,
    geom_line,
    geom_point,
    geom_segment,
    geom_smooth,
    ggplot,
    guides,
    labs,
    scale_color_manual,
    scale_shape_manual,
    scale_size_manual,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MARKER_SHAPES = ["s", "D", "^", "o", "v", "P", "X", "*"]  # one per event type, in the data's order

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Stock price ($)"  # role: close
EVENT_DATE = "Event date"  # role: event_date
EVENT_TYPE = "Event type"  # role: event_type
EVENT_LABEL = "Event label"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
# One row per trading day; the event columns are filled only on days that carry an event.
np.random.seed(42)
n_days = 180
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.018, n_days)
close = 150 * np.cumprod(1 + returns)
# 2:1 split adjustment: halve prices from the day after the split effective date
close[dates > pd.Timestamp("2024-05-20")] /= 2

events = [
    ("2024-01-25", "Earnings", "Q4 Beat"),
    ("2024-02-15", "Dividend", "Div $0.50"),
    ("2024-04-02", "News", "New Product"),
    ("2024-04-25", "Earnings", "Q1 Miss"),
    ("2024-05-20", "Split", "2:1 Split"),
    ("2024-06-10", "Dividend", "Div $0.55"),
    ("2024-07-25", "Earnings", "Q2 Beat"),
    ("2024-08-15", "News", "Partnership"),
]
days = pd.DataFrame({DATE: dates, CLOSE: close})
ev = pd.DataFrame(events, columns=[EVENT_DATE, EVENT_TYPE, EVENT_LABEL])
ev[EVENT_DATE] = pd.to_datetime(ev[EVENT_DATE])
# snap each event to its nearest trading day
ev[DATE] = [days[DATE].iloc[(days[DATE] - day).abs().argmin()] for day in ev[EVENT_DATE]]
ev[EVENT_DATE] = ev[DATE]
df = days.merge(ev, on=DATE, how="left")

# Plot: reads only df and the constants above
FLAG_Y = "flag_y"
price_range = df[CLOSE].max() - df[CLOSE].min()
flags = df.dropna(subset=[EVENT_TYPE]).reset_index(drop=True)
types = flags[EVENT_TYPE].unique().tolist()
color_map = {t: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, t in enumerate(types)}
shape_map = {t: MARKER_SHAPES[i % len(MARKER_SHAPES)] for i, t in enumerate(types)}
# The most frequent event type is the main catalyst and gets the larger marker
main_type = flags[EVENT_TYPE].value_counts().idxmax()
size_map = {t: 5 if t == main_type else 3 for t in types}

# Alternate flags above/below the price so they never sit on the line
steps = np.arange(len(flags))
side = np.where(steps % 2 == 0, 1, -1)
flags[FLAG_Y] = flags[CLOSE] + side * price_range * (0.15 + (steps % 3) * 0.08)

plot = (
    ggplot()
    + geom_line(data=df, mapping=aes(x=DATE, y=CLOSE), color=INK_SOFT, size=1.0, alpha=0.9)
    + geom_smooth(
        data=df,
        mapping=aes(x=DATE, y=CLOSE),
        method="lowess",
        color=IMPRINT_PALETTE[0],
        fill=IMPRINT_PALETTE[0],
        size=0.7,
        alpha=0.1,
    )
    + geom_segment(
        data=flags,
        mapping=aes(x=EVENT_DATE, xend=EVENT_DATE, y=CLOSE, yend=FLAG_Y, color=EVENT_TYPE),
        linetype="dashed",
        size=0.7,
    )
    + geom_point(
        data=flags,
        mapping=aes(x=EVENT_DATE, y=FLAG_Y, color=EVENT_TYPE, shape=EVENT_TYPE, size=EVENT_TYPE),
        fill=ELEVATED_BG,
        stroke=1.5,
    )
    + geom_label(
        data=flags[flags[FLAG_Y] > flags[CLOSE]],
        mapping=aes(x=EVENT_DATE, y=FLAG_Y, label=EVENT_LABEL, color=EVENT_TYPE),
        size=5.5,
        ha="center",
        va="bottom",
        nudge_y=price_range * 0.05,
        fontweight="bold",
        fill=PAGE_BG,
        label_size=0,
        boxstyle="square,pad=0.1",
        show_legend=False,
    )
    + geom_label(
        data=flags[flags[FLAG_Y] < flags[CLOSE]],
        mapping=aes(x=EVENT_DATE, y=FLAG_Y, label=EVENT_LABEL, color=EVENT_TYPE),
        size=5.5,
        ha="center",
        va="top",
        nudge_y=-price_range * 0.05,
        fontweight="bold",
        fill=PAGE_BG,
        label_size=0,
        boxstyle="square,pad=0.1",
        show_legend=False,
    )
    + scale_y_continuous(limits=(flags[FLAG_Y].min() - price_range * 0.12, flags[FLAG_Y].max() + price_range * 0.12))
    + scale_color_manual(values=color_map, limits=types)
    + scale_shape_manual(values=shape_map, limits=types)
    + scale_size_manual(values=size_map, limits=types)
    + guides(size="none")
    + scale_x_datetime(date_labels="%b %Y", date_breaks="1 month")
    + labs(title="stock-event-flags · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        axis_text_x=element_text(rotation=45, ha="right", color=INK_SOFT, size=8),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=12, weight="bold"),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=10, weight="bold"),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
