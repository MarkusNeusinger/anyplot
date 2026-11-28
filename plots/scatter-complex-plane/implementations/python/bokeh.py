""" anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-28
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Arrow, ColumnDataSource, HoverTool, Label, Legend, LegendItem, NormalHead, Range1d, Span
from bokeh.plotting import figure
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ARROW_ALPHA = [0.75, 0.55, 0.65, 0.70, 0.70]  # arrow opacity per category position, cycled
UNIT_RADIUS = 1.0  # the reference circle of the complex plane
ON_CIRCLE_TOL = 1e-6  # |z| within this of the unit radius counts as a point on the circle


def fmt_z(re, im):
    """Rectangular form a+bi, trimmed of trailing zeros."""
    r = f"{re:.2f}".rstrip("0").rstrip(".")
    b = f"{abs(im):.2f}".rstrip("0").rstrip(".")
    if abs(im) < 1e-10:
        return r
    if abs(re) < 1e-10:
        return f"{b}i" if im > 0 else f"−{b}i"
    return f"{r}{'+' if im > 0 else '−'}{b}i"


# Columns: set these to your table's column names
REAL = "Real Axis"  # role: real
IMAGINARY = "Imaginary Axis"  # role: imaginary
CATEGORY = "Category"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("complex_numbers.csv")
roots = [np.exp(2j * np.pi * k / 5) for k in range(5)]  # 5th roots of unity
arbitrary = [2.5 + 1.2j, -1.8 + 2.2j, -0.5 - 2.5j, -2.3 - 1.0j]  # all four quadrants
z_base = 1.5 + 2j
conjugates = [z_base, z_base.conjugate()]  # symmetric about the real axis
product = [z_base * np.exp(1j * np.pi / 4)]  # multiplication rotates z_base by 45 degrees
z_sum = [arbitrary[0] + arbitrary[1]]  # complex addition
points = roots + arbitrary + conjugates + product + z_sum
df = pd.DataFrame(
    {
        REAL: [z.real for z in points],
        IMAGINARY: [z.imag for z in points],
        CATEGORY: ["5th Root of Unity"] * 5 + ["Arbitrary"] * 4 + ["Conjugate Pair"] * 2 + ["Product", "Sum"],
    }
)

# Plot: reads only df and the constants above
categories = list(df[CATEGORY].unique())
color_of = {cat: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, cat in enumerate(categories)}
alpha_of = {cat: ARROW_ALPHA[i % len(ARROW_ALPHA)] for i, cat in enumerate(categories)}
z = df[REAL].to_numpy() + 1j * df[IMAGINARY].to_numpy()
df["label"] = [fmt_z(re, im) for re, im in zip(df[REAL], df[IMAGINARY], strict=True)]
df["magnitude"] = np.abs(z)
df["angle_deg"] = np.degrees(np.angle(z))
limit = max(df[REAL].abs().max(), df[IMAGINARY].abs().max(), UNIT_RADIUS) * 1.235

# Square canvas for the equal-aspect complex plane (2400 x 2400)
W, H = 2400, 2400
hover_tool = HoverTool(
    tooltips=[
        ("Point", "@label"),
        (CATEGORY, f"@{{{CATEGORY}}}"),
        ("|z|", "@magnitude{0.00}"),
        ("arg(z)", "@angle_deg{0.0}°"),
    ],
    mode="mouse",
)

p = figure(
    width=W,
    height=H,
    title="scatter-complex-plane · python · bokeh · anyplot.ai",
    x_axis_label=REAL,
    y_axis_label=IMAGINARY,
    match_aspect=True,
    tools=[hover_tool],
    toolbar_location=None,  # a toolbar would shorten the canvas
    min_border_bottom=160,  # room for 34pt x-tick labels + 42pt x-axis label
    min_border_left=180,  # room for 34pt y-tick labels + 42pt y-axis label
    min_border_top=110,  # room for 50pt title
    min_border_right=60,
)
p.x_range = Range1d(-limit, limit)
p.y_range = Range1d(-limit, limit)

# Unit circle: dashed geometric reference
theta = np.linspace(0, 2 * np.pi, 300)
unit_circle = p.line(
    UNIT_RADIUS * np.cos(theta),
    UNIT_RADIUS * np.sin(theta),
    line_color=INK_MUTED,
    line_dash="dashed",
    line_width=5,
    line_alpha=0.85,
)

# Axes through the origin
p.add_layout(Span(location=0, dimension="width", line_color=INK_SOFT, line_width=2, line_alpha=0.7))
p.add_layout(Span(location=0, dimension="height", line_color=INK_SOFT, line_width=2, line_alpha=0.7))

# Callout for the largest conjugate pair found in df: dotted link plus a label
upper = df[df[IMAGINARY] > 1e-10]
partner = upper.apply(
    lambda row: ((df[REAL] - row[REAL]).abs() + (df[IMAGINARY] + row[IMAGINARY]).abs() < 1e-10).any(), axis=1
)
pairs = upper[partner]
if not pairs.empty:
    top = pairs.loc[pairs["magnitude"].idxmax()]
    p.line(
        [top[REAL], top[REAL]],
        [top[IMAGINARY], -top[IMAGINARY]],
        line_color=IMPRINT_PALETTE[2],
        line_dash="dotted",
        line_width=3,
        line_alpha=0.5,
    )
    p.add_layout(
        Label(
            x=top[REAL] + 0.15,
            y=top[IMAGINARY] * 0.1,
            text="Conjugate pair: symmetric about Re-axis",
            text_font_size="21pt",
            text_color=IMPRINT_PALETTE[2],
            text_font_style="italic",
            background_fill_color=ELEVATED_BG,
            background_fill_alpha=0.85,
            border_line_color=IMPRINT_PALETTE[2],
            border_line_alpha=0.65,
            padding=10,
        )
    )

# Vectors from the origin to each point
for cat, re, im in zip(df[CATEGORY], df[REAL], df[IMAGINARY], strict=True):
    col = color_of[cat]
    p.add_layout(
        Arrow(
            end=NormalHead(size=18, fill_color=col, line_color=col),
            x_start=0,
            y_start=0,
            x_end=re,
            y_end=im,
            line_color=col,
            line_width=2.5,
            line_alpha=alpha_of[cat],
        )
    )

# Points by category, one source each for the hover tooltips
legend_items = []
for cat in categories:
    r = p.scatter(
        x=REAL,
        y=IMAGINARY,
        source=ColumnDataSource(df[df[CATEGORY] == cat]),
        size=26,
        color=color_of[cat],
        line_color="white",
        line_width=2.5,
        alpha=0.95,
    )
    legend_items.append(LegendItem(label=str(cat), renderers=[r]))

# Point labels, offset radially from the origin (screen pixels); marks stay at their values
placed = []
for re, im, lbl, mag in zip(df[REAL], df[IMAGINARY], df["label"], df["magnitude"], strict=True):
    angle = np.arctan2(im, re)
    on_circle = abs(mag - UNIT_RADIUS) < ON_CIRCLE_TOL
    base_dist = 55 if on_circle else 30  # larger offset where points cluster on the unit circle
    ox = base_dist * np.cos(angle)
    oy = base_dist * np.sin(angle)
    if re < -0.5:  # push left-half labels further left to clear the axis
        ox -= 12
    if abs(im) < 0.3 and re > 0:  # raise near-horizontal labels above the point
        oy += 18
    if on_circle:
        if im < -0.3:
            oy -= 16
        if abs(re) < 0.5 and im > 0:
            oy += 14
    for px, py in placed:  # nudge the label away from labels already placed
        dx = (re + ox * 0.012) - px
        dy = (im + oy * 0.012) - py
        if abs(dx) < 0.55 and abs(dy) < 0.55:
            oy += 35 if im >= py else -35
    placed.append((re + ox * 0.012, im + oy * 0.012))
    p.add_layout(Label(x=re, y=im, text=lbl, x_offset=ox, y_offset=oy, text_font_size="24pt", text_color=INK_SOFT))

# Legend, top-left
legend = Legend(
    items=[LegendItem(label="Unit Circle", renderers=[unit_circle])] + legend_items,
    location="top_left",
    label_text_font_size="30pt",
    label_text_color=INK_SOFT,
    glyph_width=36,
    glyph_height=36,
    spacing=10,
    padding=20,
    margin=20,
    background_fill_alpha=0.92,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
)
p.add_layout(legend)

# Style
p.title.text_font_size = "50pt"
p.title.text_font_style = "normal"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0.12
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save: interactive HTML, then a PNG screenshot through headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Pin the PNG to the exact canvas size
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (W, H):
    canvas = Image.new("RGB", (W, H), PAGE_BG)
    canvas.paste(img, ((W - img.size[0]) // 2, (H - img.size[1]) // 2))
    canvas.save(f"plot-{THEME}.png")
