""" anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-20
"""

import io
import os
import re

import numpy as np
import pandas as pd
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 12  # histogram bins per marginal

# Columns: set these to your table's column names
WIND_SPEED = "Wind speed (m/s)"  # role: x
POWER = "Power output (kW)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("turbine.csv")
rng = np.random.default_rng(42)
speed = np.clip(rng.weibull(2.3, 220) * 8.5, 2.0, 22.0)
rated_kw = 2000.0
power = rated_kw / (1 + np.exp(-(speed - 8.5) / 1.5)) + rng.normal(0, 120, speed.size)
df = pd.DataFrame({WIND_SPEED: speed.round(2), POWER: np.clip(power, 0, rated_kw * 1.05).round(0)})

# Plot: reads only df and the constants above
x, y = df[WIND_SPEED].to_numpy(), df[POWER].to_numpy()


def nice_range(values, bins):
    """Bin-aligned limits: whole multiples of a round bin width that cover the data."""
    raw = (np.nanmax(values) - np.nanmin(values)) / bins
    unit = 10 ** np.floor(np.log10(raw))
    step = np.ceil(raw / unit) * unit
    return np.floor(np.nanmin(values) / step) * step, np.ceil(np.nanmax(values) / step) * step


x_lo, x_hi = nice_range(x, N_BINS)
y_lo, y_hi = nice_range(y, N_BINS)
x_counts, _ = np.histogram(x, bins=N_BINS, range=(x_lo, x_hi))
y_counts, _ = np.histogram(y, bins=N_BINS, range=(y_lo, y_hi))

# Layout on the 3200 x 1800 canvas
W, H = 3200, 1800
TITLE_H, GAP, PAD = 130, 10, 20
TOP_H, RIGHT_W = 330, 400
scatter_w = W - 2 * PAD - GAP - RIGHT_W
scatter_h = H - TITLE_H - PAD - GAP - TOP_H

title = "Wind Turbine Output · scatter-marginal · python · pygal · anyplot.ai"
title_size = round(66 * min(1.0, 67 / len(title)))


def style(colors, opacity):
    return Style(
        background=PAGE_BG,
        plot_background=PAGE_BG,
        foreground=INK,
        foreground_strong=INK,
        foreground_subtle=INK_MUTED,
        colors=colors,
        title_font_size=56,
        label_font_size=56,
        major_label_font_size=44,
        opacity=opacity,
        opacity_hover=opacity,
        stroke_width=2,
    )


scatter = pygal.XY(
    width=scatter_w,
    height=scatter_h,
    style=style(IMPRINT_PALETTE, 0.6),
    x_title=WIND_SPEED,
    y_title=POWER,
    show_legend=False,
    stroke=False,
    dots_size=11,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    explicit_size=True,
    margin=20,
    xrange=(x_lo, x_hi),
    range=(y_lo, y_hi),
)
scatter.add("Observations", list(zip(df[WIND_SPEED], df[POWER], strict=True)))


def plot_box(chart):
    """Plot-area origin and size in pixels, read from the rendered SVG."""
    svg = chart.render().decode("utf-8")
    left, top = map(float, re.search(r'translate\(([\d.]+), ([\d.]+)\)" class="plot"', svg).groups())
    width, height = map(
        float, re.search(r'class="plot"[^>]*>\s*<rect x="0" y="0" width="([\d.]+)" height="([\d.]+)"', svg).groups()
    )
    return left, top, width, height


# The marginals take the scatter's plot box so their bins line up with its axes
p_left, p_top, p_w, p_h = plot_box(scatter)
marginal_style = style((INK_MUTED,), 0.55)
marginal_common = {
    "style": marginal_style,
    "show_legend": False,
    "show_x_labels": False,
    "show_y_labels": False,
    "show_x_guides": False,
    "show_y_guides": False,
    "explicit_size": True,
    "spacing": 3,
}

x_margin = pygal.Bar(
    width=scatter_w,
    height=TOP_H,
    margin_left=p_left,
    margin_right=scatter_w - p_left - p_w,
    margin_top=20,
    margin_bottom=0,
    range=(0, x_counts.max() * 1.08),
    **marginal_common,
)
x_margin.add("Wind speed", x_counts.tolist())

y_margin = pygal.HorizontalBar(
    width=RIGHT_W,
    height=scatter_h,
    margin_left=0,
    margin_right=20,
    margin_top=p_top,
    margin_bottom=scatter_h - p_top - p_h,
    range=(0, y_counts.max() * 1.08),
    **marginal_common,
)
y_margin.add("Power", y_counts.tolist())

# Compose the three panels
canvas = Image.new("RGB", (W, H), PAGE_BG)
scatter_x, scatter_y = PAD, TITLE_H + TOP_H + GAP
for chart, origin in (
    (x_margin, (PAD, TITLE_H)),
    (y_margin, (PAD + scatter_w + GAP, scatter_y)),
    (scatter, (scatter_x, scatter_y)),
):
    canvas.paste(Image.open(io.BytesIO(chart.render_to_png())).convert("RGB"), origin)


def font(size, bold=False):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


draw = ImageDraw.Draw(canvas)
title_font = font(title_size, bold=True)
title_w = draw.textlength(title, font=title_font)
draw.text(((W - title_w) / 2, 28), title, fill=INK, font=title_font)

# Summary card in the empty top-right corner
card = [(PAD + scatter_w + GAP + 30, TITLE_H + 30), (W - PAD - 10, TITLE_H + TOP_H - 20)]
draw.rounded_rectangle(card, radius=16, fill=ELEVATED_BG, outline=INK_MUTED, width=2)
draw.text((card[0][0] + 28, card[0][1] + 22), "Summary", fill=INK, font=font(42, bold=True))
lines = [f"n = {len(df)}", f"r = {df[WIND_SPEED].corr(df[POWER]):.2f}", f"mean {df[POWER].mean():.0f} kW"]
for i, line in enumerate(lines):
    draw.text((card[0][0] + 28, card[0][1] + 88 + i * 52), line, fill=INK_SOFT, font=font(36))

canvas.save(f"plot-{THEME}.png", "PNG")

# Interactive HTML: the scatter panel as SVG
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(scatter.render())
