"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
import sys


# Remove script dir from sys.path to avoid shadowing the pygal package
_script_dir = sys.path[0] if sys.path else ""
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


if _script_dir:
    sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BASE_VALUE = 100  # every series is rebased to this value on the first date

# Columns: set these to your table's column names
DATE = "Date"  # role: date
SYMBOL = "Symbol"  # role: symbol
PRICE = "Closing price (USD)"  # role: price

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 252
dates = pd.bdate_range("2024-01-02", periods=n_days)
daily_return = {"NOVA": (0.0012, 0.018), "ORBX": (0.0015, 0.022), "TERRA": (-0.0002, 0.016), "FUND": (0.0004, 0.010)}
df = pd.concat(
    [
        pd.DataFrame({DATE: dates, SYMBOL: symbol, PRICE: 100 * np.cumprod(1 + np.random.normal(mu, sigma, n_days))})
        for symbol, (mu, sigma) in daily_return.items()
    ],
    ignore_index=True,
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=DATE, columns=SYMBOL, values=PRICE, sort=False)
rebased = table / table.bfill().iloc[0] * BASE_VALUE
dates = rebased.index
final_returns = rebased.ffill().iloc[-1] - BASE_VALUE


# Best performer gets a thicker stroke for visual emphasis
best = final_returns.idxmax()

# Series take the palette in order; the reference line takes the muted ink
series_colors = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(rebased.columns))] + [INK_MUTED]

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=series_colors,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
    font_family="sans-serif",
)

# X-axis labels: monthly markers only
x_labels_all = [d.strftime("%b %Y") if i == 0 or d.month != dates[i - 1].month else "" for i, d in enumerate(dates)]
x_labels_major = [label for label in x_labels_all if label]

# Chart
chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title="line-stock-comparison · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title=f"Index (start = {BASE_VALUE})",
    show_x_guides=False,
    show_y_guides=True,
    dots_size=2,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(rebased.columns) + 1,
    x_label_rotation=45,
    show_minor_x_labels=False,
    x_labels_major=x_labels_major,
    margin_bottom=120,
)

chart.x_labels = x_labels_all

for symbol in rebased.columns:
    chart.add(
        f"{symbol} ({final_returns[symbol]:+.1f}%)",
        [
            {"value": val, "label": f"{symbol} | {d.strftime('%Y-%m-%d')} | {val:.1f}"}
            for d, val in zip(dates, rebased[symbol].tolist(), strict=True)
        ],
        stroke_style={"width": 6 if symbol == best else 3},
    )

# Horizontal reference line at the base value anchors the starting baseline visually
chart.add(
    f"Baseline ({BASE_VALUE})",
    [float(BASE_VALUE)] * len(dates),
    show_dots=False,
    stroke_style={"width": 2, "dasharray": "6,4"},
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
