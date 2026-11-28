"""anyplot.ai
heatmap-periodic-table: Periodic Table Property Heatmap
Library: pygal 3.1.3 | Python 3.14.10
Quality: 75/100 | Updated: 2026-11-28
"""

import math
import os
from itertools import pairwise

import cairosvg
import pandas as pd
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GREY_TILE = "#CCCBC3" if THEME == "light" else "#3A3A36"

FONT = "DejaVu Sans, Helvetica, Arial, sans-serif"

# Imprint palette (all eight positions, canonical order)
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Imprint sequential ramp for colored cells that fill the plot (fields stops of the theme)
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Columns: set these to your table's column names
SYMBOL = "Symbol"  # role: symbol
ATOMIC_NUMBER = "Atomic number"  # role: atomic_number
GROUP = "Group"  # role: group
PERIOD = "Period"  # role: period
ELECTRONEGATIVITY = "Pauling Electronegativity"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("elements.csv")
# Element data: (symbol, atomic_number, group[1-18], period/row[1-9], en_or_None)
# grid_row 1-7 = periods 1-7 in the main 18-column table
# grid_row 8   = lanthanide f-block row (La-Lu at cols 3-17)
# grid_row 9   = actinide  f-block row (Ac-Lr at cols 3-17)
# Group 3 of periods 6 and 7 stays empty; the f-block rows sit detached below.
elements = [
    # Period 1
    ("H", 1, 1, 1, 2.20),
    ("He", 2, 18, 1, None),
    # Period 2
    ("Li", 3, 1, 2, 0.98),
    ("Be", 4, 2, 2, 1.57),
    ("B", 5, 13, 2, 2.04),
    ("C", 6, 14, 2, 2.55),
    ("N", 7, 15, 2, 3.04),
    ("O", 8, 16, 2, 3.44),
    ("F", 9, 17, 2, 3.98),
    ("Ne", 10, 18, 2, None),
    # Period 3
    ("Na", 11, 1, 3, 0.93),
    ("Mg", 12, 2, 3, 1.31),
    ("Al", 13, 13, 3, 1.61),
    ("Si", 14, 14, 3, 1.90),
    ("P", 15, 15, 3, 2.19),
    ("S", 16, 16, 3, 2.58),
    ("Cl", 17, 17, 3, 3.16),
    ("Ar", 18, 18, 3, None),
    # Period 4
    ("K", 19, 1, 4, 0.82),
    ("Ca", 20, 2, 4, 1.00),
    ("Sc", 21, 3, 4, 1.36),
    ("Ti", 22, 4, 4, 1.54),
    ("V", 23, 5, 4, 1.63),
    ("Cr", 24, 6, 4, 1.66),
    ("Mn", 25, 7, 4, 1.55),
    ("Fe", 26, 8, 4, 1.83),
    ("Co", 27, 9, 4, 1.88),
    ("Ni", 28, 10, 4, 1.91),
    ("Cu", 29, 11, 4, 1.90),
    ("Zn", 30, 12, 4, 1.65),
    ("Ga", 31, 13, 4, 1.81),
    ("Ge", 32, 14, 4, 2.01),
    ("As", 33, 15, 4, 2.18),
    ("Se", 34, 16, 4, 2.55),
    ("Br", 35, 17, 4, 2.96),
    ("Kr", 36, 18, 4, 3.00),
    # Period 5
    ("Rb", 37, 1, 5, 0.82),
    ("Sr", 38, 2, 5, 0.95),
    ("Y", 39, 3, 5, 1.22),
    ("Zr", 40, 4, 5, 1.33),
    ("Nb", 41, 5, 5, 1.60),
    ("Mo", 42, 6, 5, 2.16),
    ("Tc", 43, 7, 5, 1.90),
    ("Ru", 44, 8, 5, 2.20),
    ("Rh", 45, 9, 5, 2.28),
    ("Pd", 46, 10, 5, 2.20),
    ("Ag", 47, 11, 5, 1.93),
    ("Cd", 48, 12, 5, 1.69),
    ("In", 49, 13, 5, 1.78),
    ("Sn", 50, 14, 5, 1.96),
    ("Sb", 51, 15, 5, 2.05),
    ("Te", 52, 16, 5, 2.10),
    ("I", 53, 17, 5, 2.66),
    ("Xe", 54, 18, 5, 2.60),
    # Period 6 — group 3 is a gap (La-Lu sit in the detached row)
    ("Cs", 55, 1, 6, 0.79),
    ("Ba", 56, 2, 6, 0.89),
    ("Hf", 72, 4, 6, 1.30),
    ("Ta", 73, 5, 6, 1.50),
    ("W", 74, 6, 6, 2.36),
    ("Re", 75, 7, 6, 1.90),
    ("Os", 76, 8, 6, 2.20),
    ("Ir", 77, 9, 6, 2.20),
    ("Pt", 78, 10, 6, 2.28),
    ("Au", 79, 11, 6, 2.54),
    ("Hg", 80, 12, 6, 2.00),
    ("Tl", 81, 13, 6, 1.62),
    ("Pb", 82, 14, 6, 2.33),
    ("Bi", 83, 15, 6, 2.02),
    ("Po", 84, 16, 6, 2.00),
    ("At", 85, 17, 6, 2.20),
    ("Rn", 86, 18, 6, 2.20),
    # Period 7 — group 3 is a gap (Ac-Lr sit in the detached row); Rf-Og have no EN
    ("Fr", 87, 1, 7, 0.70),
    ("Ra", 88, 2, 7, 0.90),
    ("Rf", 104, 4, 7, None),
    ("Db", 105, 5, 7, None),
    ("Sg", 106, 6, 7, None),
    ("Bh", 107, 7, 7, None),
    ("Hs", 108, 8, 7, None),
    ("Mt", 109, 9, 7, None),
    ("Ds", 110, 10, 7, None),
    ("Rg", 111, 11, 7, None),
    ("Cn", 112, 12, 7, None),
    ("Nh", 113, 13, 7, None),
    ("Fl", 114, 14, 7, None),
    ("Mc", 115, 15, 7, None),
    ("Lv", 116, 16, 7, None),
    ("Ts", 117, 17, 7, None),
    ("Og", 118, 18, 7, None),
    # Lanthanide f-block row (row 8, cols 3-17 = La through Lu)
    ("La", 57, 3, 8, 1.10),
    ("Ce", 58, 4, 8, 1.12),
    ("Pr", 59, 5, 8, 1.13),
    ("Nd", 60, 6, 8, 1.14),
    ("Pm", 61, 7, 8, 1.13),
    ("Sm", 62, 8, 8, 1.17),
    ("Eu", 63, 9, 8, 1.20),
    ("Gd", 64, 10, 8, 1.20),
    ("Tb", 65, 11, 8, 1.10),
    ("Dy", 66, 12, 8, 1.22),
    ("Ho", 67, 13, 8, 1.23),
    ("Er", 68, 14, 8, 1.24),
    ("Tm", 69, 15, 8, 1.25),
    ("Yb", 70, 16, 8, 1.10),
    ("Lu", 71, 17, 8, 1.27),
    # Actinide f-block row (row 9, cols 3-17 = Ac through Lr)
    ("Ac", 89, 3, 9, 1.10),
    ("Th", 90, 4, 9, 1.30),
    ("Pa", 91, 5, 9, 1.50),
    ("U", 92, 6, 9, 1.38),
    ("Np", 93, 7, 9, 1.36),
    ("Pu", 94, 8, 9, 1.28),
    ("Am", 95, 9, 9, 1.30),
    ("Cm", 96, 10, 9, 1.30),
    ("Bk", 97, 11, 9, 1.30),
    ("Cf", 98, 12, 9, 1.30),
    ("Es", 99, 13, 9, 1.30),
    ("Fm", 100, 14, 9, 1.30),
    ("Md", 101, 15, 9, 1.30),
    ("No", 102, 16, 9, 1.30),
    ("Lr", 103, 17, 9, 1.30),
]

df = pd.DataFrame(elements, columns=[SYMBOL, ATOMIC_NUMBER, GROUP, PERIOD, ELECTRONEGATIVITY])

# Plot: reads only df and the constants above
EN_MIN = df[ELECTRONEGATIVITY].min()  # 0.70  (Fr)
EN_MAX = df[ELECTRONEGATIVITY].max()  # 3.98  (F)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return GREY_TILE  # an element without a value is a grey tile outside the ramp
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


def relative_luminance(hex_c):
    vals = [int(hex_c[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in vals]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def svg_node(parent, tag, text=None, **attrs):
    """Append one SVG element (tag, attributes, text, children) to the list parent; return its children list."""
    children = []
    parent.append((tag, {k.replace("_", "-"): v for k, v in attrs.items()}, text, children))
    return children


def svg_xml(nodes):
    """Serialize the nodes of svg_node to an SVG fragment."""
    return "".join(
        f"<{tag}{''.join(f' {k}="{v}"' for k, v in attrs.items())}>{'' if text is None else text}{svg_xml(kids)}</{tag}>"
        for tag, attrs, text, kids in nodes
    )


# Canvas and layout: landscape 3200x1800 (the periodic table is wider than tall)
CANVAS_W = 3200
CANVAS_H = 1800
TILE = 158  # tile side length (px)
GAP = 8  # gap between tiles (px)
STRIDE = TILE + GAP
GRID_W = 17 * STRIDE + TILE
LEFT = (CANVAS_W - GRID_W) // 2  # left edge of column 1
TOP = 150  # top edge of the period-1 tiles
FBLOCK_EXTRA = 44  # extra gap between period 7 and the f-block rows
F_TOP = TOP + 6 * STRIDE + TILE + FBLOCK_EXTRA  # top edge of the lanthanide row

# The empty space above groups 4-11 in periods 1-3 holds the color bar
CB_X = LEFT + 3 * STRIDE
CB_W = 8 * STRIDE - GAP
CB_Y = TOP + 130
CB_H = 52

TITLE_TEXT = "heatmap-periodic-table · python · pygal · anyplot.ai"

# Pygal Style carries all theme tokens into the rendering engine
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.Bar(
    width=CANVAS_W,
    height=CANVAS_H,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    style=custom_style,
    margin=0,
)
chart.add(ELECTRONEGATIVITY, [EN_MIN])  # pygal needs one series before it renders

# Plot: pygal builds the SVG tree, the tiles and chrome are added to its root
root = []
svg_node(root, "rect", x=0, y=0, width=CANVAS_W, height=CANVAS_H, fill=PAGE_BG)  # covers the placeholder bar
svg_node(
    root,
    "text",
    TITLE_TEXT,
    x=CANVAS_W // 2,
    y=88,
    text_anchor="middle",
    fill=INK,
    style=f"font-size:66px;font-weight:500;font-family:{FONT}",
)

# Group numbers above the tiles, period numbers and Ln/An labels to the left
index_style = f"font-size:44px;font-family:{FONT}"
for g in range(1, 19):
    svg_node(
        root, "text", g, x=LEFT + (g - 1) * STRIDE + TILE / 2, y=TOP - 18, text_anchor="middle", fill=INK_MUTED,
        style=index_style,
    )  # fmt: skip
for p in range(1, 8):
    svg_node(
        root, "text", p, x=LEFT - 22, y=TOP + (p - 1) * STRIDE + TILE / 2 + 15, text_anchor="end", fill=INK_MUTED,
        style=index_style,
    )  # fmt: skip
for i, label in enumerate(["Ln", "An"]):
    svg_node(
        root, "text", label, x=LEFT - 22, y=F_TOP + i * STRIDE + TILE / 2 + 15, text_anchor="end", fill=INK_MUTED,
        style=index_style + ";font-style:italic",
    )  # fmt: skip

# Group 3 gap of periods 6 and 7: a dashed outline names the detached rows that fill it
for i, (period, span) in enumerate([(6, "57–71"), (7, "89–103")]):
    gx, gy = LEFT + 2 * STRIDE, TOP + (period - 1) * STRIDE
    svg_node(
        root, "rect", x=gx, y=gy, width=TILE, height=TILE, rx=3, fill="none", stroke=INK_MUTED, stroke_width=2,
        stroke_dasharray="8,6", stroke_opacity=0.6,
    )  # fmt: skip
    svg_node(
        root, "text", span, x=gx + TILE / 2, y=gy + TILE / 2 + 11, text_anchor="middle", fill=INK_MUTED,
        style=f"font-size:32px;font-family:{FONT}",
    )  # fmt: skip
    svg_node(
        root, "line", x1=gx + TILE / 2, y1=gy + TILE, x2=gx + TILE / 2, y2=F_TOP + i * STRIDE, stroke=INK_MUTED,
        stroke_width=2, stroke_dasharray="8,6", stroke_opacity=0.5,
    )  # fmt: skip

# Element tiles: symbol centered, atomic number top-left, value at the bottom
for sym, an, col, row, en in df[[SYMBOL, ATOMIC_NUMBER, GROUP, PERIOD, ELECTRONEGATIVITY]].itertuples(index=False):
    x = LEFT + (col - 1) * STRIDE
    y = TOP + (row - 1) * STRIDE if row <= 7 else F_TOP + (row - 8) * STRIDE
    fill = ramp_color(SEQ_FIELDS, (en - EN_MIN) / (EN_MAX - EN_MIN))
    ink = "#F0EFE8" if relative_luminance(fill) < 0.35 else "#1A1A17"
    tile = svg_node(root, "g")
    svg_node(tile, "title", f"{sym} (Z={an})" + (f": {en:.2f}" if pd.notna(en) else ": no value"))
    svg_node(tile, "rect", x=x, y=y, width=TILE, height=TILE, rx=3, fill=fill)
    svg_node(tile, "text", an, x=x + 8, y=y + 30, fill=ink, style=f"font-size:28px;font-family:{FONT}")
    svg_node(
        tile, "text", sym, x=x + TILE / 2, y=y + TILE / 2 + 20, text_anchor="middle", fill=ink,
        style=f"font-size:52px;font-weight:700;font-family:{FONT}",
    )  # fmt: skip
    if pd.notna(en):
        svg_node(
            tile, "text", f"{en:.2f}", x=x + TILE / 2, y=y + TILE - 12, text_anchor="middle", fill=ink,
            style=f"font-size:28px;font-family:{FONT}",
        )  # fmt: skip

# Color bar in the empty upper block, with its own gradient stops from the ramp
grad = svg_node(svg_node(root, "defs"), "linearGradient", id="cbGrad", x1=0, y1=0, x2=1, y2=0)
for pos, hex_c in SEQ_FIELDS:
    svg_node(grad, "stop", offset=f"{pos * 100:.1f}%", stop_color=hex_c)
svg_node(
    root, "text", ELECTRONEGATIVITY, x=CB_X + CB_W / 2, y=CB_Y - 28, text_anchor="middle", fill=INK,
    style=f"font-size:56px;font-family:{FONT}",
)  # fmt: skip
svg_node(root, "rect", x=CB_X, y=CB_Y, width=CB_W, height=CB_H, rx=4, fill="url(#cbGrad)")
ticks = [EN_MIN] + [v for v in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5) if EN_MIN < v < EN_MAX] + [EN_MAX]
for val in ticks:
    tx = CB_X + (val - EN_MIN) / (EN_MAX - EN_MIN) * CB_W
    svg_node(root, "line", x1=tx, y1=CB_Y + CB_H, x2=tx, y2=CB_Y + CB_H + 12, stroke=INK_SOFT, stroke_width=2)
    svg_node(
        root, "text", f"{val:.2f}" if val in (EN_MIN, EN_MAX) else f"{val:.1f}", x=tx, y=CB_Y + CB_H + 58,
        text_anchor="middle", fill=INK_SOFT, style=f"font-size:44px;font-family:{FONT}",
    )  # fmt: skip

# Save: PNG through cairosvg, interactive SVG (with tooltips) as the HTML view
svg_text = chart.render(is_unicode=True).replace("</svg>", svg_xml(root) + "</svg>")
cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as fh:
    fh.write(svg_text)
