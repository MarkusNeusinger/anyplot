"""anyplot.ai
icicle-basic: Basic Icicle Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 82/100 | Created: 2026-05-13
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: all eight positions, one per hierarchy level in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NAME = "name"  # role: name
PARENT = "parent"  # role: parent
VALUE = "value"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("files.csv")
# File system hierarchy: the root has an empty parent
df = pd.DataFrame(
    {
        NAME: [
            "root",
            "Documents",
            "Photos",
            "Code",
            "Projects",
            "Archive",
            "Work_Docs",
            "Personal",
            "Vacation",
            "Family",
            "Project_A",
            "Project_B",
            "Project_C",
            "Backup_2024",
        ],
        PARENT: [
            "",
            "root",
            "root",
            "root",
            "root",
            "root",
            "Documents",
            "Documents",
            "Photos",
            "Photos",
            "Code",
            "Code",
            "Code",
            "Archive",
        ],
        VALUE: [100, 25, 20, 30, 15, 10, 12, 13, 8, 12, 10, 12, 8, 10],
    }
)

# Plot: reads only df and the constants above
parent_of = df.set_index(NAME)[PARENT].fillna("").to_dict()


def depth(node):
    """Number of steps from the node up to the root."""
    level = 0
    while parent_of.get(node, ""):
        node = parent_of[node]
        level += 1
    return level


colors = [IMPRINT_PALETTE[depth(node) % len(IMPRINT_PALETTE)] for node in df[NAME]]


def label_color(fill):
    """Dark or light label ink, whichever contrasts more with the fill (same in both themes)."""
    r, g, b = (int(fill[i : i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return "#1A1A17" if (lum + 0.05) / 0.0662 > 0.99 / (lum + 0.05) else "#FAF8F1"


fig = go.Figure(
    go.Icicle(
        labels=df[NAME],
        parents=df[PARENT],
        values=df[VALUE],
        marker={"colors": colors, "line": {"color": PAGE_BG, "width": 1.5}},
        textposition="middle center",
        textfont={"size": 10, "color": [label_color(c) for c in colors]},
        leaf={"opacity": 1},
        hovertemplate=f"<b>%{{label}}</b><br>{VALUE}: %{{value}}<extra></extra>",
    )
)

fig.update_layout(
    title={
        "text": "icicle-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "family": "Arial, sans-serif"},
    margin={"l": 40, "r": 40, "t": 80, "b": 40},
    showlegend=False,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
