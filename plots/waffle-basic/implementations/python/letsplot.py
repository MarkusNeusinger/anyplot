"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-26
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    gggrid,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first series ALWAYS #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Theme-adaptive custom theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    plot_title=element_text(size=16, color=INK, hjust=0.5),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(size=14, color=INK),
    legend_text=element_text(size=12, color=INK_SOFT),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_line=element_blank(),
)

# Columns
PREFERENCE = "Preference"  # role: category
PERCENT = "Percent"  # role: value

# Data - Survey results on voting preferences (shares sum to 100%)
df = pd.DataFrame({PREFERENCE: ["Very Likely", "Likely", "Neutral", "Unlikely"], PERCENT: [45, 28, 18, 9]})

# Plot
GRID_SIDE = 10  # 10x10 grid, each square = 1% of the whole
# Whole squares per category: cumulative shares rounded to square edges, so the blocks always fill the grid
edges = (df[PERCENT].fillna(0).cumsum() / df[PERCENT].sum() * GRID_SIDE**2).round().astype(int)
counts = edges.diff().fillna(edges).astype(int)
legend_labels = [f"{name} ({pct:g}%)" for name, pct in zip(df[PREFERENCE], df[PERCENT], strict=True)]
position = pd.Series(range(GRID_SIDE**2))
squares = pd.DataFrame(
    {
        "col": position % GRID_SIDE,
        "row": GRID_SIDE - 1 - position // GRID_SIDE,
        PREFERENCE: pd.Categorical(
            pd.Series(legend_labels).repeat(counts).reset_index(drop=True), categories=legend_labels, ordered=True
        ),
    }
)
plot = (
    ggplot(squares, aes(x="col", y="row", fill=PREFERENCE))
    + geom_tile(width=0.88, height=0.88, size=0)
    + coord_fixed(ratio=1)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + labs(title="waffle-basic · python · letsplot · anyplot.ai", fill=PREFERENCE)
    + theme_void()
    + anyplot_theme
)

# One-panel grid paints the whole canvas with the page color
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save outputs
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
