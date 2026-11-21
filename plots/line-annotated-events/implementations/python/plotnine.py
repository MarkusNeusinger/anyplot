""" anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LABEL_LEVELS = (0.92, 0.85)  # alternating label heights, as a share of the value range
LABEL_NUDGE = 0.02  # gap between a label's marker and its text, as a share of the value range

# Columns: set these to your table's column names
DATE = "Date"  # role: date
VISITORS = "Daily Visitors (count)"  # role: value
EVENT_DATE = "Event date"  # role: event_date
EVENT_LABEL = "Event"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
# Event columns are filled only on the rows that carry an event; every other row leaves them empty.
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=365, freq="D")
base = 50000 + np.cumsum(np.random.randn(365) * 500)
seasonal = 5000 * np.sin(2 * np.pi * np.arange(365) / 365)
weekly = 3000 * np.sin(2 * np.pi * np.arange(365) / 7)
event_dates = pd.to_datetime(["2024-02-15", "2024-05-01", "2024-07-20", "2024-10-10", "2024-12-01"])
event_labels = ["v2.0 Release", "Mobile App Launch", "API Update", "Enterprise Tier", "Holiday Campaign"]
df = pd.DataFrame({DATE: dates, VISITORS: base + seasonal + weekly})
df[EVENT_DATE] = pd.Series(event_dates, dtype="datetime64[ns]")
df[EVENT_LABEL] = pd.Series(event_labels, dtype="object")

# Plot: reads only df and the constants above
events = df.dropna(subset=[EVENT_DATE]).reset_index(drop=True)
y_min, y_range = df[VISITORS].min(), df[VISITORS].max() - df[VISITORS].min()
levels = [LABEL_LEVELS[i % len(LABEL_LEVELS)] for i in range(len(events))]
events["y_pos"] = y_min + np.array(levels) * y_range

plot = (
    ggplot(df, aes(x=DATE, y=VISITORS))
    + geom_line(color=IMPRINT_PALETTE[0], size=0.8, alpha=0.9)
    + geom_vline(
        aes(xintercept=EVENT_DATE), data=events, color=IMPRINT_PALETTE[1], linetype="dashed", size=0.6, alpha=0.8
    )
    + geom_point(aes(x=EVENT_DATE, y="y_pos"), data=events, color=IMPRINT_PALETTE[1], size=2.5, shape="D")
    + geom_text(
        aes(x=EVENT_DATE, y="y_pos", label=EVENT_LABEL),
        data=events,
        color=INK,
        size=7,
        ha="center",
        va="bottom",
        nudge_y=LABEL_NUDGE * y_range,
        fontweight="bold",
    )
    + labs(title="line-annotated-events · python · plotnine · anyplot.ai")
    + scale_x_datetime(date_breaks="2 months", date_labels="%b %Y")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(angle=45, ha="right"),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, weight="bold", color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
