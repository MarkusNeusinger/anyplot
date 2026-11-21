""" anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: pygal 3.1.3 | Python 3.14.10
Quality: 77/100 | Updated: 2026-11-21
"""

import os
from io import BytesIO

import cairosvg
import numpy as np
import pandas as pd
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LAYOUT = "AAB;AAC;DDF"  # mosaic pattern: repeated letters span cells, an unused letter (F) stays blank
CANVAS_W, CANVAS_H = 3200, 1800
TITLE_H = 110  # band above the grid for the figure title
PAD = 30  # outer margin
GAP = 24  # spacing between neighbouring panels

# Columns: set these to your table's column names
PANEL = "Panel"  # role: extra
SERIES = "Series"  # role: extra
X = "x"  # role: x
Y = "y"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("panels.csv")
# One long table: each row belongs to the layout letter in PANEL
#   A = revenue and costs by month, B = sales by category, C = share by region, D = marketing spend vs sales
rng = np.random.default_rng(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
revenue = [120, 135, 142, 138, 155, 168, 172, 185, 178, 192, 205, 218]
costs = [85, 88, 92, 90, 98, 105, 108, 115, 112, 120, 128, 135]
categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]
category_sales = [450, 320, 280, 195, 165]
regions = ["North", "South", "East", "West"]
region_shares = [35, 28, 22, 15]
marketing_spend = rng.uniform(10, 100, 40)
sales_response = marketing_spend * 2.5 + rng.normal(0, 25, 40)

df = pd.concat(
    [
        pd.DataFrame({PANEL: "A", SERIES: "Revenue", X: months, Y: revenue}),
        pd.DataFrame({PANEL: "A", SERIES: "Costs", X: months, Y: costs}),
        pd.DataFrame({PANEL: "B", SERIES: categories, X: categories, Y: category_sales}),
        pd.DataFrame({PANEL: "C", SERIES: regions, X: regions, Y: region_shares}),
        pd.DataFrame({PANEL: "D", SERIES: "Accounts", X: marketing_spend, Y: sales_response}),
    ],
    ignore_index=True,
)

# Plot
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    font_family="sans-serif",
    title_font_size=44,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=28,
    value_font_size=26,
    stroke_width=4,
)

# Grid geometry from the layout string: bounding box of every letter in cells
grid = LAYOUT.split(";")
n_rows, n_cols = len(grid), len(grid[0])
cell_w = (CANVAS_W - 2 * PAD + GAP) / n_cols
cell_h = (CANVAS_H - TITLE_H - PAD + GAP) / n_rows
boxes = {}
for r, row in enumerate(grid):
    for c, letter in enumerate(row):
        r0, c0, r1, c1 = boxes.get(letter, (r, c, r, c))
        boxes[letter] = (min(r0, r), min(c0, c), max(r1, r), max(c1, c))


def panel_size(letter):
    r0, c0, r1, c1 = boxes[letter]
    return round((c1 - c0 + 1) * cell_w - GAP), round((r1 - r0 + 1) * cell_h - GAP)


def panel_origin(letter):
    r0, c0, _, _ = boxes[letter]
    return round(PAD + c0 * cell_w), round(TITLE_H + r0 * cell_h)


def sub(letter):
    return df[df[PANEL] == letter]


# Panel A: the largest cell holds the primary series, revenue against costs over time
panel_a = pygal.Line(
    width=panel_size("A")[0],
    height=panel_size("A")[1],
    style=style,
    truncate_label=-1,
    legend_at_bottom=True,
    show_y_guides=True,
    show_x_guides=False,
    x_title="Month",
    y_title="Amount ($K)",
    title="Monthly Revenue vs Costs",
    dots_size=9,
)
series_a = sub("A")
panel_a.x_labels = list(dict.fromkeys(series_a[X]))
for name, part in series_a.groupby(SERIES, sort=False):
    panel_a.add(str(name), part[Y].tolist())

# Panel B: sales by category as horizontal bars
panel_b = pygal.HorizontalBar(
    width=panel_size("B")[0],
    height=panel_size("B")[1],
    style=style,
    truncate_label=-1,
    show_legend=False,
    show_y_guides=True,
    title="Sales by Category",
    print_values=True,
    print_values_position="center",
)
for _, row in sub("B").iterrows():
    panel_b.add(str(row[SERIES]), row[Y])

# Panel C: regional share as a donut
panel_c = pygal.Pie(
    width=panel_size("C")[0],
    height=panel_size("C")[1],
    style=style,
    truncate_label=-1,
    legend_at_bottom=True,
    title="Regional Share",
    inner_radius=0.4,
)
for _, row in sub("C").iterrows():
    panel_c.add(str(row[SERIES]), row[Y])

# Panel D: marketing spend against sales response
panel_d = pygal.XY(
    width=panel_size("D")[0],
    height=panel_size("D")[1],
    style=style,
    truncate_label=-1,
    show_legend=False,
    show_y_guides=True,
    x_title="Marketing Spend ($K)",
    y_title="Sales ($K)",
    title="Marketing ROI Correlation",
    stroke=False,
    dots_size=10,
)
scatter = sub("D")
panel_d.add("Accounts", list(zip(scatter[X].astype(float), scatter[Y].astype(float), strict=True)))

panels = {"A": panel_a, "B": panel_b, "C": panel_c, "D": panel_d}

# Compose: rasterize each pygal SVG and paste it at its place in the grid
combined = Image.new("RGB", (CANVAS_W, CANVAS_H), PAGE_BG)
for letter, chart in panels.items():
    w, h = panel_size(letter)
    png = cairosvg.svg2png(bytestring=chart.render(), output_width=w, output_height=h)
    combined.paste(Image.open(BytesIO(png)).convert("RGB"), panel_origin(letter))

TITLE = "subplot-mosaic · python · pygal · anyplot.ai"
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
except OSError:
    title_font = ImageFont.load_default()
draw = ImageDraw.Draw(combined)
left, _, right, _ = draw.textbbox((0, 0), TITLE, font=title_font)
draw.text(((CANVAS_W - (right - left)) // 2, 28), TITLE, fill=INK, font=title_font)

combined.save(f"plot-{THEME}.png")

# Interactive HTML: the same grid in CSS, with each pygal SVG inlined
areas = "".join(f'"{" ".join(row)}" ' for row in grid)
cells = "".join(
    f'<div style="grid-area: {letter}">{chart.render(is_unicode=True).split("?>", 1)[-1]}</div>'
    for letter, chart in panels.items()
)
html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{TITLE}</title>
<style>
body {{ font-family: sans-serif; background: {PAGE_BG}; margin: 20px; }}
h1 {{ text-align: center; color: {INK}; font-size: 32px; }}
.mosaic {{ display: grid; grid-template-areas: {areas}; gap: {GAP // 2}px; max-width: 1600px;
  margin: 0 auto; aspect-ratio: {CANVAS_W} / {CANVAS_H - TITLE_H}; }}
.mosaic svg {{ width: 100%; height: 100%; }}
</style>
</head>
<body>
<h1>{TITLE}</h1>
<div class="mosaic">{cells}</div>
</body>
</html>"""
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html)
