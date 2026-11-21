"""anyplot.ai
icicle-basic: Basic Icicle Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
"""

import os
import sys


sys.path.pop(0)

import cairosvg
import pandas as pd
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: one color per hierarchy level, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Label colors drawn inside the rectangles (fills are the same in both themes)
LABEL_DARK = "#1A1A17"
LABEL_LIGHT = "#FAF8F1"

# Columns: set these to your table's column names
NODE = "name"  # role: name
PARENT = "parent"  # role: parent
VALUE = "value"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("hierarchy.csv")
# Organizational hierarchy (Company -> Divisions -> Departments -> Teams); values sit on the leaves
df = pd.DataFrame(
    [
        ("TechCorp", None, None),
        ("Engineering", "TechCorp", None),
        ("Operations", "TechCorp", None),
        ("Sales", "TechCorp", None),
        ("Backend", "Engineering", None),
        ("Frontend", "Engineering", None),
        ("DevOps", "Engineering", None),
        ("HR", "Operations", None),
        ("Finance", "Operations", None),
        ("APAC", "Sales", None),
        ("EMEA", "Sales", None),
        ("APIs", "Backend", 45),
        ("Databases", "Backend", 50),
        ("Services", "Backend", 40),
        ("Web", "Frontend", 35),
        ("Mobile", "Frontend", 30),
        ("Infrastructure", "DevOps", 55),
        ("Recruiting", "HR", 25),
        ("Payroll", "HR", 15),
        ("Accounting", "Finance", 35),
        ("Planning", "Finance", 25),
        ("Enterprise", "APAC", 60),
        ("SMB", "APAC", 40),
        ("EMEA Enterprise", "EMEA", 70),
        ("EMEA SMB", "EMEA", 50),
    ],
    columns=[NODE, PARENT, VALUE],
)

# Plot
# Tree structure from the parent column
children = {}
for name, parent in zip(df[NODE], df[PARENT], strict=True):
    if pd.notna(parent):
        children.setdefault(parent, []).append(name)
root = df.loc[df[PARENT].isna(), NODE].iloc[0]
leaf_value = dict(zip(df[NODE], df[VALUE], strict=True))


def total(name):
    """Value of a node: its own value for a leaf, the sum of its children otherwise."""
    if name not in children:
        return leaf_value[name]
    return sum(total(child) for child in children[name])


# Layout: x extent as a share of the root, depth as the row
positions = {root: (0.0, 1.0, 0)}
order = [root]
for name in order:
    x0, x1, depth = positions[name]
    cursor = x0
    for child in children.get(name, []):
        share = total(child) / total(name) * (x1 - x0)
        positions[child] = (cursor, cursor + share, depth + 1)
        cursor += share
        order.append(child)
max_depth = max(depth for _, _, depth in positions.values())
# Row labels follow the number of levels; the first four are the sample's domain names
level_labels = ["Company", "Division", "Department", "Team"]

# Canvas: 3200 x 1800 landscape
WIDTH = 3200
HEIGHT = 1800
MARGIN_TOP = 170
MARGIN_BOTTOM = 70
MARGIN_LEFT = 60
MARGIN_RIGHT = 330
PLOT_WIDTH = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PLOT_HEIGHT = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
row_height = PLOT_HEIGHT / (max_depth + 1)
GAP = 4
LABEL_SIZE = 44
CHAR_WIDTH = 0.66  # average glyph width as a share of the font size
TITLE_SIZE = 66

# pygal Style carries the theme tokens and the palette
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=TITLE_SIZE,
    label_font_size=LABEL_SIZE,
    major_label_font_size=LABEL_SIZE,
    legend_font_size=LABEL_SIZE,
)


def luminance(hex_color):
    """Relative luminance of a #RRGGBB color."""
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def label_color(fill):
    """Pick the label color with the higher contrast against the fill."""
    lum = luminance(fill)
    contrast_dark = (lum + 0.05) / (luminance(LABEL_DARK) + 0.05)
    contrast_light = (luminance(LABEL_LIGHT) + 0.05) / (lum + 0.05)
    return LABEL_DARK if contrast_dark >= contrast_light else LABEL_LIGHT


# Build the SVG by hand: pygal has no icicle chart type
def esc(text):
    """Escape text for SVG content."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
    f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="{custom_style.background}"/>',
    f'<text x="{WIDTH / 2}" y="105" text-anchor="middle" fill="{custom_style.foreground_strong}" '
    f'font-size="{custom_style.title_font_size}" font-family="sans-serif" font-weight="500">'
    "icicle-basic · python · pygal · anyplot.ai</text>",
    '<g class="icicle-chart">',
]

for name, (x0, x1, depth) in positions.items():
    px_x = MARGIN_LEFT + x0 * PLOT_WIDTH
    px_width = (x1 - x0) * PLOT_WIDTH - GAP
    px_y = MARGIN_TOP + depth * row_height
    px_height = row_height - GAP
    fill = custom_style.colors[depth]
    label = str(name)

    parts.append(
        f'<rect x="{px_x:.1f}" y="{px_y:.1f}" width="{max(0, px_width):.1f}" height="{px_height:.1f}" fill="{fill}">'
        f"<title>{esc(label)}: {total(name):g}</title></rect>"
    )
    # Label only where the text fits inside its own rectangle
    if len(label) * LABEL_SIZE * CHAR_WIDTH <= px_width - 24:
        parts.append(
            f'<text x="{px_x + px_width / 2:.1f}" y="{px_y + px_height / 2:.1f}" text-anchor="middle" '
            f'dominant-baseline="central" fill="{label_color(fill)}" font-size="{LABEL_SIZE}" '
            f'font-family="sans-serif" font-weight="500">{esc(label)}</text>'
        )
parts.append("</g>")

# Level names on the right
parts.append('<g class="level-labels">')
for depth in range(max_depth + 1):
    level_label = level_labels[depth] if depth < len(level_labels) else f"Level {depth + 1}"
    parts.append(
        f'<text x="{MARGIN_LEFT + PLOT_WIDTH + 36}" y="{MARGIN_TOP + (depth + 0.5) * row_height:.1f}" '
        f'dominant-baseline="central" fill="{INK_SOFT}" font-size="{LABEL_SIZE}" '
        f'font-family="sans-serif">{esc(level_label)}</text>'
    )
parts.append("</g></svg>")
svg_output = "".join(parts)

with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg_output)

cairosvg.svg2png(bytestring=svg_output.encode("utf-8"), write_to=f"plot-{THEME}.png")
