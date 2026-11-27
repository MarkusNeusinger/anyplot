"""anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: letsplot 4.11.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for colored cells (heatmap fields), light and dark stops
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants: the mosaic, drawn as text. Repeated letters span cells, "." leaves a gap
LAYOUT = "AAA;BBC;DEF"
ROW_WEIGHTS = [0.9, 1.1, 1.0]  # relative row heights, one per row of LAYOUT
GAP = 0.02  # spacing between panels, as a share of the canvas
TITLE_SHARE = 0.05  # top share of the canvas reserved for the main title
LABEL_WIDTH = 5  # y tick labels of the left-hand panels are padded to this width so their plot boxes start flush

# Columns: set these to your table's column names
PANEL = "Panel"  # role: extra
X = "Day"  # role: x
Y = "Value"  # role: y
CATEGORY = "Category"  # role: extra
GROUP = "Group"  # role: extra
Z = "Score"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("panels.csv")
rng = np.random.default_rng(42)
n_days = 100
revenue = np.cumsum(rng.normal(5, 10, n_days)) + 1000
products = ["Laptops", "Monitors", "Keyboards", "Webcams", "Headsets"]
sales = [450, 380, 290, 520, 340]
effort = rng.uniform(20, 80, 60)
output = effort * 0.7 + rng.normal(0, 8, 60) + 10
scores = np.concatenate([rng.normal(50, 10, 150), rng.normal(80, 8, 100)])
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
growth = [2.1, 3.5, 2.8, 4.2, 3.9, 5.1]
quarters = ["Q1", "Q2", "Q3", "Q4"]
regions = ["North", "South", "West"]
heat = rng.integers(60, 100, (len(quarters), len(regions)))

df = pd.concat(
    [
        pd.DataFrame({PANEL: "A", X: np.arange(n_days), Y: revenue}),
        pd.DataFrame({PANEL: "B", CATEGORY: products, Y: sales}),
        pd.DataFrame({PANEL: "C", X: effort, Y: output}),
        pd.DataFrame({PANEL: "D", X: scores}),
        pd.DataFrame({PANEL: "E", X: np.arange(len(months)), CATEGORY: months, Y: growth}),
        pd.DataFrame(
            {PANEL: "F", CATEGORY: np.repeat(quarters, len(regions)), GROUP: regions * len(quarters), Z: heat.ravel()}
        ),
    ],
    ignore_index=True,
)


# Plot: reads only df and the constants above
def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


base_theme = theme_minimal() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=11, color=INK),
    axis_text=element_text(size=9, color=INK_SOFT),
    plot_title=element_text(size=12, face="bold", color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=9, color=INK_SOFT),
    legend_title=element_text(size=10, color=INK),
)

# One frame per panel, in the order the panels appear in df: A to F in the sample
frames = [frame for _, frame in df.groupby(PANEL, sort=False)]

# Each panel is drawn when df holds its frame, so a table with fewer panels still renders
plots = []

# A: primary panel, the revenue trend over time
if len(frames) > 0:
    data_a = frames[0]
    ticks_a = np.linspace(0, data_a[Y].max(), 5)
    plots.append(
        ggplot(data_a, aes(x=X, y=Y))
        + geom_area(fill=IMPRINT_PALETTE[0], alpha=0.3)
        + geom_line(color=IMPRINT_PALETTE[0], size=1.2)
        + scale_y_continuous(
            limits=[0, float(data_a[Y].max()) * 1.05],
            breaks=ticks_a,
            labels=[f"{t:,.0f}".rjust(LABEL_WIDTH, " ") for t in ticks_a],
        )
        + labs(x=X, y="Revenue ($)", title="Daily Revenue Overview")
        + base_theme
    )

# B: sales per product
if len(frames) > 1:
    ticks_b = np.linspace(0, frames[1][Y].max(), 5)
    plots.append(
        ggplot(frames[1], aes(x=CATEGORY, y=Y))
        + geom_bar(stat="identity", fill=IMPRINT_PALETTE[0], color=INK_SOFT, size=0.3, alpha=0.9)
        + scale_y_continuous(breaks=ticks_b, labels=[f"{t:,.0f}".rjust(LABEL_WIDTH, " ") for t in ticks_b])
        + labs(x="Product", y="Units Sold", title="Sales by Product")
        + base_theme
    )

# C: scatter with a linear trend
if len(frames) > 2:
    plots.append(
        ggplot(frames[2], aes(x=X, y=Y))
        + geom_point(color=IMPRINT_PALETTE[0], size=2.5, alpha=0.7)
        + geom_smooth(method="lm", color=IMPRINT_PALETTE[1], size=1.0, se=False)
        + labs(x="Effort (hours)", y="Output (units)", title="Effort vs Output")
        + base_theme
    )

# D: histogram
if len(frames) > 3:
    ticks_d = np.linspace(0, np.histogram(frames[3][X].dropna(), bins=25)[0].max(), 5).round()
    plots.append(
        ggplot(frames[3], aes(x=X))
        + geom_histogram(bins=25, fill=IMPRINT_PALETTE[0], color=INK_SOFT, alpha=0.85, size=0.2)
        + scale_y_continuous(breaks=ticks_d, labels=[f"{t:,.0f}".rjust(LABEL_WIDTH, " ") for t in ticks_d])
        + labs(x="Performance Score", y="Frequency", title="Score Distribution")
        + base_theme
    )

# E: line with markers over months
if len(frames) > 4:
    data_e = frames[4]
    plots.append(
        ggplot(data_e, aes(x=X, y=Y))
        + geom_line(color=IMPRINT_PALETTE[0], size=1.2)
        + geom_point(color=IMPRINT_PALETTE[0], size=3.5)
        + scale_x_continuous(breaks=data_e[X].tolist(), labels=data_e[CATEGORY].tolist())
        + labs(x="Month", y="Growth Rate (%)", title="Monthly Growth")
        + base_theme
    )

# F: heatmap, cell values in a color that contrasts with each tile
if len(frames) > 5:
    data_f = frames[5]
    z_min, z_max = data_f[Z].min(), data_f[Z].max()
    tile_hex = [ramp_color(SEQ_FIELDS, (v - z_min) / max(z_max - z_min, 1e-9)) for v in data_f[Z]]
    # relative luminance of each tile decides the ink: light text on dark tiles, dark text on light ones
    weights = (0.2126, 0.7152, 0.0722)
    on_dark_tile = np.array(
        [
            sum(w * (int(h[i : i + 2], 16) / 255) ** 2.2 for w, i in zip(weights, (1, 3, 5), strict=True)) < 0.18
            for h in tile_hex
        ]
    )
    plots.append(
        ggplot(data_f, aes(x=GROUP, y=CATEGORY, fill=Z))
        + geom_tile(color=PAGE_BG, size=0.8)
        + geom_text(aes(label=Z), data=data_f[on_dark_tile], size=6, color="#FAF8F1")
        + geom_text(aes(label=Z), data=data_f[~on_dark_tile], size=6, color="#1A1A17")
        + scale_fill_gradientn(colors=[ramp_color(SEQ_FIELDS, k / 255) for k in range(256)])
        + scale_y_discrete(limits=data_f[CATEGORY].unique().tolist()[::-1])
        + labs(x="Region", y="Quarter", title="Regional Score (value in cell)")
        + base_theme
        + theme(legend_position="none")
    )

# Layout: one (x, y, width, height) region per letter, in ggbunch's canvas fractions
rows = LAYOUT.split(";")
edges = np.concatenate([[0], np.cumsum(ROW_WEIGHTS)]) / np.sum(ROW_WEIGHTS)
boxes = []
for letter in sorted({ch for ch in LAYOUT if ch.isalpha()}):
    cells = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == letter]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    top = TITLE_SHARE + edges[r0] * (1 - TITLE_SHARE)
    bottom = TITLE_SHARE + edges[r1 + 1] * (1 - TITLE_SHARE)
    boxes.append((c0 / len(rows[0]) + GAP / 2, top + GAP / 2, (c1 + 1 - c0) / len(rows[0]) - GAP, bottom - top - GAP))
boxes = boxes[: len(plots)]
final_plot = (
    ggbunch(plots=plots, regions=boxes)
    + ggsize(800, 450)
    + ggtitle("subplot-mosaic · python · letsplot · anyplot.ai")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, color=INK, face="bold", hjust=0.5),
    )
)

output_dir = os.path.dirname(os.path.abspath(__file__))
ggsave(final_plot, os.path.join(output_dir, f"plot-{THEME}.png"), scale=4)
ggsave(final_plot, os.path.join(output_dir, f"plot-{THEME}.html"))
