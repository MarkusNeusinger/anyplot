""" anyplot.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-19
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Corporate Annual Budget ($M)
budget = {
    "Engineering": {"Software Dev": 250, "Hardware": 100, "R&D": 50},
    "Marketing": {"Digital Ads": 150, "Events": 70, "PR": 30},
    "Operations": {"HR": 80, "Finance": 70, "Admin": 50},
    "Sales": {"Direct": 100, "Channel": 50},
}
cat_names = list(budget.keys())
cat_totals = {cat: sum(vals.values()) for cat, vals in budget.items()}
total = sum(cat_totals.values())  # $1000M

fig, (ax_tree, ax_sun) = plt.subplots(1, 2, figsize=(16, 9), facecolor=PAGE_BG)
fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.11, wspace=0.06)
ax_tree.set_facecolor(PAGE_BG)
ax_sun.set_facecolor(PAGE_BG)

# ── Treemap ───────────────────────────────────────────────────────────────────
ax_tree.set_xlim(0, 1)
ax_tree.set_ylim(0, 1)
ax_tree.axis("off")
ax_tree.set_title("Treemap", fontsize=22, color=INK, fontweight="medium", pad=12)

y_pos = 0.0
for i, (cat, items) in enumerate(budget.items()):
    cat_h = cat_totals[cat] / total
    n_items = len(items)
    x_pos = 0.0
    for j, (item, val) in enumerate(items.items()):
        item_w = val / cat_totals[cat]
        cell_alpha = 0.55 + 0.45 * ((n_items - 1 - j) / max(n_items - 1, 1))
        rect = mpatches.Rectangle(
            (x_pos + 0.004, y_pos + 0.004),
            item_w - 0.008,
            cat_h - 0.008,
            facecolor=COLORS[i],
            edgecolor=PAGE_BG,
            linewidth=3,
            alpha=cell_alpha,
            zorder=2,
        )
        ax_tree.add_patch(rect)
        if item_w > 0.10 and cat_h > 0.07:
            ax_tree.text(
                x_pos + item_w / 2,
                y_pos + cat_h / 2,
                f"{item}\n${val}M",
                ha="center",
                va="center",
                fontsize=11,
                color="white",
                fontweight="bold",
                zorder=4,
                linespacing=1.4,
            )
        x_pos += item_w
    # Category label at top-left of band
    ax_tree.text(
        0.010, y_pos + cat_h - 0.012, cat, ha="left", va="top", fontsize=13, color="white", fontweight="bold", zorder=5
    )
    y_pos += cat_h

# ── Sunburst ──────────────────────────────────────────────────────────────────
ax_sun.set_xlim(-1.15, 1.15)
ax_sun.set_ylim(-1.15, 1.15)
ax_sun.set_aspect("equal")
ax_sun.axis("off")
ax_sun.set_title("Sunburst", fontsize=22, color=INK, fontweight="medium", pad=12)

r_inner = 0.28
r_outer = 0.70
ring_gap = 0.05

start_deg = 90.0
for i, (cat, items) in enumerate(budget.items()):
    cat_sweep = (cat_totals[cat] / total) * 360
    end_deg = start_deg - cat_sweep

    # Inner ring: category
    wedge_in = mpatches.Wedge(
        (0, 0), r_inner, end_deg, start_deg, facecolor=COLORS[i], edgecolor=PAGE_BG, linewidth=2, zorder=2
    )
    ax_sun.add_patch(wedge_in)

    # Outer ring: items
    item_start = start_deg
    n_items = len(items)
    for j, (item, val) in enumerate(items.items()):
        item_sweep = (val / cat_totals[cat]) * cat_sweep
        item_end = item_start - item_sweep
        cell_alpha = 0.50 + 0.50 * ((n_items - 1 - j) / max(n_items - 1, 1))
        wedge_out = mpatches.Wedge(
            (0, 0),
            r_outer,
            item_end,
            item_start,
            width=r_outer - r_inner - ring_gap,
            facecolor=COLORS[i],
            edgecolor=PAGE_BG,
            linewidth=2,
            alpha=cell_alpha,
            zorder=2,
        )
        ax_sun.add_patch(wedge_out)

        if item_sweep >= 20:
            mid_deg = (item_start + item_end) / 2
            mid_rad = np.radians(mid_deg)
            r_mid = r_inner + ring_gap + (r_outer - r_inner - ring_gap) / 2
            ax_sun.text(
                np.cos(mid_rad) * r_mid,
                np.sin(mid_rad) * r_mid,
                f"{item}\n${val}M",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
                zorder=5,
                linespacing=1.3,
            )
        item_start = item_end
    start_deg = end_deg

# Center label
ax_sun.text(0, 0.05, f"${total}M", ha="center", va="center", fontsize=18, color=INK, fontweight="bold", zorder=6)
ax_sun.text(0, -0.08, "Total", ha="center", va="center", fontsize=13, color=INK_SOFT, zorder=6)

# Legend
legend_patches = [mpatches.Patch(facecolor=COLORS[i], label=cat_names[i]) for i in range(len(cat_names))]
leg = fig.legend(
    handles=legend_patches, loc="lower center", ncol=4, fontsize=15, frameon=True, bbox_to_anchor=(0.5, 0.01)
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.suptitle(
    "hierarchy-toggle-view · python · matplotlib · anyplot.ai", fontsize=20, color=INK, fontweight="medium", y=0.96
)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
