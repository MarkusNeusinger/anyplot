"""anyplot.ai
icicle-basic: Basic Icicle Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
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

# Imprint palette: one color per hierarchy level, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LEVEL = "Level"  # derived column: depth of a node in the hierarchy
VIEW_WIDTH = 620  # inner view in px; the saved PNG is this times scale_factor plus title and legend padding
LABEL_PX = 6.5  # estimated width of one label character in view px, decides which nodes get a label

# Columns: set these to your table's column names
NAME = "Name"  # role: name
PARENT = "Parent"  # role: parent
VALUE = "Size (MB)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("files.csv")
# Only leaves carry a size; a folder's size is the sum of its children.
df = pd.DataFrame(
    {
        NAME: [
            "root",
            "Documents",
            "Media",
            "Projects",
            "Reports",
            "Presentations",
            "Images",
            "Videos",
            "WebApp",
            "DataScience",
            "Q1_Report.pdf",
            "Q2_Report.pdf",
            "Annual_Review.pdf",
            "Sales_Deck.pptx",
            "Strategy.pptx",
            "photo_album.jpg",
            "banner.png",
            "tutorial.mp4",
            "demo.mp4",
            "frontend.js",
            "backend.py",
            "styles.css",
            "analysis.ipynb",
            "model.pkl",
        ],
        PARENT: [None, "root", "root", "root"]
        + ["Documents"] * 2
        + ["Media"] * 2
        + ["Projects"] * 2
        + ["Reports"] * 3
        + ["Presentations"] * 2
        + ["Images"] * 2
        + ["Videos"] * 2
        + ["WebApp"] * 3
        + ["DataScience"] * 2,
        VALUE: [None] * 10 + [120, 95, 150, 85, 110, 180, 75, 350, 280, 65, 120, 45, 95, 180],
    }
)

# Plot: reads only df and the constants above
children = df.groupby(PARENT, sort=False)[NAME].apply(list).to_dict()
leaf_value = df.set_index(NAME)[VALUE]
root = df.loc[df[PARENT].isna(), NAME].iloc[0]


def subtree_total(node):
    """Total size under a node: its own value for a leaf, the sum of its children otherwise."""
    if node not in children:
        return leaf_value[node]
    return sum(subtree_total(child) for child in children[node])


# Lay out: breadth-first so every parent is placed before its children
rows = []
queue = [(root, 0, 0.0, 1.0)]
while queue:
    node, level, x0, x1 = queue.pop(0)
    rows.append({NAME: node, LEVEL: level, "x0": x0, "x1": x1, VALUE: subtree_total(node)})
    kids = children.get(node, [])
    total = sum(subtree_total(k) for k in kids)
    cursor = x0
    for kid in kids:
        width = (x1 - x0) * subtree_total(kid) / total
        queue.append((kid, level + 1, cursor, cursor + width))
        cursor += width
rect = pd.DataFrame(rows)
rect["row"] = rect[LEVEL]
rect["row_end"] = rect[LEVEL] + 1
rect["mid_x"] = (rect["x0"] + rect["x1"]) / 2
rect["mid_row"] = rect[LEVEL] + 0.5
n_levels = rect[LEVEL].max() + 1

# Label only where the name fits inside its rectangle
fits = (rect["x1"] - rect["x0"]) * VIEW_WIDTH > rect[NAME].str.len() * LABEL_PX + 8
rect["label"] = rect[NAME].where(fits, "")

# Dark text on light fills, white text on dark fills (by perceived brightness of the level color)
fills = [IMPRINT_PALETTE[i] for i in range(n_levels)]


def brightness(hex_color):
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b


rect["ink"] = rect[LEVEL].map(lambda lv: "#1A1A17" if brightness(fills[lv]) > 130 else "#FFFFFF")

ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
level_scale = alt.Scale(domain=list(range(n_levels)), range=fills)
row_scale = alt.Scale(domain=[0, n_levels], reverse=True)

blocks = (
    alt.Chart(rect)
    .mark_rect(stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        x=alt.X("x0:Q", axis=None, scale=alt.Scale(domain=[0, 1], nice=False)),
        x2="x1:Q",
        y=alt.Y("row:Q", axis=None, scale=row_scale),
        y2="row_end:Q",
        color=alt.Color(LEVEL, type="ordinal", title=LEVEL, scale=level_scale),
        tooltip=[
            alt.Tooltip(NAME.translate(ESCAPE), type="nominal", title=NAME),
            alt.Tooltip(VALUE.translate(ESCAPE), type="quantitative", title=VALUE),
            alt.Tooltip(LEVEL, type="ordinal", title=LEVEL),
        ],
    )
)

labels = (
    alt.Chart(rect)
    .mark_text(fontSize=10, fontWeight="bold")
    .encode(
        x=alt.X("mid_x:Q", axis=None, scale=alt.Scale(domain=[0, 1], nice=False)),
        y=alt.Y("mid_row:Q", axis=None, scale=row_scale),
        text="label:N",
        color=alt.Color("ink:N", scale=None),
    )
)

title = "icicle-basic · python · altair · anyplot.ai"
icicle = (
    (blocks + labels)
    .properties(width=VIEW_WIDTH, height=320, background=PAGE_BG, title=alt.Title(title, fontSize=16, color=INK))
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
        padding=8,
    )
)

# Save as PNG and HTML with theme-suffixed names, then pad (never crop) to the 3200 x 1800 target
icicle.save(f"plot-{THEME}.png", scale_factor=4.0)
icicle.save(f"plot-{THEME}.html")

TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
canvas.save(f"plot-{THEME}.png")
