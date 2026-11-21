""" anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (position 1 first)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
X_LABEL = "Evolutionary Distance (substitutions per site)"
SCALE_BAR = 0.1

# Column constants
NODE = "node"  # role: species_names
PARENT = "parent"  # role: newick_string
DIST = "distance"  # role: branch_lengths
POS = "position"
KIND = "kind"
CLADE = "clade"
INFO = "info"

# Data: primate species tree (mitochondrial DNA), rectangular cladogram
# Structure: ((((Human, Chimp), Gorilla), Orangutan), Gibbon)
df = pd.DataFrame(
    {
        NODE: ["Root", "Hominidae", "Homininae", "Hominini", "Human", "Chimpanzee", "Gorilla", "Orangutan", "Gibbon"],
        PARENT: ["", "Root", "Hominidae", "Homininae", "Hominini", "Hominini", "Homininae", "Hominidae", "Root"],
        DIST: [0.00, 0.20, 0.40, 0.60, 0.75, 0.75, 0.65, 0.45, 0.25],
        POS: [1.9375, 2.875, 3.75, 4.5, 5, 4, 3, 2, 1],
        KIND: ["internal"] * 4 + ["leaf"] * 5,
        CLADE: ["", "Hominidae", "Homininae", "Hominini", "", "", "", "", ""],
        INFO: [
            "Root (Common Ancestor)",
            "Hominid Ancestor",
            "Great Ape Ancestor",
            "Human-Chimp Ancestor",
            "Modern human (Homo sapiens)",
            "Chimpanzee (Pan troglodytes)",
            "Western gorilla (Gorilla gorilla)",
            "Bornean orangutan (Pongo pygmaeus)",
            "White-handed gibbon (Hylobates lar)",
        ],
    }
)

leaves = df[df[KIND] == "leaf"]
internals = df[df[KIND] == "internal"]
nodes = df.set_index(NODE)

# Plot
p = figure(
    width=3200,
    height=1800,
    title="Primate Evolution · tree-phylogenetic · python · bokeh · anyplot.ai",
    x_axis_label=X_LABEL,
    y_axis_label="",
    x_range=(df[DIST].min() - 0.15, df[DIST].max() * 1.4),
    y_range=(df[POS].min() - 0.7, df[POS].max() + 0.7),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=60,
    min_border_top=110,
    min_border_right=50,
)

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_font_size = "46pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "40pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT

p.yaxis.visible = False
p.grid.visible = False

# Horizontal branches: each non-root node is joined to its parent, length = distance difference
for _, row in df[df[PARENT] != ""].iterrows():
    parent_x = nodes.loc[row[PARENT], DIST]
    p.line([parent_x, row[DIST]], [row[POS], row[POS]], line_width=6, line_color=BRAND)

# Vertical branches: each internal node spans the positions of its children
for name in internals[NODE]:
    children = df[df[PARENT] == name]
    p.line([nodes.loc[name, DIST]] * 2, [children[POS].min(), children[POS].max()], line_width=6, line_color=BRAND)

# Nodes
leaf_source = ColumnDataSource(leaves)
internal_source = ColumnDataSource(internals)
leaf_scatter = p.scatter(
    DIST, POS, source=leaf_source, size=34, color=BRAND, line_color=INK_SOFT, line_width=4, name="leaf_nodes"
)
internal_scatter = p.scatter(DIST, POS, source=internal_source, size=26, color=INK_SOFT, name="internal_nodes")

p.add_tools(
    HoverTool(
        renderers=[leaf_scatter, internal_scatter],
        tooltips=[("Type", f"@{{{KIND}}}"), ("Info", f"@{{{INFO}}}")],
        mode="mouse",
    )
)

# Species labels at the end of each leaf branch
for _, row in leaves.iterrows():
    p.add_layout(
        Label(
            x=row[DIST] + 0.02,
            y=row[POS],
            text=row[NODE],
            text_font_size="32pt",
            text_baseline="middle",
            text_color=INK,
        )
    )

# Scale bar drawn at the same scale as the branches
scale_bar_y = df[POS].min() - 0.4
p.line([0, SCALE_BAR], [scale_bar_y, scale_bar_y], line_width=6, line_color=INK_SOFT)
p.add_layout(
    Label(
        x=0.0, y=scale_bar_y - 0.25, text=f"{SCALE_BAR} substitutions/site", text_font_size="26pt", text_color=INK_SOFT
    )
)

# Clade annotations left of each named internal node
for _, row in internals[internals[CLADE] != ""].iterrows():
    p.add_layout(
        Label(
            x=row[DIST] - 0.17,
            y=row[POS] + 0.22,
            text=row[CLADE],
            text_font_size="30pt",
            text_font_style="italic",
            text_color=INK_SOFT,
            text_baseline="middle",
        )
    )

# Legend
legend = Legend(
    items=[
        LegendItem(label="Extant Species (Leaf Nodes)", renderers=[leaf_scatter]),
        LegendItem(label="Ancestral Nodes (Internal)", renderers=[internal_scatter]),
    ],
    location="top_right",
    label_text_font_size="28pt",
    label_text_color=INK_SOFT,
    spacing=10,
    padding=15,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    border_line_color=INK_SOFT,
)
p.add_layout(legend)

# Save HTML (required catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium/headless Chrome
W, H = 3200, 1800
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
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
