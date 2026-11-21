"""anyplot.ai
upset-basic: UpSet Plot for Multi-Set Intersection Analysis
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_point,
    geom_rect,
    geom_segment,
    ggbunch,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INACTIVE = "#C0BDB5" if THEME == "light" else "#404038"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
MAX_INTERSECTIONS = 12  # columns shown, largest first

ELEMENT = "User"  # role: element
SETS = "Channels"  # role: sets

# Data: user acquisition channels; replace with your own table, one row per element,
# for example df = pd.DataFrame({ELEMENT: ids, SETS: [("Email", "Social"), ...]})
np.random.seed(42)
channels = ["Email", "Social", "Search", "Referral", "Direct"]
n_users = 1000
probs = [0.42, 0.55, 0.38, 0.25, 0.32]
member = np.column_stack([np.random.random(n_users) < p for p in probs])
df = pd.DataFrame(
    {
        ELEMENT: [f"user-{i + 1}" for i in range(n_users)],
        SETS: [tuple(c for c, m in zip(channels, row, strict=False) if m) for row in member],
    }
)
df = df[df[SETS].str.len() > 0].reset_index(drop=True)

# Plot
df = df.dropna(subset=[SETS])
set_names = sorted({s for combo in df[SETS] for s in combo})

# Intersections sorted by size
inter = df.groupby(df[SETS].apply(frozenset)).size().rename("count").reset_index()
inter = inter.sort_values("count", ascending=False).head(MAX_INTERSECTIONS).reset_index(drop=True)
inter["idx"] = range(len(inter))
inter["degree"] = inter[SETS].apply(len)
inter["degree_str"] = inter["degree"].astype(str)

# Set ordering: smallest size at bottom (y=0), largest at top
set_sizes = pd.Series({s: int(df[SETS].apply(lambda combo, s=s: s in combo).sum()) for s in set_names})
set_sizes = set_sizes.sort_values(ascending=True)
ordered_sets = list(set_sizes.index)
set_y = {s: i for i, s in enumerate(ordered_sets)}

# Dot matrix and connecting lines
dot_df = pd.DataFrame(
    [{"x": row["idx"], "y": set_y[s], "active": s in row[SETS]} for _, row in inter.iterrows() for s in ordered_sets]
)
line_df = pd.DataFrame(
    [
        {"x": row["idx"], "ymin": min(ys), "ymax": max(ys)}
        for _, row in inter.iterrows()
        if len(ys := [set_y[s] for s in ordered_sets if s in row[SETS]]) > 1
    ]
)

# Set size bars (geom_rect for precise horizontal bars)
bar_h = 0.38
set_df = pd.DataFrame({"y": [set_y[s] for s in ordered_sets], "xmax": set_sizes.values})
set_df["xmin"] = 0
set_df["ymin"] = set_df["y"] - bar_h
set_df["ymax"] = set_df["y"] + bar_h

# Shared axis limits
y_lim = [-0.6, len(ordered_sets) - 0.4]
y_breaks = list(range(len(ordered_sets)))
x_lim = [-0.7, len(inter) - 0.3]
x_breaks = list(range(len(inter)))

# Shared base theme
base_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.15),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=10),
)

# Intersection size bars (top panel), colored by degree; only degrees present
degree_palette = {str(d): IMPRINT_PALETTE[(d - 1) % len(IMPRINT_PALETTE)] for d in sorted(inter["degree"].unique())}

p_top = (
    ggplot(inter, aes(x="idx", y="count", fill="degree_str"))
    + geom_bar(stat="identity", width=0.65)
    + scale_fill_manual(values=degree_palette, name="Degree")
    + scale_x_continuous(limits=x_lim, breaks=x_breaks)
    + scale_y_continuous(expand=[0.02, 0])
    + labs(x="", y="Intersection Size", title="upset-basic · python · letsplot · anyplot.ai")
    + base_theme
    + theme(axis_text_x=element_blank(), axis_ticks_x=element_blank(), panel_grid_major_x=element_blank())
)

# Dot matrix (bottom-right panel)
p_matrix = (
    ggplot()
    + geom_point(
        data=dot_df[~dot_df["active"]].reset_index(drop=True),
        mapping=aes(x="x", y="y"),
        color=INACTIVE,
        size=2.5,
        alpha=0.6,
    )
    + geom_segment(data=line_df, mapping=aes(x="x", xend="x", y="ymin", yend="ymax"), color=BRAND, size=1.8)
    + geom_point(data=dot_df[dot_df["active"]].reset_index(drop=True), mapping=aes(x="x", y="y"), color=BRAND, size=4)
    + scale_x_continuous(limits=x_lim, breaks=x_breaks)
    + scale_y_continuous(limits=y_lim, breaks=y_breaks, labels=ordered_sets)
    + labs(x="Intersection", y="")
    + base_theme
    + theme(axis_ticks=element_blank(), panel_grid_major=element_blank())
)

# Set size bars (bottom-left panel)
p_sets = (
    ggplot(set_df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"))
    + geom_rect(fill=BRAND, color=None)
    + scale_x_continuous(limits=[0, set_df["xmax"].max() * 1.12], expand=[0, 0])
    + scale_y_continuous(limits=y_lim, breaks=y_breaks, labels=ordered_sets)
    + labs(x="Set Size", y="")
    + base_theme
    + theme(axis_ticks_y=element_blank(), panel_grid_major_y=element_blank())
)

# Combine with ggbunch (800x450 base; scale=4 -> 3200x1800 px)
top_h = 0.58
left_w = 0.24
fig = ggbunch(
    [p_top, p_sets, p_matrix],
    [(0, 0, 1.0, top_h), (0, top_h, left_w, 1 - top_h), (left_w, top_h, 1 - left_w, 1 - top_h)],
) + ggsize(800, 450)

# Save
ggsave(fig, f"plot-{THEME}.png", path=".", scale=4)
ggsave(fig, f"plot-{THEME}.html", path=".")
