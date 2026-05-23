""" anyplot.ai
drawdown-basic: Drawdown Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-23
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

# Data — 2 years of synthetic daily portfolio returns
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=500, freq="D")
returns = np.random.normal(0.0003, 0.018, len(dates))
price = 100 * np.cumprod(1 + returns)

# Drawdown: % decline from running maximum
running_max = np.maximum.accumulate(price)
drawdown = (price - running_max) / running_max * 100

# Max drawdown stats
max_dd_idx = int(np.argmin(drawdown))
max_dd_value = drawdown[max_dd_idx]
max_dd_date = dates[max_dd_idx].strftime("%Y-%m-%d")

# Duration: days from peak to trough
peak_slice = price[: max_dd_idx + 1]
peak_idx = int(np.where(peak_slice == peak_slice.max())[0][-1])
duration_days = (dates[max_dd_idx] - dates[peak_idx]).days

# Recovery time: days from trough to next new high
recovery_after = [i for i in range(max_dd_idx, len(drawdown)) if drawdown[i] >= -0.1]
if recovery_after:
    recovery_days = (dates[recovery_after[0]] - dates[max_dd_idx]).days
    recovery_str = f"{recovery_days}d"
else:
    recovery_str = "Not recovered"

# Recovery indices: where drawdown crosses back to ~zero (new highs)
recovery_indices = [i for i in range(1, len(drawdown)) if drawdown[i - 1] < -0.5 and drawdown[i] >= -0.1]

# Style — semantic colors: red = loss/drawdown, purple = peak loss marker, green = recovery
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#B71D27", "#9418DB", "#009E73", INK_MUTED),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
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
    x_title="Date",
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
    range=(min(drawdown) * 1.1, 5),
)

# X-axis labels — every ~60 days for readability
x_labels = [d.strftime("%Y-%m") if i % 60 == 0 else "" for i, d in enumerate(dates)]
chart.x_labels = x_labels

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
    for idx in recovery_indices[:8]:
        recovery_data[idx] = 0.0
    chart.add("Recovery Points", recovery_data, show_dots=True, dots_size=14)

# Save (theme-suffixed — pipeline runs this script twice)
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
