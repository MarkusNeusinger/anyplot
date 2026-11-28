"""anyplot.ai
horizon-basic: Horizon Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-28
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BANDS = 3  # folded bands per polarity
ROW_GAP = 0.18  # empty space between rows, as a share of the row height
DIV_NEGATIVE = "#AE3030"  # imprint_div poles; the midpoint is the page color
DIV_POSITIVE = "#4467A3"

# Columns: set these to your table's column names
DAY = "Trading day (2024)"  # role: date
EXCESS = "Excess return vs benchmark (pp)"  # role: value
SECTOR = "Sector"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("sectors.csv")
np.random.seed(42)
trading_days = pd.bdate_range("2024-01-02", periods=126)
# (sector, daily drift pp, daily volatility pp): cumulative excess return is a drifted random walk
sector_params = [
    ("Technology", 0.14, 1.3),
    ("Consumer Discretionary", 0.09, 1.1),
    ("Financials", 0.07, 0.9),
    ("Industrials", 0.05, 0.8),
    ("Healthcare", 0.04, 0.7),
    ("Utilities", -0.03, 0.5),
    ("Real Estate", -0.06, 1.0),
    ("Energy", -0.08, 1.4),
]
df = pd.concat(
    [
        pd.DataFrame(
            {
                DAY: trading_days,
                EXCESS: np.cumsum(np.random.normal(drift, volatility, len(trading_days))),
                SECTOR: sector,
            }
        )
        for sector, drift, volatility in sector_params
    ],
    ignore_index=True,
)

# Plot
table = df.pivot_table(index=DAY, columns=SECTOR, values=EXCESS, sort=False)
# Rank rows by final cumulative excess return (best performer on top)
ranked = table.ffill().iloc[-1].sort_values(ascending=False).index

# One band range for every row: a color stands for the same magnitude in all sectors
band_size = np.nanmax(np.abs(table.to_numpy())) / N_BANDS


def blend(t, pole):
    """Mix the page color toward a pole color by share t (imprint_div fields ramp)."""
    mix = [round(int(PAGE_BG[i : i + 2], 16) * (1 - t) + int(pole[i : i + 2], 16) * t) for i in (1, 3, 5)]
    return "#" + "".join(f"{c:02X}" for c in mix)


# Band k: from a visible first step (never the bare page color) up to the full pole
steps = [0.4 + 0.6 * k / (N_BANDS - 1) for k in range(N_BANDS)]
pos_colors = [blend(t, DIV_POSITIVE) for t in steps]
neg_colors = [blend(t, DIV_NEGATIVE) for t in steps]

# Each row is a stack of layers measured in row heights (0 to 1). A value in band m draws its
# remainder r in band m's color at the baseline, with the full lower band m-1 above it.
row_stacks = []  # per row, from the bottom of the chart up: (polarity, band, heights, color)
for sector in reversed(ranked):
    values = table[sector].to_numpy()
    magnitude = np.abs(values)
    band = np.minimum(magnitude // band_size, N_BANDS - 1)
    remainder = np.clip((magnitude - band * band_size) / band_size, 0, 1)
    stack = []
    for polarity, on_side, colors in (("+", values >= 0, pos_colors), ("−", values < 0, neg_colors)):
        for k in reversed(range(N_BANDS)):
            heights = np.where(on_side & (band == k), remainder, 0.0)
            if k + 1 < N_BANDS:
                heights = heights + np.where(on_side & (band == k + 1), 1 - remainder, 0.0)
            stack.append((polarity, k, heights, colors[k]))
    row_stacks.append((sector, values, stack))

day_labels = [d.strftime("%b %d") for d in table.index]
row_pitch = 1 + ROW_GAP
series_colors = []
chart_series = []
for j, (sector, values, stack) in enumerate(row_stacks):
    # The top row's layers carry the legend entries: the value range each color step stands for
    is_key_row = j == len(row_stacks) - 1
    for sign, k, heights, color in stack:
        low, high = k * band_size, (k + 1) * band_size
        key = (
            f"{sign}{low:.0f} to {sign}{high:.0f} pp".replace("+0 to", "0 to").replace("−0 to", "0 to")
            if is_key_row
            else None
        )
        points = [
            {"value": float(h), "label": f"{sector} · {day}: {v:+.1f} pp"}
            for h, v, day in zip(heights, values, day_labels, strict=True)
        ]
        chart_series.append((key, points))
        series_colors.append(color)
    # The spacer lifts the next row's baseline; it draws nothing
    used = sum(heights for _, _, heights, _ in stack)
    chart_series.append((None, [float(g) for g in row_pitch - used]))
    series_colors.append(PAGE_BG)

title = "Sector Performance vs Benchmark · horizon-basic · python · pygal · anyplot.ai"
title_font_size = round(66 * min(1.0, 67 / len(title)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(series_colors),
    opacity="1",
    opacity_hover="1",
    title_font_size=title_font_size,
    legend_font_size=44,
    label_font_size=44,
    major_label_font_size=44,
    value_font_size=36,
    font_family="sans-serif",
)

chart = pygal.StackedLine(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=DAY,
    fill=True,
    show_dots=False,
    stroke_style={"width": 0},
    show_y_guides=False,
    show_x_guides=True,
    x_labels=day_labels,
    x_labels_major_count=9,
    show_minor_x_labels=False,
    x_label_rotation=0,
    truncate_label=-1,
    y_labels=[{"label": sector, "value": j * row_pitch + 0.5} for j, (sector, _, _) in enumerate(row_stacks)],
    range=(0, len(row_stacks) * row_pitch - ROW_GAP),
    legend_at_bottom=False,
    truncate_legend=-1,
    legend_box_size=44,
    margin=50,
)
for key, points in chart_series:
    chart.add(key, points)

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
