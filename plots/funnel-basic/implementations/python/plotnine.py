"""anyplot.ai
funnel-basic: Basic Funnel Chart
Library: plotnine 0.15.3 | Python 3.14.4
Quality: pending | Updated: 2026-04-26
"""

# Script filename "plotnine.py" shadows the plotnine package on sys.path.
# Drop the script's own directory before importing.
import os
import sys


sys.path = [p for p in sys.path if not p.endswith("implementations/python")]

import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_identity,
    scale_y_reverse,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette: all eight positions, one per stage in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LIGHT_FILLS = {"#C475FD", "#2ABCCD", "#99B314"}  # light Imprint hues that need dark text
GAP = 0.06  # vertical gap between segments

# Columns: set these to your table's column names
STAGE = "Stage"  # role: stage
VALUE = "Customers"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("funnel.csv")
df = pd.DataFrame(
    {STAGE: ["Awareness", "Interest", "Consideration", "Intent", "Purchase"], VALUE: [1000, 600, 400, 200, 100]}
)

# Plot: reads only df and the constants above
X, Y, ORDER, FILL, LABEL, TEXT = "x", "y", "order", "fill", "label", "text_color"
funnel = df.dropna(subset=[STAGE, VALUE]).reset_index(drop=True)
stages = funnel[STAGE].tolist()
widths = funnel[VALUE] / funnel[VALUE].iloc[0]
polygons = []
labels = []
for i, stage in enumerate(stages):
    w_top = widths.iloc[i]
    # Flat bottom on the last segment: match its own width.
    w_bot = widths.iloc[i + 1] if i + 1 < len(funnel) else w_top
    y_top = i + GAP / 2
    y_bot = (i + 1) - GAP / 2
    fill = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    for order, (x, y) in enumerate([(-w_top / 2, y_top), (w_top / 2, y_top), (w_bot / 2, y_bot), (-w_bot / 2, y_bot)]):
        polygons.append({STAGE: stage, X: x, Y: y, ORDER: order, FILL: fill})
    labels.append(
        {
            STAGE: stage,
            X: 0,
            Y: (y_top + y_bot) / 2,
            LABEL: f"{stage}\n{funnel[VALUE].iloc[i]:,.0f}  ·  {widths.iloc[i] * 100:.0f}%",
            TEXT: "#1A1A17" if fill in LIGHT_FILLS else "white",
        }
    )

df_poly = pd.DataFrame(polygons)
df_poly[STAGE] = pd.Categorical(df_poly[STAGE], categories=stages, ordered=True)
df_labels = pd.DataFrame(labels)

plot = (
    ggplot(df_poly, aes(x=X, y=Y, fill=FILL, group=STAGE))
    + geom_polygon(color=PAGE_BG, size=1)
    + geom_text(aes(x=X, y=Y, label=LABEL, color=TEXT), data=df_labels, size=7, fontweight="bold", inherit_aes=False)
    + scale_fill_identity()
    + scale_color_identity()
    + scale_y_reverse()
    + labs(title="funnel-basic · python · plotnine · anyplot.ai", x="", y="")
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=12, color=INK, weight="medium", ha="center"),
        plot_margin=0.02,
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
