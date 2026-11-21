""" anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotnine as pn


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 7  # rolling window in days

# Columns: set these to your table's column names
DATE = "Date"  # role: date
VIEWS = "Page views"  # role: value
SERIES = "Series"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("page_views.csv")
rng = np.random.default_rng(42)
days = pd.date_range("2024-01-01", periods=180, freq="D")
growth = np.linspace(8200, 11800, len(days))  # slow audience growth
weekly = 1 + 0.18 * np.cos(2 * np.pi * (days.day_of_week - 2) / 7)  # midweek peak, weekend dip
views = growth * weekly * rng.lognormal(0, 0.07, len(days))
df = pd.DataFrame({DATE: days, VIEWS: views.round()})

# Plot: reads only df and the constants above
raw_label = "Daily page views"
roll_label = f"{WINDOW}-day rolling average"
rolling = df[VIEWS].rolling(window=WINDOW, center=True).mean()  # NaN until the window is full

long = pd.concat(
    [
        pd.DataFrame({DATE: df[DATE], VIEWS: df[VIEWS], SERIES: raw_label}),
        pd.DataFrame({DATE: df[DATE], VIEWS: rolling, SERIES: roll_label}).dropna(),
    ],
    ignore_index=True,
)
labels = [raw_label, roll_label]
long[SERIES] = pd.Categorical(long[SERIES], categories=labels, ordered=True)

plot = (
    pn.ggplot(long, pn.aes(x=DATE, y=VIEWS, color=SERIES, alpha=SERIES, size=SERIES))
    + pn.geom_line()
    + pn.scale_color_manual(values=IMPRINT_PALETTE, limits=labels)
    + pn.scale_alpha_manual(values=[0.6, 1.0], limits=labels)
    + pn.scale_size_manual(values=[0.45, 1.5], limits=labels)
    + pn.guides(alpha="none", size="none")
    + pn.scale_x_datetime(date_breaks="1 month", date_labels="%b %Y")
    + pn.labs(title="line-timeseries-rolling · python · plotnine · anyplot.ai", color="")
    + pn.theme_minimal()
    + pn.theme(
        figure_size=(8, 4.5),
        plot_background=pn.element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=pn.element_rect(fill=PAGE_BG),
        panel_grid_major=pn.element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=pn.element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=pn.element_rect(color=INK_SOFT, fill=None),
        axis_title=pn.element_text(size=10, color=INK),
        axis_text=pn.element_text(size=8, color=INK_SOFT),
        axis_line=pn.element_line(color=INK_SOFT),
        plot_title=pn.element_text(size=12, color=INK),
        legend_background=pn.element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=pn.element_text(size=8, color=INK_SOFT),
        legend_position="top",
        text=pn.element_text(size=7),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
