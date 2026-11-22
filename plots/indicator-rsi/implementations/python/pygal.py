"""anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-16
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
OVERBOUGHT = 70  # RSI above this level reads as overbought
OVERSOLD = 30  # RSI below this level reads as oversold
MIDLINE = 50  # bullish / bearish bias line
LOOKBACK = 14  # standard RSI lookback period

# Columns: set these to your table's column names
DATE = "Trading date"  # role: date
RSI = "RSI (14-period)"  # role: rsi

# Data: replace this block with your own table, for example df = pd.read_csv("rsi.csv")
np.random.seed(42)
n_days = 120
changes = np.random.randn(n_days) * 0.8
changes[15:32] += 4.0  # strong uptrend pushes RSI above 70
changes[75:92] += 4.5
changes[40:57] -= 4.0  # strong downtrend pushes RSI below 30
changes[100:115] -= 3.5
changes = pd.Series(changes)
avg_gain = changes.clip(lower=0).ewm(alpha=1 / LOOKBACK, adjust=False, min_periods=LOOKBACK).mean()
avg_loss = (-changes.clip(upper=0)).ewm(alpha=1 / LOOKBACK, adjust=False, min_periods=LOOKBACK).mean()
rsi_values = 100 - 100 / (1 + avg_gain / avg_loss)
df = pd.DataFrame({DATE: pd.bdate_range("2025-01-02", periods=n_days), RSI: rsi_values})

# Plot: reads only df and the constants above


def blend(color, share):
    """Mix a hex color into the page background at the given share, giving an opaque tint."""
    mixed = [round(int(color[i : i + 2], 16) * share + int(PAGE_BG[i : i + 2], 16) * (1 - share)) for i in (1, 3, 5)]
    return f"#{mixed[0]:02X}{mixed[1]:02X}{mixed[2]:02X}"


rsi_color = IMPRINT_PALETTE[0]
overbought_color = IMPRINT_PALETTE[4]
oversold_color = IMPRINT_PALETTE[2]
n = len(df)

# Series are drawn in the order they are added, so the colors follow the same order:
# zone fills first, threshold lines above them, the RSI line on top.
series_colors = (
    blend(overbought_color, 0.16),
    PAGE_BG,
    blend(oversold_color, 0.16),
    overbought_color,
    oversold_color,
    INK_MUTED,
    rsi_color,
)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=series_colors,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=38,
    value_font_size=36,
    stroke_width=6,
    opacity=1,
    opacity_hover=1,
)

dates = df[DATE].dt.strftime("%b %d").tolist()
chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title="indicator-rsi · python · pygal · anyplot.ai",
    x_title=f"{DATE} ({n} days)",
    y_title=RSI,
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    range=(0, 100),
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=36,
    margin=40,
    margin_bottom=150,
    x_label_rotation=0,
    show_minor_x_labels=False,
    truncate_label=-1,
)
chart.x_labels = dates
chart.x_labels_major = dates[::20]

# Shaded zones: the 100 fill is tinted red, the neutral band is painted over it in the page color,
# and the oversold fill sits below 30
chart.add(f"Overbought zone (>{OVERBOUGHT})", [100] * n, fill=True, show_dots=False, stroke_style={"width": 0})
chart.add(
    f"Neutral band ({OVERSOLD}-{OVERBOUGHT})", [OVERBOUGHT] * n, fill=True, show_dots=False, stroke_style={"width": 0}
)
chart.add(f"Oversold zone (<{OVERSOLD})", [OVERSOLD] * n, fill=True, show_dots=False, stroke_style={"width": 0})

# Threshold and centerline references
chart.add(f"Overbought ({OVERBOUGHT})", [OVERBOUGHT] * n, stroke_style={"width": 4, "dasharray": "20,10"})
chart.add(f"Oversold ({OVERSOLD})", [OVERSOLD] * n, stroke_style={"width": 4, "dasharray": "20,10"})
chart.add(f"Centerline ({MIDLINE})", [MIDLINE] * n, stroke_style={"width": 2, "dasharray": "10,10"})

# RSI line last so it sits on top; the first LOOKBACK days stay empty until the window is filled
chart.add(RSI, [None if pd.isna(v) else float(v) for v in df[RSI]], stroke_style={"width": 7})

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
