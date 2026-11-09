""" anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: plotnine 0.15.8 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_manual,
    theme,
    theme_void,
)


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per plan tier in data order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BAND_ALPHA = (
    0.5 if THEME == "light" else 0.7
)  # translucent bands fade toward a dark page, so they need more opacity there
LABEL_INKS = ("#1A1A17", "#F0EFE8")  # block labels sit on the fixed fills, so they use whichever ink contrasts more

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: time_point
NEXT_QUARTER = "Next quarter"  # role: extra
PLAN = "Plan tier"  # role: category
NEXT_PLAN = "Next plan tier"  # role: extra
SUBSCRIBERS = "Subscribers (thousands)"  # role: value
MOVED = "Subscribers moving (thousands)"  # role: flow

# Data: replace this block with your own table, for example df = pd.read_csv("plan_moves.csv")
quarters = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]
plans = ["Basic", "Standard", "Premium"]
moves = [
    [38, 9, 3, 4, 26, 5, 1, 2, 12],  # Q1 -> Q2, from Basic, Standard, Premium to Basic, Standard, Premium
    [32, 8, 3, 3, 27, 7, 1, 2, 17],  # Q2 -> Q3
    [27, 6, 3, 3, 26, 8, 1, 3, 23],  # Q3 -> Q4
]
df = pd.DataFrame(
    {
        QUARTER: np.repeat(quarters[:-1], len(plans) ** 2),
        NEXT_QUARTER: np.repeat(quarters[1:], len(plans) ** 2),
        PLAN: np.tile(np.repeat(plans, len(plans)), len(quarters) - 1),
        NEXT_PLAN: np.tile(plans, len(plans) * (len(quarters) - 1)),
        MOVED: np.concatenate(moves),
    }
)

# Plot: reads only df and the constants above
flows = df.dropna(subset=[QUARTER, NEXT_QUARTER, PLAN, NEXT_PLAN, MOVED])
stages = pd.unique(pd.concat([flows[QUARTER], flows[NEXT_QUARTER]])).tolist()
tiers = pd.unique(pd.concat([flows[PLAN], flows[NEXT_PLAN]])).tolist()
fill_colors = dict(zip(tiers, IMPRINT_PALETTE, strict=False))  # tiers past the eighth fall back to the muted anchor

# Label ink per tier: WCAG relative luminance of the block fill and of both inks, then the higher contrast ratio
srgb = {
    c: np.array([int(c[i : i + 2], 16) for i in (1, 3, 5)]) / 255 for c in [*IMPRINT_PALETTE, INK_MUTED, *LABEL_INKS]
}
lum = {
    c: np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4) @ [0.2126, 0.7152, 0.0722]
    for c, v in srgb.items()
}
dark_ink, light_ink = LABEL_INKS
fill_lum = {tier: lum[fill_colors.get(tier, INK_MUTED)] for tier in tiers}
label_inks = {
    tier: dark_ink if (fl + 0.05) / (lum[dark_ink] + 0.05) >= (lum[light_ink] + 0.05) / (fl + 0.05) else light_ink
    for tier, fl in fill_lum.items()
}

# Block value: what leaves a block, or what arrives in it at the last time point
outflow = flows.groupby([QUARTER, PLAN], sort=False)[MOVED].sum()
inflow = flows.groupby([NEXT_QUARTER, NEXT_PLAN], sort=False)[MOVED].sum()
inflow.index.names = outflow.index.names
block_values = outflow.combine_first(inflow)

block_width = 0.32
gap = 0.05 * block_values.groupby(level=0).sum().max()
stack_heights = {
    stage: block_values[stage].sum() + gap * (len(block_values[stage]) - 1) for stage in block_values.index.levels[0]
}
tallest = max(stack_heights.values())

node_rows = []
for i, stage in enumerate(stages):
    y_top = (tallest + stack_heights[stage]) / 2
    for tier in tiers:
        value = block_values.get((stage, tier), np.nan)
        if not value > 0:
            continue
        node_rows.append(
            {
                PLAN: tier,
                SUBSCRIBERS: value,
                "x": i,
                "xmin": i - block_width / 2,
                "xmax": i + block_width / 2,
                "ymin": y_top - value,
                "ymax": y_top,
                "label": f"{tier}\n{value:,.0f}k",
                "label_color": label_inks[tier],
            }
        )
        y_top -= value + gap
nodes = pd.DataFrame(node_rows)
nodes["label_y"] = (nodes["ymin"] + nodes["ymax"]) / 2

# Bands: each one leaves its source block and enters its target block at a running offset from the top
out_cursor = {(stages[int(r["x"])], r[PLAN]): r["ymax"] for _, r in nodes.iterrows()}
in_cursor = dict(out_cursor)
curve = np.linspace(0, 1, 50)
ease = 3 * curve**2 - 2 * curve**3
band_parts = []
for k, row in flows.iterrows():
    source, target, flow = (row[QUARTER], row[PLAN]), (row[NEXT_QUARTER], row[NEXT_PLAN]), row[MOVED]
    if not flow > 0 or source not in out_cursor or target not in in_cursor:
        continue
    src_top, tgt_top = out_cursor[source], in_cursor[target]
    out_cursor[source] -= flow
    in_cursor[target] -= flow
    x_left = stages.index(source[0]) + block_width / 2
    x_right = stages.index(target[0]) - block_width / 2
    xs = x_left + (x_right - x_left) * curve
    upper = src_top + (tgt_top - src_top) * ease
    band_parts.append(
        pd.DataFrame(
            {
                "x": np.concatenate([xs, xs[::-1]]),
                "y": np.concatenate([upper, (upper - flow)[::-1]]),
                "band": k,
                PLAN: source[1],
            }
        )
    )
bands = pd.concat(band_parts, ignore_index=True)

header_y = tallest * 1.04
plot = (
    ggplot()
    + geom_polygon(bands, aes(x="x", y="y", group="band", fill=PLAN), alpha=BAND_ALPHA, color=None)
    + geom_rect(nodes, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill=PLAN), color=PAGE_BG, size=0.6)
    + geom_text(
        nodes, aes(x="x", y="label_y", label="label", color="label_color"), size=6.5, fontweight="bold", lineheight=1.1
    )
    + scale_color_identity()
    + annotate(
        "text", x=range(len(stages)), y=header_y, label=stages, color=INK, size=9, fontweight="bold", va="bottom"
    )
    + scale_fill_manual(values=fill_colors, limits=tiers, na_value=INK_MUTED)
    + coord_cartesian(xlim=(-0.35, len(stages) - 0.65), ylim=(0, header_y * 1.06), expand=False)
    + labs(
        title="alluvial-basic · python · plotnine · anyplot.ai",
        subtitle=f"Block height: {SUBSCRIBERS} per {PLAN.lower()} · Band width: {MOVED.lower()} to the next {QUARTER.lower()}",
    )
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=12, color=INK, weight="bold", ha="left"),
        plot_subtitle=element_text(size=8, color=INK_SOFT, ha="left"),
        plot_margin=0.03,
        legend_position="none",
        axis_text=element_blank(),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
