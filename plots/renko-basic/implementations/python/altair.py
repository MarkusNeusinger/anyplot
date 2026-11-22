""" anyplot.ai
renko-basic: Basic Renko Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
"""

import os
import sys


# Workaround for import conflict: altair.py shadows the altair library
# Remove the script directory from sys.path before importing
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: bullish takes position 1, bearish the red at position 5
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULLISH = IMPRINT_PALETTE[0]
BEARISH = IMPRINT_PALETTE[4]

# Constants
BRICK_SIZE = 2.0  # price move that draws one brick
BRICK_GAP = 0.15  # share of a column left empty between neighbouring bricks

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 250
returns = np.random.normal(0.001, 0.015, n_days)
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=n_days), CLOSE: 100 * np.cumprod(1 + returns)})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# Build Renko bricks: one brick per BRICK_SIZE move away from the last brick's close
prices = df[CLOSE].to_numpy()
last_close = round(prices[0] / BRICK_SIZE) * BRICK_SIZE
rows = []
for p in prices:
    while abs(p - last_close) >= BRICK_SIZE:
        step = BRICK_SIZE if p > last_close else -BRICK_SIZE
        rows.append(
            {
                "brick": len(rows),
                "low": min(last_close, last_close + step),
                "high": max(last_close, last_close + step),
                "direction": "Bullish" if step > 0 else "Bearish",
                "close": last_close + step,
            }
        )
        last_close += step
bricks = pd.DataFrame(rows)
bricks["brick_end"] = bricks["brick"] + 1 - BRICK_GAP

chart = (
    alt.Chart(bricks)
    .mark_rect(strokeWidth=1, stroke=INK_SOFT)
    .encode(
        x=alt.X("brick", type="quantitative", title="Brick index", scale=alt.Scale(nice=False)),
        x2="brick_end",
        y=alt.Y("low", type="quantitative", title=CLOSE, scale=alt.Scale(zero=False)),
        y2="high",
        color=alt.Color(
            "direction",
            type="nominal",
            title="Direction",
            scale=alt.Scale(domain=["Bullish", "Bearish"], range=[BULLISH, BEARISH]),
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, orient="right"),
        ),
        tooltip=[
            alt.Tooltip("brick", type="quantitative", title="Brick #"),
            alt.Tooltip("low", type="quantitative", title="Low", format="$.2f"),
            alt.Tooltip("high", type="quantitative", title="High", format="$.2f"),
            alt.Tooltip("direction", type="nominal", title="Direction"),
        ],
    )
    .properties(
        width=570,
        height=320,
        title=alt.Title("renko-basic · python · altair · anyplot.ai", fontSize=28, anchor="middle"),
        background=PAGE_BG,
    )
    .interactive()
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        gridColor=INK,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the exact landscape target canvas
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(f"altair vl-convert produced {_w}x{_h}, exceeds target {TW}x{TH}. Shrink width/height.")
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")
