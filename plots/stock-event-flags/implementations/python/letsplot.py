"""anyplot.ai
stock-event-flags: Stock Chart with Event Flags
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-27
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
    geom_line,
    geom_point,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_shape_manual,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"  # INK at 15 %

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Semantic Imprint colors and marker shapes per event type (shapes back the colors up for color-blind readers)
EVENT_COLORS = {
    "Earnings": IMPRINT_PALETTE[2],
    "Dividend": IMPRINT_PALETTE[0],
    "News": IMPRINT_PALETTE[3],
    "Split": IMPRINT_PALETTE[4],
}
EVENT_SHAPES = {"Earnings": 18, "Dividend": 16, "News": 17, "Split": 15}
HOLIDAY_SEASON = ("2023-11-24", "2023-12-26")  # Black Friday to the day after Christmas, the extended event

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close ($)"  # role: close
EVENT_DATE = "Event date"  # role: event_date
EVENT_TYPE = "Event type"  # role: event_type
EVENT_LABEL = "Event label"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
# One row per trading day; the event columns are filled only on the days an event falls on
rng = np.random.default_rng(7)
dates = pd.date_range(start="2023-09-01", periods=170, freq="B")
daily_returns = rng.normal(0.0004, 0.014, len(dates))
event_calendar = {
    "2023-09-14": ("Dividend", "Div $0.50"),
    "2023-10-12": ("News", "Comp Sales Up"),
    "2023-11-16": ("Earnings", "Q3 Beat"),
    "2023-11-24": ("News", "Black Friday"),
    "2023-12-14": ("Dividend", "Div $0.50"),
    "2024-01-11": ("News", "Holiday Warning"),
    "2024-02-29": ("Earnings", "Q4 Miss"),
    "2024-03-14": ("Dividend", "Div $0.55"),
    "2024-04-04": ("Split", "3:1 Split"),
}
jump_by_type = {"Earnings": 0.04, "News": 0.025, "Dividend": 0.0, "Split": 0.0}
for day, (kind, _) in event_calendar.items():
    sign = -1 if day in ("2024-01-11", "2024-02-29") else 1
    daily_returns[dates.get_loc(pd.Timestamp(day))] += sign * jump_by_type[kind]
df = pd.DataFrame({DATE: dates, CLOSE: 82 * np.cumprod(1 + daily_returns)})
df[EVENT_DATE] = [d if d.strftime("%Y-%m-%d") in event_calendar else pd.NaT for d in dates]
df[EVENT_TYPE] = [event_calendar.get(d.strftime("%Y-%m-%d"), (None, None))[0] for d in dates]
df[EVENT_LABEL] = [event_calendar.get(d.strftime("%Y-%m-%d"), (None, None))[1] for d in dates]

# Plot: reads only df and the constants above
events = df.dropna(subset=[EVENT_DATE]).reset_index(drop=True)

# Three-tier staggered flag heights keep neighboring flags and their labels apart
price_range = df[CLOSE].max() - df[CLOSE].min()
tier_offsets = [price_range * 0.2, price_range * 0.4, price_range * 0.6]
events["Flag y"] = [price + tier_offsets[i % 3] for i, price in enumerate(events[CLOSE])]

y_min = df[CLOSE].min() - price_range * 0.05
y_max = events["Flag y"].max() + price_range * 0.14

band = pd.DataFrame(
    {
        "xmin": [pd.Timestamp(HOLIDAY_SEASON[0])],
        "xmax": [pd.Timestamp(HOLIDAY_SEASON[1])],
        "ymin": [y_min],
        "ymax": [y_max],
    }
)
band_label = pd.DataFrame(
    {"x": [pd.Timestamp(HOLIDAY_SEASON[0])], "y": [y_min + price_range * 0.04], "label": ["Holiday season"]}
)

title = "stock-event-flags · python · letsplot · anyplot.ai"
n_title = len(title)
title_fontsize = round(16 * 67 / n_title) if n_title > 67 else 16

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=title_fontsize),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=11),
    legend_position="right",
)

plot = (
    ggplot()
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=band,
        fill=IMPRINT_PALETTE[3],
        alpha=0.12,
        color=IMPRINT_PALETTE[3],
        size=0,
    )
    + geom_text(aes(x="x", y="y", label="label"), data=band_label, hjust=0, size=5, color=INK_SOFT, fontface="italic")
    + geom_area(aes(x=DATE, y=CLOSE), data=df, fill=INK_SOFT, alpha=0.12)
    + geom_line(
        aes(x=DATE, y=CLOSE),
        data=df,
        color=INK_SOFT,
        size=1.3,
        tooltips=layer_tooltips().line(f"@{{{DATE}}}").line(f"Price: $@{{{CLOSE}}}"),
    )
    + geom_segment(
        aes(x=EVENT_DATE, y=CLOSE, xend=EVENT_DATE, yend="Flag y"),
        data=events,
        color=INK_MUTED,
        size=0.5,
        linetype="dashed",
    )
    + geom_point(
        aes(x=EVENT_DATE, y="Flag y", color=EVENT_TYPE, shape=EVENT_TYPE),
        data=events,
        size=6,
        tooltips=layer_tooltips()
        .title(f"@{{{EVENT_TYPE}}}")
        .line(f"@{{{EVENT_LABEL}}}")
        .line(f"Date: @{{{EVENT_DATE}}}")
        .line(f"Price: $@{{{CLOSE}}}"),
    )
    + geom_text(aes(x=EVENT_DATE, y="Flag y", label=EVENT_LABEL), data=events, vjust=-1.5, size=6, color=INK)
    + geom_point(aes(x=EVENT_DATE, y=CLOSE), data=events, color=INK_MUTED, size=2.5)
    + scale_color_manual(values=EVENT_COLORS)
    + scale_shape_manual(values=EVENT_SHAPES)
    + scale_x_datetime(format="%b %Y", expand=[0.04, 0.04])
    + scale_y_continuous(limits=[y_min, y_max])
    + labs(x=DATE, y=CLOSE, title=title)
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
