""" anyplot.ai
drawdown-basic: Drawdown Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-26
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

# Imprint palette: loss red, peak-loss purple and recovery green are semantic picks from it
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RECOVERY_TOLERANCE = 0.1  # a drawdown shallower than this (in %) counts as back at a new high
MIN_DIP = 0.5  # a recovery needs a dip deeper than this (in %) right before it
MAX_RECOVERY_MARKS = 8  # recovery markers drawn, to keep the chart readable
LABEL_EVERY = 60  # one x tick label per this many rows

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PRICE = "Portfolio value"  # role: price

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=500, freq="D")
returns = np.random.normal(0.0003, 0.018, len(dates))
df = pd.DataFrame({DATE: dates, PRICE: 100 * np.cumprod(1 + returns)})

# Plot: reads only df and the constants above
price = df[PRICE].to_numpy()
dates = df[DATE]

# Drawdown: % decline from running maximum
running_max = np.fmax.accumulate(price)
drawdown = (price - running_max) / running_max * 100

# Max drawdown stats
max_dd_idx = int(np.nanargmin(drawdown))
max_dd_value = drawdown[max_dd_idx]
max_dd_date = dates[max_dd_idx].strftime("%Y-%m-%d")

# Duration: days from peak to trough
peak_slice = price[: max_dd_idx + 1]
peak_idx = int(np.where(peak_slice == np.nanmax(peak_slice))[0][-1])
duration_days = (dates[max_dd_idx] - dates[peak_idx]).days

# Recovery time: days from trough to next new high
recovery_after = [i for i in range(max_dd_idx, len(drawdown)) if drawdown[i] >= -RECOVERY_TOLERANCE]
if recovery_after:
    recovery_days = (dates[recovery_after[0]] - dates[max_dd_idx]).days
    recovery_str = f"{recovery_days}d"
else:
    recovery_str = "Not recovered"

# Recovery indices: where drawdown crosses back to ~zero (new highs)
recovery_indices = [
    i for i in range(1, len(drawdown)) if drawdown[i - 1] < -MIN_DIP and drawdown[i] >= -RECOVERY_TOLERANCE
]

# Style — semantic colors: red = loss/drawdown, purple = peak loss marker, green = recovery
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=(IMPRINT_PALETTE[4], IMPRINT_PALETTE[1], IMPRINT_PALETTE[0], INK_MUTED),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=56,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
    opacity=".65",
    opacity_hover=".85",
)

chart = pygal.Line(
    width=3200,
    height=1800,
    title="drawdown-basic · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title="Drawdown (%)",
    style=custom_style,
    show_dots=False,
    stroke_style={"width": 4},
    fill=False,
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=45,
    legend_at_bottom=True,
    truncate_legend=-1,
    legend_box_size=44,
    range=(np.nanmin(drawdown) * 1.1, 0),
)

# X-axis labels — sparse for readability
chart.x_labels = [d.strftime("%Y-%m") if i % LABEL_EVERY == 0 else "" for i, d in enumerate(dates)]

# Main drawdown series with fill — per-series fill keeps the area clean
chart.add(f"Drawdown (Max: {max_dd_value:.1f}% on {max_dd_date})", list(drawdown), fill=True)

# Max drawdown marker — prominent dot at the trough (no fill, just the dot)
max_marker = [None] * len(drawdown)
max_marker[max_dd_idx] = drawdown[max_dd_idx]
chart.add(
    f"Max Drawdown: {max_dd_value:.1f}% | Duration: {duration_days}d | Recovery: {recovery_str}",
    max_marker,
    show_dots=True,
    dots_size=18,
)

# Recovery point markers — green dots at zero-crossings (no fill since values ≈ 0)
if recovery_indices:
    recovery_data = [None] * len(drawdown)
    for idx in recovery_indices[:MAX_RECOVERY_MARKS]:
        recovery_data[idx] = 0.0
    chart.add("Recovery Points", recovery_data, show_dots=True, dots_size=14, stroke=False)

# Save (theme-suffixed — pipeline runs this script twice)
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
