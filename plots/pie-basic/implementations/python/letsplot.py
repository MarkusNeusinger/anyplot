""" anyplot.ai
pie-basic: Basic Pie Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-28
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_pie,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_labels,
    layer_tooltips,
    scale_color_identity,
    scale_fill_manual,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ANYPLOT_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# anyplot categorical palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
REST = "Others"  # the rest category takes the muted tone, not a palette position

# Columns: set these to your table's column names
COMPANY = "company"  # role: category
SHARE = "share"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("shares.csv")
# Global smartphone market share (2024)
df = pd.DataFrame({COMPANY: ["Apple", "Samsung", "Xiaomi", "OPPO", REST], SHARE: [23.1, 19.4, 13.7, 8.8, 35.0]})

# Plot — square canvas (600×600 × scale=4 = 2400×2400 px)
title = "pie-basic · python · letsplot · anyplot.ai"
title_size = 16

# Colors: Imprint positions in data order, muted for the rest category
is_rest = df[COMPANY].eq(REST).fillna(False).tolist()
colors = [ANYPLOT_MUTED if rest else IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, rest in enumerate(is_rest)]

# Explode the smallest slice; the subtitle names it from the data
smallest = df[SHARE].idxmin()
# Label ink follows the fill: dark on the light fills (lavender, and the muted rest slice on the dark page), white elsewhere
dark_label = {"#C475FD", ANYPLOT_MUTED} if THEME == "dark" else {"#C475FD"}
df = df.assign(
    explode=[0.08 if i == smallest else 0.0 for i in df.index],
    label=[f"{v:.1f}%" for v in df[SHARE]],
    label_color=["#1A1A17" if c in dark_label else "#FFFFFF" for c in colors],
)
subtitle = f"{df[COMPANY][smallest]}'s {df[SHARE][smallest]}% slice is the smallest — '{df[COMPANY][df[SHARE].idxmax()]}' dominate at {df[SHARE].max():g}%"

# Rich HTML tooltips — letsplot-specific interactivity
pie_tooltips = layer_tooltips().title(f"@{COMPANY}").line("Market share|@label")

plot = (
    ggplot(df)
    + geom_pie(
        aes(slice=SHARE, fill=COMPANY, explode="explode", color="label_color"),
        stat="identity",
        size=40,
        hole=0,
        stroke=0,
        spacer_width=1.0,
        spacer_color=PAGE_BG,
        labels=layer_labels().line("@label").size(11).inherit_color(),
        tooltips=pie_tooltips,
    )
    + scale_fill_manual(values=colors)
    + scale_color_identity()
    + labs(title=title, subtitle=subtitle, fill="Brand", caption="Global smartphone market share, 2024")
    + ggsize(600, 600)
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=title_size, hjust=0.5, face="bold", color=INK),
        plot_subtitle=element_text(size=11, hjust=0.5, color=INK_SOFT),
        plot_caption=element_text(size=9, hjust=0.5, color=ANYPLOT_MUTED),
        legend_title=element_text(size=12, face="bold", color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        plot_margin=[20, 20, 20, 20],
        legend_position="right",
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
