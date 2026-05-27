""" anyplot.ai
area-cumulative-flow: Cumulative Flow Diagram for Workflow Analytics
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-07
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

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030")

# Data: 90-day Kanban board for a software delivery team
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-01-02", periods=n_days, freq="D")

# Daily new items entering the backlog (1–3 per day)
daily_new = np.random.randint(1, 4, n_days)
backlog_entered = np.cumsum(daily_new).astype(float)

# Each stage has a fixed lag from the previous stage boundary
analysis_lag = 4  # days after entering backlog before analysis starts
dev_lag = 8  # days in analysis before development starts
testing_lag = 12  # days in development before testing starts
done_lag = 6  # days in testing before done

analysis_entered = np.zeros(n_days)
dev_entered = np.zeros(n_days)
testing_entered = np.zeros(n_days)
done = np.zeros(n_days)

for d in range(n_days):
    if d >= analysis_lag:
        analysis_entered[d] = backlog_entered[d - analysis_lag]
    if d >= analysis_lag + dev_lag:
        dev_entered[d] = analysis_entered[d - dev_lag]
    if d >= analysis_lag + dev_lag + testing_lag:
        testing_entered[d] = dev_entered[d - testing_lag]
    if d >= analysis_lag + dev_lag + testing_lag + done_lag:
        done[d] = testing_entered[d - done_lag]

# Band widths (WIP per stage) — stacked bottom-to-top: Done → Backlog
done_band = done
testing_band = testing_entered - done
dev_band = dev_entered - testing_entered
analysis_band = analysis_entered - dev_entered
backlog_band = backlog_entered - analysis_entered

# X-axis labels — show every 15th day
all_labels = [d.strftime("%b %d") for d in dates]
major_labels = [d.strftime("%b %d") for d in dates[::15]]

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=2,
)

# Chart
chart = pygal.StackedLine(
    style=custom_style,
    fill=True,
    width=4800,
    height=2700,
    title="Kanban Delivery Flow · area-cumulative-flow · pygal · anyplot.ai",
    x_title="Date",
    y_title="Cumulative Item Count",
    show_minor_x_labels=False,
    x_label_rotation=30,
    margin=100,
    show_dots=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
)

chart.x_labels = all_labels
chart.x_labels_major = major_labels

# Add series from bottom (Done) to top (Backlog) — workflow order reversed
chart.add("Done", done_band.tolist())
chart.add("Testing", testing_band.tolist())
chart.add("Development", dev_band.tolist())
chart.add("Analysis", analysis_band.tolist())
chart.add("Backlog", backlog_band.tolist())

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
