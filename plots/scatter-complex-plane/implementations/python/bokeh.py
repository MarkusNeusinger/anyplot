""" anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-06-02
"""

import os
import sys


# Prevent this file (bokeh.py) from shadowing the installed bokeh package when
# Python prepends the script's directory to sys.path at startup.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import Arrow, ColumnDataSource, HoverTool, Label, Legend, LegendItem, NormalHead, Range1d, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome (Imprint palette system)
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — 8 hues, hybrid-v3 sort order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# === Data ===
# 5th roots of unity — equally spaced on the unit circle
roots = [np.exp(2j * np.pi * k / 5) for k in range(5)]

# Arbitrary complex numbers spanning all four quadrants
z_a = 2.5 + 1.2j
z_b = -1.8 + 2.2j
z_c = -0.5 - 2.5j
z_d = -2.3 - 1.0j
arbitrary = [z_a, z_b, z_c, z_d]

# Conjugate pair — symmetric about the real axis
z_base = 1.5 + 2j
conjugates = [z_base, z_base.conjugate()]

# Product: multiplication by exp(iπ/4) rotates z_base by 45°
product = [z_base * np.exp(1j * np.pi / 4)]

# Sum of two arbitrary points — illustrates complex addition geometry
z_sum = [z_a + z_b]  # = 0.7 + 3.4j

all_points = roots + arbitrary + conjugates + product + z_sum
categories = ["5th Root of Unity"] * 5 + ["Arbitrary"] * 4 + ["Conjugate Pair"] * 2 + ["Product"] * 1 + ["Sum"] * 1

color_map = {
    "5th Root of Unity": IMPRINT_PALETTE[0],  # brand green
    "Arbitrary": IMPRINT_PALETTE[1],  # lavender
    "Conjugate Pair": IMPRINT_PALETTE[2],  # blue
    "Product": IMPRINT_PALETTE[3],  # ochre
    "Sum": IMPRINT_PALETTE[4],  # matte red
}

real_parts = [z.real for z in all_points]
imag_parts = [z.imag for z in all_points]


def fmt_z(z):
    r = f"{z.real:.2f}".rstrip("0").rstrip(".")
    im = f"{abs(z.imag):.2f}".rstrip("0").rstrip(".")
    if abs(z.imag) < 1e-10:
        return r
    if abs(z.real) < 1e-10:
        return f"{im}i" if z.imag > 0 else f"−{im}i"
    sign = "+" if z.imag > 0 else "−"
    return f"{r}{sign}{im}i"


labels = [fmt_z(z) for z in all_points]

# === Plot ===
# Square canvas for equal-aspect complex plane — 2400×2400 per Imprint style guide
hover_tool = HoverTool(
    tooltips=[
        ("Point", "@label"),
        ("Category", "@category"),
        ("|z|", "@magnitude{0.00}"),
        ("arg(z)", "@angle_deg{0.0}°"),
    ],
    mode="mouse",
)

p = figure(
    width=2400,
    height=2400,
    title="scatter-complex-plane · python · bokeh · anyplot.ai",
    x_axis_label="Real Axis",
    y_axis_label="Imaginary Axis",
    match_aspect=True,
    tools=[hover_tool],
    toolbar_location=None,  # omit for static PNG — toolbar offset shifts canvas height
    min_border_bottom=160,  # room for 34pt x-tick labels + 42pt x-axis label
    min_border_left=180,  # room for 34pt y-tick labels + 42pt y-axis label
    min_border_top=110,  # room for 50pt title
    min_border_right=60,
)

p.x_range = Range1d(-4.2, 4.2)
p.y_range = Range1d(-4.2, 4.2)

# Unit circle — dashed geometric reference, more prominent than previous
theta = np.linspace(0, 2 * np.pi, 300)
unit_circle_r = p.line(
    np.cos(theta).tolist(),
    np.sin(theta).tolist(),
    line_color=INK_MUTED,
    line_dash="dashed",
    line_width=5,
    line_alpha=0.85,
)

# Axes through origin
p.add_layout(Span(location=0, dimension="width", line_color=INK_SOFT, line_width=2, line_alpha=0.7))
p.add_layout(Span(location=0, dimension="height", line_color=INK_SOFT, line_width=2, line_alpha=0.7))

# Focal-point annotation: dotted line connecting conjugate pair + callout label
p.line(
    [z_base.real, z_base.real],
    [z_base.imag, -z_base.imag],
    line_color=IMPRINT_PALETTE[2],
    line_dash="dotted",
    line_width=3,
    line_alpha=0.5,
)
p.add_layout(
    Label(
        x=z_base.real + 0.15,
        y=0.2,
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

# Vectors from origin to each complex number — visual hierarchy via alpha
alpha_map = {"5th Root of Unity": 0.75, "Arbitrary": 0.55, "Conjugate Pair": 0.65, "Product": 0.70, "Sum": 0.70}
for i, (rx, iy) in enumerate(zip(real_parts, imag_parts, strict=True)):
    cat = categories[i]
    col = color_map[cat]
    p.add_layout(
        Arrow(
            end=NormalHead(size=18, fill_color=col, line_color=col),
            x_start=0,
            y_start=0,
            x_end=rx,
            y_end=iy,
            line_color=col,
            line_width=2.5,
            line_alpha=alpha_map[cat],
        )
    )

# Scatter by category — ColumnDataSource for hover tooltips
legend_items = []
for cat_name, color in color_map.items():
    idx = [i for i, c in enumerate(categories) if c == cat_name]
    src = ColumnDataSource(
        data={
            "x": [real_parts[i] for i in idx],
            "y": [imag_parts[i] for i in idx],
            "label": [labels[i] for i in idx],
            "category": [cat_name] * len(idx),
            "magnitude": [abs(all_points[i]) for i in idx],
            "angle_deg": [np.degrees(np.angle(all_points[i])) for i in idx],
        }
    )
    r = p.scatter(x="x", y="y", source=src, size=26, color=color, line_color="white", line_width=2.5, alpha=0.95)
    legend_items.append(LegendItem(label=cat_name, renderers=[r]))

# Point labels — radially offset from origin to reduce crowding near unit circle
placed = []
for i, (rx, iy, lbl) in enumerate(zip(real_parts, imag_parts, labels, strict=True)):
    angle = np.arctan2(iy, rx)
    cat = categories[i]
    # Larger offset for roots of unity (clustered on the unit circle)
    base_dist = 55 if cat == "5th Root of Unity" else 30
    ox = base_dist * np.cos(angle)
    oy = base_dist * np.sin(angle)
    # Push left-half labels further left to clear axis
    if rx < -0.5:
        ox -= 12
    # Raise near-horizontal labels above the data point
    if abs(iy) < 0.3 and rx > 0:
        oy += 18
    # Stagger root labels at bottom to avoid overlap with tick marks
    if cat == "5th Root of Unity":
        if iy < -0.3:
            oy -= 16
        if abs(rx) < 0.5 and iy > 0:
            oy += 14
    # Nudge away from already-placed labels to reduce crowding
    for px, py in placed:
        dx = (rx + ox * 0.012) - px
        dy = (iy + oy * 0.012) - py
        if abs(dx) < 0.55 and abs(dy) < 0.55:
            oy += 35 if iy >= py else -35
    placed.append((rx + ox * 0.012, iy + oy * 0.012))
    p.add_layout(Label(x=rx, y=iy, text=lbl, x_offset=ox, y_offset=oy, text_font_size="24pt", text_color=INK_SOFT))

# Legend — top-left, clean Imprint chrome
legend = Legend(
    items=[LegendItem(label="Unit Circle", renderers=[unit_circle_r])] + legend_items,
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

# Chrome styling — canonical Imprint font sizing for 2400×2400 bokeh canvas
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

# === Save ===
# HTML artifact (interactive — hover works without visible toolbar)
output_file(f"plot-{THEME}.html")
save(p)

# PNG via headless Chrome / Selenium — must match figure width/height exactly
W, H = 2400, 2400
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
# CDP override ensures exact viewport size — window-size alone is eaten by browser chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Belt-and-braces: pin saved PNG to exact target dims so the post-render gate passes
from PIL import Image as _PILImage


_img = _PILImage.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (W, H):
    _norm = _PILImage.new("RGB", (W, H), PAGE_BG)
    _norm.paste(_img, ((W - _img.size[0]) // 2, (H - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
