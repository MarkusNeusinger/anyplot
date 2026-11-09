""" anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants: the standard Bollinger parameters
WINDOW = 20  # trading days in the moving average
N_STD = 2  # standard deviations between the middle and each outer band

# Columns: set these to your table's column names
DATE = "Trading date"  # role: date
CLOSE = "Price (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
df = pd.DataFrame(
    {
        DATE: pd.bdate_range("2024-01-02", periods=120),
        CLOSE: (150 * np.cumprod(1 + np.random.normal(0.0005, 0.015, 120))).round(2),
    }
)

# Plot: the bands come from the close price, and start where a full window is available
prices = df.dropna(subset=[DATE]).sort_values(DATE).reset_index(drop=True)
rolling = prices[CLOSE].rolling(WINDOW)
prices["sma"] = rolling.mean()
prices["upper"] = prices["sma"] + N_STD * rolling.std(ddof=0)
prices["lower"] = prices["sma"] - N_STD * rolling.std(ddof=0)
bands = prices.dropna(subset=["upper", "lower"])
dates = prices[DATE].dt.to_pydatetime()
band_dates = bands[DATE].dt.to_pydatetime()

BAND = IMPRINT_PALETTE[1]
band_rgb = ", ".join(str(int(BAND[i : i + 2], 16)) for i in (1, 3, 5))
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    # series order: band fill, upper band, lower band, middle band (neutral ink), close price
    colors=(f"rgba({band_rgb}, 0.18)", BAND, BAND, INK, IMPRINT_PALETTE[0]),
    guide_stroke_color=RULE,
    major_guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    title_font_size=66,
    label_font_size=46,
    major_label_font_size=46,
    legend_font_size=46,
    value_font_size=36,
    tooltip_font_size=36,
    opacity=1,
    opacity_hover=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=3,
)

chart = pygal.DateTimeLine(
    width=3200,
    height=1800,
    style=custom_style,
    title="indicator-bollinger · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title=CLOSE,
    # one dataset's first band value as the fill baseline turns the band outline into a closed polygon
    zero=float(bands["lower"].iloc[0]) if len(bands) else 0,
    show_x_guides=False,
    show_y_guides=True,
    show_dots=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=40,
    truncate_legend=-1,
    spacing=24,
    margin=40,
    x_value_formatter=lambda moment: moment.strftime("%b %Y"),
    # pygal sets one stroke width for every line; the close and the middle band get their own
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.serie-3 .line { stroke-width: 4px !important; } .serie-4 .line { stroke-width: 7px !important; }",
    ],
)
chart.x_labels = pd.date_range(prices[DATE].min(), prices[DATE].max(), freq="MS").to_pydatetime().tolist()

# Band fill: forward along the upper band, back along the lower band
chart.add(
    None,
    list(zip(band_dates, bands["upper"], strict=True)) + list(zip(band_dates[::-1], bands["lower"][::-1], strict=True)),
    fill=True,
)
chart.add(f"Bollinger bands (±{N_STD}σ)", list(zip(band_dates, bands["upper"], strict=True)))
chart.add(None, list(zip(band_dates, bands["lower"], strict=True)))
chart.add(f"{WINDOW}-day SMA", list(zip(band_dates, bands["sma"], strict=True)), stroke_style={"dasharray": "18, 12"})
closes = [None if pd.isna(price) else float(price) for price in prices[CLOSE]]
chart.add("Close", list(zip(dates, closes, strict=True)), allow_interruptions=True)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
