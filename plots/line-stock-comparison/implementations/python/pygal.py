""" anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-23
"""

import datetime
import os
import sys


# Remove script dir from sys.path to avoid shadowing the pygal package
_script_dir = sys.path[0] if sys.path else ""
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


if _script_dir:
    sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ANYPLOT_PALETTE = ("#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E")

# Data
np.random.seed(42)
n_days = 252

start_date = datetime.date(2024, 1, 2)
dates = []
current_date = start_date
while len(dates) < n_days:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += datetime.timedelta(days=1)

returns_aapl = np.random.normal(0.0012, 0.018, n_days)
returns_googl = np.random.normal(0.0015, 0.022, n_days)
returns_msft = np.random.normal(-0.0002, 0.016, n_days)
returns_spy = np.random.normal(0.0004, 0.010, n_days)

price_aapl = 100 * np.cumprod(1 + returns_aapl)
price_googl = 100 * np.cumprod(1 + returns_googl)
price_msft = 100 * np.cumprod(1 + returns_msft)
price_spy = 100 * np.cumprod(1 + returns_spy)

rebased_aapl = price_aapl / price_aapl[0] * 100
rebased_googl = price_googl / price_googl[0] * 100
rebased_msft = price_msft / price_msft[0] * 100
rebased_spy = price_spy / price_spy[0] * 100

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
    font_family="sans-serif",
)

# X-axis labels — monthly markers only
x_labels_all = [d.strftime("%b %Y") if i == 0 or d.month != dates[i - 1].month else "" for i, d in enumerate(dates)]
x_labels_major = [label for label in x_labels_all if label]

# Chart
chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title="line-stock-comparison · python · pygal · anyplot.ai",
    x_title="Date",
    y_title="Rebased Price (Start = 100)",
    show_x_guides=False,
    show_y_guides=True,
    dots_size=2,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    x_label_rotation=45,
    show_minor_x_labels=False,
    x_labels_major=x_labels_major,
    margin_bottom=120,
)

chart.x_labels = x_labels_all

chart.add(
    "AAPL",
    [
        {"value": val, "label": f"AAPL | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
        for i, val in enumerate(rebased_aapl.tolist())
    ],
)
chart.add(
    "GOOGL",
    [
        {"value": val, "label": f"GOOGL | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
        for i, val in enumerate(rebased_googl.tolist())
    ],
)
chart.add(
    "MSFT",
    [
        {"value": val, "label": f"MSFT | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
        for i, val in enumerate(rebased_msft.tolist())
    ],
)
chart.add(
    "SPY (Benchmark)",
    [
        {"value": val, "label": f"SPY | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
        for i, val in enumerate(rebased_spy.tolist())
    ],
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
