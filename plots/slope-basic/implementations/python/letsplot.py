""" anyplot.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-04-30
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#C8C7BF" if THEME == "light" else "#333330"

# Okabe-Ito: green = increase, orange = decrease
COLOR_INCREASE = "#009E73"
COLOR_DECREASE = "#D55E00"

# Consumer electronics quarterly sales ($K): Q1 vs Q4
data = {
    "entity": [
        "Laptops",
        "Smartphones",
        "Smart TVs",
        "Monitors",
        "Headphones",
        "Cameras",
        "Streaming Devices",
        "Speakers",
        "Tablets",
        "Gaming Consoles",
    ],
    "Q1": [80, 210, 120, 155, 140, 195, 55, 175, 105, 90],
    "Q4": [130, 175, 160, 120, 185, 215, 95, 140, 150, 60],
}
df = pd.DataFrame(data)
df["change"] = df["Q4"] - df["Q1"]
df["direction"] = df["change"].apply(lambda x: "Increase" if x > 0 else "Decrease")
df["abs_change"] = df["change"].abs()

# Top 3 movers by absolute change — receive visual emphasis
top_movers = set(df.nlargest(3, "abs_change")["entity"])

# Segment data
df_segments = pd.DataFrame(
    {
        "entity": df["entity"].values,
        "x_start": [0] * 10,
        "x_end": [1] * 10,
        "y_start": df["Q1"].values,
        "y_end": df["Q4"].values,
        "direction": df["direction"].values,
        "change": df["change"].values,
    }
)
seg_normal = df_segments[~df_segments["entity"].isin(top_movers)].reset_index(drop=True)
seg_top = df_segments[df_segments["entity"].isin(top_movers)].reset_index(drop=True)

# Points (both endpoints)
df_long = pd.DataFrame(
    {"entity": df["entity"].tolist() * 2, "value": df["Q1"].tolist() + df["Q4"].tolist(), "x": [0] * 10 + [1] * 10}
).merge(df[["entity", "direction"]], on="entity")

# Endpoint labels: entity name + value for legibility in crowded regions
df_left = pd.DataFrame(
    {
        "entity": df["entity"].values,
        "value": df["Q1"].values,
        "x": [0] * 10,
        "label": [f"{e} (${v}K)" for e, v in zip(df["entity"], df["Q1"], strict=False)],
    }
)
df_right = pd.DataFrame(
    {
        "entity": df["entity"].values,
        "value": df["Q4"].values,
        "x": [1] * 10,
        "label": [f"{e} (${v}K)" for e, v in zip(df["entity"], df["Q4"], strict=False)],
    }
)

# Custom tooltip format — letsplot-specific interactive feature
_tooltip_normal = (
    layer_tooltips()
    .title("@entity")
    .line("Q1 Sales|$@{y_start}K")
    .line("Q4 Sales|$@{y_end}K")
    .line("Change|@{change}K")
)
_tooltip_top = (
    layer_tooltips()
    .title("@entity  ★ Top mover")
    .line("Q1 Sales|$@{y_start}K")
    .line("Q4 Sales|$@{y_end}K")
    .line("Change|@{change}K")
)

plot = (
    ggplot()
    # Background lines: dimmed to let top movers stand out
    + geom_segment(
        data=seg_normal,
        mapping=aes(x="x_start", y="y_start", xend="x_end", yend="y_end", color="direction"),
        size=1.8,
        alpha=0.40,
        tooltips=_tooltip_normal,
    )
    # Top-mover lines: bold, fully opaque — emphasises biggest Q1→Q4 changes
    + geom_segment(
        data=seg_top,
        mapping=aes(x="x_start", y="y_start", xend="x_end", yend="y_end", color="direction"),
        size=3.5,
        alpha=1.0,
        tooltips=_tooltip_top,
    )
    + geom_point(data=df_long, mapping=aes(x="x", y="value", color="direction"), size=6)
    + geom_text(data=df_left, mapping=aes(x="x", y="value", label="label"), hjust=1.08, size=10, color=INK_SOFT)
    + geom_text(data=df_right, mapping=aes(x="x", y="value", label="label"), hjust=-0.08, size=10, color=INK_SOFT)
    + scale_color_manual(values={"Increase": COLOR_INCREASE, "Decrease": COLOR_DECREASE})
    + scale_x_continuous(breaks=[0, 1], labels=["Q1 Sales ($K)", "Q4 Sales ($K)"], limits=[-1.05, 2.05])
    + scale_y_continuous(limits=[25, 245])
    + labs(title="slope-basic · letsplot · anyplot.ai", x="", y="Sales ($K)", color="Change")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=GRID_COLOR, size=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=28, color=INK),
        axis_title_y=element_text(size=22, color=INK),
        axis_title_x=element_blank(),
        axis_text_x=element_text(size=20, color=INK_SOFT),
        axis_text_y=element_text(size=18, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=20, color=INK),
        legend_text=element_text(size=18, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x → 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for letsplot interactive tooltips
ggsave(plot, f"plot-{THEME}.html", path=".")
