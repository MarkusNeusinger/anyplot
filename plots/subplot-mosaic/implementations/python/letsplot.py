"""anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEQ_LOW, SEQ_HIGH = IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]  # Imprint sequential ramp

# Columns: set these to your table's column names (one long table, one block of rows per panel)
PANEL = "Panel"  # role: extra
CATEGORY = "Category"  # role: extra
GROUP = "Quarter"  # role: extra
X = "X"  # role: x
Y = "Y"  # role: y
Z = "Z"  # role: z

# Data: replace this block with your own table, one row per mark, tagged with the panel it feeds
rng = np.random.default_rng(42)
n_days = 100
revenue = 1000 + np.cumsum(rng.normal(5, 10, n_days))
products = ["Product A", "Product B", "Product C", "Product D", "Product E"]
sales = [450, 380, 290, 520, 340]
effort = rng.uniform(20, 80, 60)
output = effort * 0.7 + rng.normal(0, 8, 60) + 10
scores = np.concatenate([rng.normal(50, 10, 150), rng.normal(80, 8, 100)])
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
growth = [2.1, 3.5, 2.8, 4.2, 3.9, 5.1]
regions = ["Region A", "Region B", "Region C"]
quarters = ["Q1", "Q2", "Q3", "Q4"]
heat = rng.integers(60, 100, size=(len(quarters), len(regions)))

df = pd.concat(
    [
        pd.DataFrame({PANEL: "A", X: np.arange(n_days), Y: revenue}),
        pd.DataFrame({PANEL: "B", CATEGORY: products, Y: sales}),
        pd.DataFrame({PANEL: "C", X: effort, Y: output}),
        pd.DataFrame({PANEL: "D", X: scores}),
        pd.DataFrame({PANEL: "E", CATEGORY: months, X: np.arange(len(months)), Y: growth}),
        pd.DataFrame(
            {
                PANEL: "F",
                CATEGORY: np.tile(regions, len(quarters)),
                GROUP: np.repeat(quarters, len(regions)),
                Z: heat.ravel(),
            }
        ),
    ],
    ignore_index=True,
)

# Plot: every panel reads its own slice of df
panels = [part for _, part in df.groupby(PANEL, sort=False)]
panel_a, panel_b, panel_c, panel_d, panel_e, panel_f = panels

anyplot_theme = theme_minimal() + theme(
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    plot_title=element_text(size=11, face="bold", color=INK),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.15),
    panel_grid_minor=element_blank(),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
)

# A: wide overview, the primary view
plot_a = (
    ggplot(panel_a, aes(x=X, y=Y))
    + geom_area(fill=IMPRINT_PALETTE[0], alpha=0.3)
    + geom_line(color=IMPRINT_PALETTE[0], size=1.2)
    + scale_y_continuous(limits=[panel_a[Y].min() * 0.95, panel_a[Y].max() * 1.03])
    + labs(x="Day", y="Revenue ($)", title="Daily Revenue Overview")
    + anyplot_theme
)

# B: bar chart, two thirds of the middle row
plot_b = (
    ggplot(panel_b, aes(x=CATEGORY, y=Y))
    + geom_bar(stat="identity", fill=IMPRINT_PALETTE[0], color=INK_SOFT, size=0.3, alpha=0.9)
    + labs(x="Product", y="Units Sold", title="Sales by Product")
    + anyplot_theme
)

# C: scatter with fitted trend, one third of the middle row
plot_c = (
    ggplot(panel_c, aes(x=X, y=Y))
    + geom_point(color=IMPRINT_PALETTE[0], size=2.5, alpha=0.7)
    + geom_smooth(method="lm", color=IMPRINT_PALETTE[1], size=1.0, se=False)
    + labs(x="Effort (hours)", y="Output (units)", title="Effort vs Output")
    + anyplot_theme
)

# D: histogram
plot_d = (
    ggplot(panel_d, aes(x=X))
    + geom_histogram(bins=25, fill=IMPRINT_PALETTE[0], color=INK_SOFT, alpha=0.85, size=0.2)
    + labs(x="Performance Score", y="Frequency", title="Score Distribution")
    + anyplot_theme
)

# E: line with markers over month positions
plot_e = (
    ggplot(panel_e, aes(x=X, y=Y))
    + geom_line(color=IMPRINT_PALETTE[0], size=1.2)
    + geom_point(color=IMPRINT_PALETTE[0], size=3.5)
    + scale_x_continuous(breaks=panel_e[X].tolist(), labels=panel_e[CATEGORY].tolist())
    + labs(x="Month", y="Growth Rate (%)", title="Monthly Growth")
    + anyplot_theme
)

# F: heatmap with the Imprint sequential ramp
plot_f = (
    ggplot(panel_f, aes(x=CATEGORY, y=GROUP, fill=Z))
    + geom_tile(color=PAGE_BG, size=1.0)
    + geom_text(aes(label=Z), size=6, color="#FAF8F1")
    + scale_fill_gradient(low=SEQ_LOW, high=SEQ_HIGH, name="Score")
    + labs(x="Region", y=GROUP, title="Regional Performance")
    + anyplot_theme
    + theme(legend_position="right")
)

# Mosaic layout (x, y, width, height as fractions of the canvas), gutters of 0.02:
#   AAA
#   BBC
#   DEF
regions_layout = [
    (0.0, 0.08, 1.0, 0.25),
    (0.0, 0.35, 0.66, 0.31),
    (0.68, 0.35, 0.32, 0.31),
    (0.0, 0.68, 0.32, 0.32),
    (0.34, 0.68, 0.32, 0.32),
    (0.68, 0.68, 0.32, 0.32),
]

final_plot = (
    ggbunch(plots=[plot_a, plot_b, plot_c, plot_d, plot_e, plot_f], regions=regions_layout)
    + ggsize(800, 450)
    + ggtitle("subplot-mosaic · python · letsplot · anyplot.ai")
    + theme(
        plot_title=element_text(size=16, color=INK, face="bold", hjust=0.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

output_dir = os.path.dirname(os.path.abspath(__file__))
ggsave(final_plot, os.path.join(output_dir, f"plot-{THEME}.png"), scale=4)
ggsave(final_plot, os.path.join(output_dir, f"plot-{THEME}.html"))
