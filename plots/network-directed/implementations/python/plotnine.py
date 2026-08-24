"""anyplot.ai
network-directed: Directed Network Graph
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-08-24
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: Python package import graph for a web service — arrows point from an
# importing module to the module it depends on, showing build order bottom-up.
modules = [
    {"id": "config", "tier": "Foundation"},
    {"id": "logging", "tier": "Foundation"},
    {"id": "types", "tier": "Foundation"},
    {"id": "database", "tier": "Data access"},
    {"id": "cache", "tier": "Data access"},
    {"id": "http_client", "tier": "Data access"},
    {"id": "auth", "tier": "Domain services"},
    {"id": "user_service", "tier": "Domain services"},
    {"id": "payment_service", "tier": "Domain services"},
    {"id": "notification_service", "tier": "Domain services"},
    {"id": "api_gateway", "tier": "Gateway"},
    {"id": "admin_panel", "tier": "Gateway"},
    {"id": "public_api", "tier": "Gateway"},
    {"id": "web_app", "tier": "Application"},
    {"id": "worker", "tier": "Application"},
]

imports = [
    ("database", "config"),
    ("database", "logging"),
    ("cache", "config"),
    ("http_client", "logging"),
    ("http_client", "types"),
    ("auth", "database"),
    ("auth", "cache"),
    ("user_service", "database"),
    ("user_service", "auth"),
    ("payment_service", "database"),
    ("payment_service", "http_client"),
    ("notification_service", "http_client"),
    ("notification_service", "cache"),
    ("api_gateway", "auth"),
    ("api_gateway", "user_service"),
    ("admin_panel", "user_service"),
    ("admin_panel", "payment_service"),
    ("public_api", "payment_service"),
    ("public_api", "notification_service"),
    ("web_app", "api_gateway"),
    ("web_app", "public_api"),
    ("worker", "notification_service"),
    ("worker", "payment_service"),
]

# Layered layout: one row per tier, modules spread evenly across the row.
tier_order = ["Foundation", "Data access", "Domain services", "Gateway", "Application"]
tier_rows = {tier: [] for tier in tier_order}
for module in modules:
    tier_rows[module["tier"]].append(module["id"])

positions = {}
for row, tier in enumerate(tier_order):
    members = tier_rows[tier]
    count = len(members)
    xs = np.linspace(0.08, 0.92, count) if count > 1 else np.array([0.5])
    y = 0.08 + row * (0.84 / (len(tier_order) - 1))
    for module_id, x in zip(members, xs, strict=True):
        positions[module_id] = (float(x), float(y))

node_df = pd.DataFrame(
    {
        "x": [positions[m["id"]][0] for m in modules],
        "y": [positions[m["id"]][1] for m in modules],
        "label": [m["id"] for m in modules],
        "tier": pd.Categorical([m["tier"] for m in modules], categories=tier_order, ordered=True),
    }
)

# Pull the arrow endpoint back from the target node center so the arrowhead
# lands just outside the marker instead of hiding under it.
margin = 0.028
edge_rows = []
for src, tgt in imports:
    x0, y0 = positions[src]
    x1, y1 = positions[tgt]
    dx, dy = x1 - x0, y1 - y0
    dist = max((dx**2 + dy**2) ** 0.5, 1e-6)
    edge_rows.append(
        {
            "x": x0 + (dx / dist) * margin * 0.5,
            "y": y0 + (dy / dist) * margin * 0.5,
            "xend": x1 - (dx / dist) * margin,
            "yend": y1 - (dy / dist) * margin,
        }
    )
edge_df = pd.DataFrame(edge_rows)

tier_colors = dict(zip(tier_order, IMPRINT_PALETTE, strict=True))

# Plot
plot = (
    ggplot()
    + geom_segment(
        data=edge_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        color=INK_SOFT,
        size=0.5,
        alpha=0.6,
        arrow=arrow(angle=22, length=0.09, ends="last", type="closed"),
    )
    + geom_point(data=node_df, mapping=aes(x="x", y="y", color="tier"), size=8, alpha=0.95, stroke=0.6)
    + geom_text(data=node_df, mapping=aes(x="x", y="y", label="label"), color=INK, size=3.3, nudge_y=0.032, va="bottom")
    + scale_color_manual(values=tier_colors, name="Build tier")
    + coord_cartesian(xlim=(-0.02, 1.02), ylim=(-0.02, 1.05))
    + labs(title="network-directed · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        plot_title=element_text(color=INK, size=12, ha="center"),
        legend_background=element_rect(fill=ELEVATED_BG, color=None),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=9),
        legend_key=element_rect(fill=ELEVATED_BG),
        legend_box_spacing=0.01,
        plot_margin=0.01,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
