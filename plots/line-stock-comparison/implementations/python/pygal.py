""" anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-23
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

IMPRINT = ("#009E73", "#C475FD", "#AE3030", "#4467A3", "#99B314", "#954477", "#BD8233")

# Extended palette: data series use positions 1-4, INK_MUTED reserved for the reference line
PALETTE_WITH_REF = IMPRINT[:4] + (INK_MUTED,)

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

# Year-end returns for legend labels (data storytelling)
final_returns = {
    "AAPL": rebased_aapl[-1] - 100,
    "GOOGL": rebased_googl[-1] - 100,
    "MSFT": rebased_msft[-1] - 100,
    "SPY": rebased_spy[-1] - 100,
}


def fmt_ret(r):
    sign = "+" if r >= 0 else ""
    return f"{sign}{r:.1f}%"


# Best performer gets a thicker stroke for visual emphasis
best = max(final_returns, key=final_returns.get)


def series_stroke(name):
    return {"width": 6} if name == best else {"width": 3}


# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=PALETTE_WITH_REF,
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
    legend_at_bottom_columns=5,
    x_label_rotation=45,
    show_minor_x_labels=False,
    x_labels_major=x_labels_major,
    margin_bottom=120,
)

chart.x_labels = x_labels_all

chart.add(
    f"AAPL ({fmt_ret(final_returns['AAPL'])})",
    [
        {"value": val, "label": f"AAPL | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
        for i, val in enumerate(rebased_aapl.tolist())
    ],
    stroke_style=series_stroke("AAPL"),
)
chart.add(
    f"GOOGL ({fmt_ret(final_returns['GOOGL'])})",
    [
        {"value": val, "label": f"GOOGL | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
        for i, val in enumerate(rebased_googl.tolist())
    ],
    stroke_style=series_stroke("GOOGL"),
)
chart.add(
    f"MSFT ({fmt_ret(final_returns['MSFT'])})",
    [
        {"value": val, "label": f"MSFT | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
        for i, val in enumerate(rebased_msft.tolist())
    ],
    stroke_style=series_stroke("MSFT"),
)
chart.add(
    f"SPY ({fmt_ret(final_returns['SPY'])})",
    [
        {"value": val, "label": f"SPY | {dates[i].strftime('%Y-%m-%d')} | {val:.1f}"}
        for i, val in enumerate(rebased_spy.tolist())
    ],
    stroke_style=series_stroke("SPY"),
)

# Horizontal reference line at y=100 anchors the starting baseline visually
chart.add("Baseline (100)", [100.0] * n_days, show_dots=False, stroke_style={"width": 2, "dasharray": "6,4"})

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
