"""anyplot.ai
icicle-basic: Basic Icicle Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-13
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per top-level branch in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(style="white", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Constants
ROOT_COLOR = "#7A7A72"  # neutral fill for the root block, identical in both themes
MIN_CHARS = 4  # a rectangle that cannot hold this many characters gets no label

# Columns: set these to your table's column names
NAME = "Budget line"  # role: name
PARENT = "Parent"  # role: parent
VALUE = "Budget (thousand USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("budget.csv")
# Annual budget by department, project and expense category; only leaves carry a value
rows = [
    ("Company", None, None),
    ("Engineering", "Company", None),
    ("Marketing", "Company", None),
    ("Operations", "Company", None),
    ("Sales", "Company", None),
    ("Platform", "Engineering", None),
    ("Mobile App", "Engineering", None),
    ("Campaigns", "Marketing", None),
    ("Brand", "Marketing", None),
    ("Logistics", "Operations", None),
    ("Facilities", "Operations", None),
    ("Enterprise", "Sales", None),
    ("Retail", "Sales", None),
    ("Platform Staff", "Platform", 1450),
    ("Platform Cloud", "Platform", 780),
    ("Mobile Staff", "Mobile App", 920),
    ("Mobile Tools", "Mobile App", 210),
    ("Campaign Media", "Campaigns", 640),
    ("Campaign Events", "Campaigns", 330),
    ("Brand Agency", "Brand", 280),
    ("Brand Content", "Brand", 190),
    ("Shipping", "Logistics", 710),
    ("Warehousing", "Logistics", 460),
    ("Rent", "Facilities", 520),
    ("Utilities", "Facilities", 150),
    ("Enterprise Staff", "Enterprise", 880),
    ("Enterprise Travel", "Enterprise", 240),
    ("Retail Staff", "Retail", 560),
    ("Retail Commissions", "Retail", 310),
]
df = pd.DataFrame(rows, columns=[NAME, PARENT, VALUE])

# Plot: reads only df and the constants above
children = {name: [] for name in df[NAME]}
for name, parent in zip(df[NAME], df[PARENT], strict=True):
    if parent in children:
        children[parent].append(name)
own_value = dict(zip(df[NAME], df[VALUE], strict=True))
root = df.loc[df[PARENT].isna(), NAME].iloc[0]


def total(name):
    """Leaf value, or the sum over the children."""
    if not children[name]:
        return 0.0 if pd.isna(own_value[name]) else own_value[name]
    return sum(total(child) for child in children[name])


def depth(name):
    """Number of levels below this node, itself included."""
    return 1 + max((depth(child) for child in children[name]), default=0)


n_levels = depth(root)
branch_color = {name: IMPRINT_PALETTE[i] for i, name in enumerate(children[root])}

# Icicle layout: one row per level, children split the parent's width by value
rects = []
stack = [(root, 0.0, 1.0, 0, None)]
while stack:
    name, x0, x1, level, branch = stack.pop()
    rects.append((name, x0, x1 - x0, level, branch))
    x = x0
    for child in children[name]:
        width = (x1 - x0) * total(child) / total(name) if total(name) else 0.0
        stack.append((child, x, x + width, level + 1, child if level == 0 else branch))
        x += width

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.03, top=0.88)
ax_width_in = fig.get_figwidth() * (0.98 - 0.02)
row_height = 1.0 / n_levels
gap = 0.002

for name, x, width, level, branch in rects:
    if branch is None:
        color = to_rgb(ROOT_COLOR)
    else:
        # Lighter toward the leaves, mixed with white so the fill is identical in both themes
        mix = 0.28 * (level - 1)
        color = tuple(c + (1 - c) * mix for c in to_rgb(branch_color[branch]))
    y = 1.0 - (level + 1) * row_height
    ax.add_patch(
        Rectangle(
            (x + gap, y + gap), width - 2 * gap, row_height - 2 * gap, facecolor=color, edgecolor=PAGE_BG, linewidth=1.2
        )
    )

    # Label only rectangles with room for it; pick the text color with the better contrast
    fontsize = 9 if level < 2 else 7
    chars_fit = int(width * ax_width_in / (fontsize * 0.8 / 72))
    if chars_fit < MIN_CHARS:
        continue
    lum = [0.2126, 0.7152, 0.0722]
    rel = sum(
        w * (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4) for w, c in zip(lum, color, strict=True)
    )
    text_color = "#1A1A17" if (rel + 0.05) / 0.05 > 1.05 / (rel + 0.05) else "#FFFFFF"
    name = str(name)
    label = name if len(name) <= chars_fit else name[: chars_fit - 1] + "…"
    ax.text(
        x + width / 2,
        y + row_height / 2,
        f"{label}\n{total(name):,.0f}",
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold",
        color=text_color,
        linespacing=1.25,
    )

# Style
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.set_title("icicle-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=8)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
