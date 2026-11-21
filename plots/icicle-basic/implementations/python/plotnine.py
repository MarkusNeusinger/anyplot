"""anyplot.ai
icicle-basic: Basic Icicle Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one color per hierarchy level, root first
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LABEL_VALUE_MIN = 0.07  # rectangles wider than this share of the root get name and value
LABEL_NAME_MIN = 0.05  # rectangles wider than this share get the name only

# Columns: set these to your table's column names
NAME = "Name"  # role: name
PARENT = "Parent"  # role: parent
VALUE = "Size (MB)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("folders.csv")
# Only leaves carry a value; parents are summed from their children below.
df = pd.DataFrame(
    {
        NAME: [
            "root",
            "Documents",
            "Photos",
            "Projects",
            "Archive",
            "Reports",
            "Invoices",
            "Notes",
            "Vacation",
            "Family",
            "Events",
            "WebApp",
            "DataSci",
            "Mobile",
            "Frontend",
            "Backend",
            "Config",
            "Models",
            "Scripts",
            "Old2023",
            "Old2022",
        ],
        PARENT: [
            "",
            "root",
            "root",
            "root",
            "root",
            "Documents",
            "Documents",
            "Documents",
            "Photos",
            "Photos",
            "Photos",
            "Projects",
            "Projects",
            "Projects",
            "WebApp",
            "WebApp",
            "WebApp",
            "DataSci",
            "DataSci",
            "Archive",
            "Archive",
        ],
        VALUE: [
            None,
            None,
            None,
            None,
            None,
            450,
            280,
            180,
            680,
            520,
            340,
            None,
            None,
            380,
            320,
            420,
            200,
            520,
            300,
            1200,
            950,
        ],
    }
)

# Plot: reads only df and the constants above
children = {name: [] for name in df[NAME]}
for name, parent in zip(df[NAME], df[PARENT], strict=True):
    if parent in children:
        children[parent].append(name)
root = df.loc[~df[PARENT].isin(children), NAME].iloc[0]
own_value = dict(zip(df[NAME], df[VALUE], strict=True))


def total(name):
    """Leaf value, or the sum of the children's totals."""
    if not children[name]:
        return own_value[name]
    return sum(total(kid) for kid in children[name])


# Depth-first layout: width follows value, children sit inside their parent's extent
rects = []


def place(name, depth, x_start, x_end):
    rects.append({"name": name, "xmin": x_start, "xmax": x_end, "depth": depth, "value": total(name)})
    kids = sorted(children[name], key=lambda k: -total(k))
    kid_sum = sum(total(k) for k in kids)
    x = x_start
    for kid in kids:
        width = total(kid) / kid_sum * (x_end - x_start)
        place(kid, depth + 1, x, x + width)
        x += width


place(root, 0, 0.0, 1.0)
rect_df = pd.DataFrame(rects)

# Root in the top row, one row per level below it
max_depth = rect_df["depth"].max()
rect_df["ymax"] = max_depth - rect_df["depth"] + 1
rect_df["ymin"] = max_depth - rect_df["depth"]
rect_df["width"] = rect_df["xmax"] - rect_df["xmin"]
rect_df["x_center"] = (rect_df["xmin"] + rect_df["xmax"]) / 2
rect_df["y_center"] = (rect_df["ymin"] + rect_df["ymax"]) / 2

# Labels: name and value on wide rectangles, name only on medium ones, none on slivers
rect_df["label"] = [
    f"{n}\n({v:.0f} MB)" if w > LABEL_VALUE_MIN else (n if w > LABEL_NAME_MIN else "")
    for n, v, w in zip(rect_df["name"], rect_df["value"], rect_df["width"], strict=True)
]

# Color by hierarchy level
levels = [f"Level {d}" for d in range(max_depth + 1)]
rect_df["level"] = pd.Categorical([f"Level {d}" for d in rect_df["depth"]], categories=levels, ordered=True)

# Text color per level, chosen for contrast against the level's fill
dark_bg = rect_df[rect_df["depth"].isin([0, 1, 3])]
light_bg = rect_df[~rect_df["depth"].isin([0, 1, 3])]

plot = (
    ggplot(rect_df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="level"), color="white", size=0.75)
    + geom_text(aes(x="x_center", y="y_center", label="label"), data=dark_bg, size=5, color=INK)
    + geom_text(aes(x="x_center", y="y_center", label="label"), data=light_bg, size=5, color=INK)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=levels, name="Hierarchy level")
    + labs(title="icicle-basic · python · plotnine · anyplot.ai")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        figure_size=(8, 4.5),
        plot_margin=0.03,
        plot_title=element_text(size=14, ha="center", weight="bold", color=INK),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
