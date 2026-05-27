""" anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-27
"""

import os
import sys


_here = __file__.replace("\\", "/").rsplit("/", 1)[0]
sys.path = [p for p in sys.path if p not in ("", ".", _here)]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    arrow,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# anyplot categorical palette — hybrid-v3 order
ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Portfolio data — anyplot palette with semantic assignments
np.random.seed(42)

TOTAL_PORTFOLIO = 1_200_000

MAIN_COLORS = {
    "Equities": ANYPLOT_PALETTE[0],  # #009E73 green  — growth / equities
    "Fixed Income": ANYPLOT_PALETTE[2],  # #4467A3 blue   — stability / bonds
    "Alternatives": ANYPLOT_PALETTE[1],  # #C475FD lavender — non-standard assets
    "Cash": ANYPLOT_PALETTE[3],  # #BD8233 ochre  — value / currency
}
MAIN_WEIGHTS = {"Equities": 45, "Fixed Income": 30, "Alternatives": 15, "Cash": 10}

# Equities sub-holdings — semantic colors within holding categories
HOLDINGS = [
    {"name": "Tech Stocks", "weight": 18, "color": ANYPLOT_PALETTE[5]},  # #2ABCCD cyan  — tech
    {"name": "Healthcare", "weight": 12, "color": ANYPLOT_PALETTE[6]},  # #954477 rose  — health
    {"name": "Financials", "weight": 10, "color": ANYPLOT_PALETTE[2]},  # #4467A3 blue  — finance
    {"name": "Energy", "weight": 5, "color": ANYPLOT_PALETTE[3]},  # #BD8233 ochre — commodity
]

# Geometry constants
OUTER_R = 80
INNER_R = 40
OUTER_R_D = 62
INNER_R_D = 30
CX_MAIN = -95
CX_DETAIL = 90
CY = 0
GAP = 0.025
N_PTS = 50

# Build main donut polygons (asset classes) — inline, no function
rows_main = []
label_rows_main_pct = []
label_rows_main_usd = []
angle = np.pi / 2

for asset_class, weight in MAIN_WEIGHTS.items():
    color = MAIN_COLORS[asset_class]
    sweep = (weight / 100) * 2 * np.pi
    end_angle = angle - sweep
    arcs = np.linspace(end_angle + GAP, angle - GAP, N_PTS)
    outer_pts = list(zip(CX_MAIN + OUTER_R * np.cos(arcs), CY + OUTER_R * np.sin(arcs), strict=False))
    inner_pts = list(zip(CX_MAIN + INNER_R * np.cos(arcs[::-1]), CY + INNER_R * np.sin(arcs[::-1]), strict=False))
    all_pts = outer_pts + inner_pts + [outer_pts[0]]
    for order, (x, y) in enumerate(all_pts):
        rows_main.append({"x": x, "y": y, "segment": asset_class, "order": order, "fill": color})
    mid_a = (angle + end_angle) / 2
    pct_r = (INNER_R + OUTER_R) / 2 + 7
    usd_r = (INNER_R + OUTER_R) / 2 - 7
    dollar_val = weight / 100 * TOTAL_PORTFOLIO
    dollar_str = f"${dollar_val / 1000:.0f}K"
    label_rows_main_pct.append(
        {"x": CX_MAIN + pct_r * float(np.cos(mid_a)), "y": CY + pct_r * float(np.sin(mid_a)), "label": f"{weight}%"}
    )
    label_rows_main_usd.append(
        {"x": CX_MAIN + usd_r * float(np.cos(mid_a)), "y": CY + usd_r * float(np.sin(mid_a)), "label": dollar_str}
    )
    angle = end_angle

main_df = pd.DataFrame(rows_main)
main_label_pct_df = pd.DataFrame(label_rows_main_pct)
main_label_usd_df = pd.DataFrame(label_rows_main_usd)

# Build detail donut polygons (Equities breakdown) — inline, no function
rows_detail = []
label_rows_detail_pct = []
label_rows_detail_usd = []
angle = np.pi / 2
equities_total = MAIN_WEIGHTS["Equities"]

for holding in HOLDINGS:
    name = holding["name"]
    weight = holding["weight"]
    color = holding["color"]
    sweep = (weight / equities_total) * 2 * np.pi
    end_angle = angle - sweep
    arcs = np.linspace(end_angle + GAP, angle - GAP, N_PTS)
    outer_pts = list(zip(CX_DETAIL + OUTER_R_D * np.cos(arcs), CY + OUTER_R_D * np.sin(arcs), strict=False))
    inner_pts = list(zip(CX_DETAIL + INNER_R_D * np.cos(arcs[::-1]), CY + INNER_R_D * np.sin(arcs[::-1]), strict=False))
    all_pts = outer_pts + inner_pts + [outer_pts[0]]
    for order, (x, y) in enumerate(all_pts):
        rows_detail.append({"x": x, "y": y, "segment": name, "order": order, "fill": color})
    mid_a = (angle + end_angle) / 2
    pct_r = (INNER_R_D + OUTER_R_D) / 2 + 5
    usd_r = (INNER_R_D + OUTER_R_D) / 2 - 5
    dollar_val = weight / 100 * TOTAL_PORTFOLIO
    dollar_str = f"${dollar_val / 1000:.0f}K"
    label_rows_detail_pct.append(
        {"x": CX_DETAIL + pct_r * float(np.cos(mid_a)), "y": CY + pct_r * float(np.sin(mid_a)), "label": f"{weight}%"}
    )
    label_rows_detail_usd.append(
        {"x": CX_DETAIL + usd_r * float(np.cos(mid_a)), "y": CY + usd_r * float(np.sin(mid_a)), "label": dollar_str}
    )
    angle = end_angle

detail_df = pd.DataFrame(rows_detail)
detail_label_pct_df = pd.DataFrame(label_rows_detail_pct)
detail_label_usd_df = pd.DataFrame(label_rows_detail_usd)

# Connecting arrow — drill-down indicator from main to detail donut
arrow_df = pd.DataFrame([{"x": CX_MAIN + OUTER_R + 7, "y": 16, "xend": CX_DETAIL - OUTER_R_D - 7, "yend": 16}])

# Section titles — tightened y to reduce corner whitespace
TITLE_Y = 100
titles_df = pd.DataFrame(
    [
        {"x": CX_MAIN, "y": TITLE_Y, "label": "Portfolio Allocation"},
        {"x": CX_DETAIL, "y": TITLE_Y, "label": "Equities Breakdown"},
    ]
)

# Center hole labels — detail donut shows dollar value of equities allocation
center_df = pd.DataFrame(
    [
        {"x": CX_MAIN, "y": 7, "label": "Total"},
        {"x": CX_MAIN, "y": -10, "label": "$1.2M"},
        {"x": CX_DETAIL, "y": 5, "label": "$540K"},
        {"x": CX_DETAIL, "y": -10, "label": "Equities"},
    ]
)

# Legend at bottom — color boxes + text labels
leg_items = list(MAIN_WEIGHTS.keys())
LEG_X_START = -152
LEG_Y = -106
LEG_SPACING = 80
BOX_SIZE = 10

legend_text_df = pd.DataFrame(
    [{"x": LEG_X_START + i * LEG_SPACING + BOX_SIZE + 3, "y": LEG_Y, "label": name} for i, name in enumerate(leg_items)]
)

box_rows = []
for i, name in enumerate(leg_items):
    x0 = LEG_X_START + i * LEG_SPACING
    y0 = LEG_Y
    pts = [
        (x0, y0 - BOX_SIZE / 2),
        (x0 + BOX_SIZE, y0 - BOX_SIZE / 2),
        (x0 + BOX_SIZE, y0 + BOX_SIZE / 2),
        (x0, y0 + BOX_SIZE / 2),
        (x0, y0 - BOX_SIZE / 2),
    ]
    for order, (x, y) in enumerate(pts):
        box_rows.append({"x": x, "y": y, "segment": f"box_{name}", "order": order, "fill": MAIN_COLORS[name]})
legend_box_df = pd.DataFrame(box_rows)

# Title — scale fontsize if longer than 67-char baseline
title_str = "pie-portfolio-interactive · python · plotnine · anyplot.ai"
n_chars = len(title_str)
title_fs = max(8, round(12 * (67 / n_chars if n_chars > 67 else 1.0)))

# Plot
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", group="segment", fill="fill"), data=main_df, color=PAGE_BG, size=0.8, alpha=0.97)
    + geom_polygon(aes(x="x", y="y", group="segment", fill="fill"), data=detail_df, color=PAGE_BG, size=0.8, alpha=0.97)
    + geom_text(aes(x="x", y="y", label="label"), data=main_label_pct_df, size=3.5, fontweight="bold", color="#FFFFFF")
    + geom_text(aes(x="x", y="y", label="label"), data=main_label_usd_df, size=3.0, color="#FFFFFF")
    + geom_text(
        aes(x="x", y="y", label="label"), data=detail_label_pct_df, size=3.2, fontweight="bold", color="#FFFFFF"
    )
    + geom_text(aes(x="x", y="y", label="label"), data=detail_label_usd_df, size=2.8, color="#FFFFFF")
    + geom_segment(
        aes(x="x", xend="xend", y="y", yend="yend"),
        data=arrow_df,
        color=INK_SOFT,
        size=1.0,
        linetype="dashed",
        arrow=arrow(length=0.10, type="closed"),
    )
    + geom_text(aes(x="x", y="y", label="label"), data=titles_df, size=5.2, fontweight="bold", color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=center_df, size=3.8, color=INK_SOFT)
    + geom_polygon(aes(x="x", y="y", group="segment", fill="fill"), data=legend_box_df, color=INK_SOFT, size=0.3)
    + geom_text(aes(x="x", y="y", label="label"), data=legend_text_df, size=2.8, ha="left", color=INK_SOFT)
    + scale_fill_identity()
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-195, 185))
    + scale_y_continuous(limits=(-118, 113))
    + labs(title=title_str)
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=title_fs, ha="center", color=INK, weight="bold"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
