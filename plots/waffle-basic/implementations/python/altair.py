""" anyplot.ai
waffle-basic: Basic Waffle Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GRID_SIDE = 10  # standard 10x10 waffle: every square is 1% of the whole

# Columns: set these to your table's column names
CATEGORY = "Category"  # role: category
VALUE = "Share of budget (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("budget.csv")
df = pd.DataFrame({CATEGORY: ["Engineering", "Marketing", "Operations", "Design", "Legal"], VALUE: [40, 28, 18, 10, 4]})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
LEGEND_LABEL = "Category (share)"
ROW, COL = "row", "col"

# Whole squares per category: cumulative rounding keeps the grid exactly full
cells = GRID_SIDE * GRID_SIDE
table = df.dropna(subset=[VALUE]).reset_index(drop=True)
shares = table[VALUE].astype(float) / table[VALUE].astype(float).sum()
edges = (shares.cumsum() * cells).round().astype(int).tolist()
counts = pd.Series(edges).diff().fillna(edges[0]).astype(int).tolist()

squares = []
for name, value, count in zip(table[CATEGORY], shares, counts, strict=True):
    for _ in range(count):
        idx = len(squares)
        squares.append(
            {CATEGORY: name, LEGEND_LABEL: f"{name} ({value:.0%})", ROW: idx // GRID_SIDE, COL: idx % GRID_SIDE}
        )
grid = pd.DataFrame(squares)
legend_order = [f"{name} ({value:.0%})" for name, value in zip(table[CATEGORY], shares, strict=True)]

title = "Budget Allocation · waffle-basic · python · altair · anyplot.ai"

chart = (
    alt.Chart(grid)
    .mark_rect(stroke=PAGE_BG, strokeWidth=4, cornerRadius=5)
    .encode(
        x=alt.X(f"{COL}:O", axis=None),
        y=alt.Y(f"{ROW}:O", axis=None),
        color=alt.Color(
            LEGEND_LABEL.translate(ESCAPE),
            type="nominal",
            title=LEGEND_LABEL,
            sort=None,
            scale=alt.Scale(domain=legend_order, range=IMPRINT_PALETTE[: len(legend_order)]),
            legend=alt.Legend(
                titleFontSize=18,
                labelFontSize=16,
                symbolType="square",
                symbolSize=500,
                orient="right",
                padding=12,
                rowPadding=8,
            ),
        ),
        tooltip=[alt.Tooltip(CATEGORY.translate(ESCAPE), title=CATEGORY)],
    )
    .properties(
        width=340, height=340, background=PAGE_BG, title=alt.Title(title, fontSize=15, anchor="middle", color=INK)
    )
    .configure_view(fill=None, stroke=None)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK, titleColor=INK)
)

# Save outputs, padded (never cropped) to the 2400 x 2400 square canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    # Other data can widen the legend or title: shrink to fit, never crop
    fit = min(TARGET / img.width, TARGET / img.height)
    img = img.resize((int(img.width * fit), int(img.height * fit)), Image.LANCZOS)
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
