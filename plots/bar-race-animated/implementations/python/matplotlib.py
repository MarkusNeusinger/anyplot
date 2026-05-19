"""anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-19
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data: Tech Company Market Cap ($B) — year-end snapshots (2019–2024)
companies = ["Alphabet", "Amazon", "Apple", "Meta", "Microsoft", "Nvidia", "Tesla"]
company_colors = {c: OKABE_ITO[i] for i, c in enumerate(companies)}

market_cap = {
    "Alphabet": [920, 1200, 1960, 1140, 1800, 2150],
    "Amazon": [940, 1640, 1730, 855, 1570, 2170],
    "Apple": [1050, 2250, 2950, 2070, 2990, 3750],
    "Meta": [580, 780, 890, 335, 940, 1440],
    "Microsoft": [1200, 1680, 2530, 1790, 2800, 3130],
    "Nvidia": [145, 325, 745, 365, 1220, 3280],
    "Tesla": [75, 670, 1060, 388, 790, 695],
}
years = [2019, 2020, 2021, 2022, 2023, 2024]

max_val = max(v for vlist in market_cap.values() for v in vlist)

# GridSpec gives precise control over subplot spacing
fig = plt.figure(figsize=(20, 11), facecolor=PAGE_BG)
gs = GridSpec(2, 3, figure=fig)
axes = [fig.add_subplot(gs[i // 3, i % 3]) for i in range(6)]

for idx, (year, ax) in enumerate(zip(years, axes, strict=False)):
    ax.set_facecolor(PAGE_BG)

    # Sort ascending so highest-value company tops the chart
    snapshot = {c: market_cap[c][idx] for c in companies}
    sorted_items = sorted(snapshot.items(), key=lambda x: x[1])
    names = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]
    bar_colors = [company_colors[n] for n in names]

    bars = ax.barh(names, values, color=bar_colors, height=0.72, edgecolor=PAGE_BG, linewidth=0.8)

    # Nvidia tracked across all panels with a distinctive colored border
    for name, bar in zip(names, bars, strict=False):
        if name == "Nvidia":
            bar.set_edgecolor(company_colors["Nvidia"])
            bar.set_linewidth(2.0)

    # Value labels — Nvidia's label rendered in brand color with stroke for legibility
    offset = max_val * 0.015
    for i, (name, val) in enumerate(zip(names, values, strict=False)):
        is_nvidia = name == "Nvidia"
        txt = ax.text(
            val + offset,
            i,
            f"${val:,}B",
            va="center",
            ha="left",
            fontsize=13,
            color=company_colors["Nvidia"] if is_nvidia else INK_SOFT,
            fontweight="bold" if is_nvidia else "normal",
        )
        if is_nvidia:
            txt.set_path_effects([pe.withStroke(linewidth=2, foreground=PAGE_BG), pe.Normal()])

    ax.set_title(str(year), fontsize=20, fontweight="bold", color=INK, pad=8)
    ax.set_xlim(0, max_val * 1.38)
    ax.set_xlabel("Market Cap ($B)", fontsize=14, color=INK_MUTED, labelpad=4)
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT, length=0)
    for spine in ("top", "right", "bottom"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(INK_SOFT)

    # Final panel: annotate Nvidia's historic rise + inset sparkline
    if idx == 5 and "Nvidia" in names:
        nv_pos = names.index("Nvidia")
        nv_val = values[nv_pos]
        nv_color = company_colors["Nvidia"]
        growth = nv_val / market_cap["Nvidia"][0]

        # Arrow annotation pointing to Nvidia's bar from safe empty space between rows
        ax.annotate(
            f" ×{growth:.0f} since 2019 ",
            xy=(nv_val, nv_pos),
            xytext=(max_val * 0.72, 2.5),
            fontsize=14,
            fontweight="bold",
            color=nv_color,
            arrowprops={"arrowstyle": "-|>", "color": nv_color, "lw": 2.0, "connectionstyle": "arc3,rad=-0.25"},
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": ELEVATED_BG,
                "edgecolor": nv_color,
                "linewidth": 1.5,
                "alpha": 0.92,
            },
        )

        # Inset sparkline in the empty lower-right area: Nvidia 2019→2024 trajectory
        ax_spark = ax.inset_axes([0.35, 0.04, 0.60, 0.20])
        ax_spark.set_facecolor(ELEVATED_BG)
        nv_vals = [market_cap["Nvidia"][y_idx] for y_idx in range(len(years))]
        ax_spark.plot(years, nv_vals, color=nv_color, lw=2.0, marker="o", markersize=4.5, solid_capstyle="round")
        ax_spark.fill_between(years, nv_vals, alpha=0.15, color=nv_color)
        ax_spark.set_xticks(years)
        ax_spark.set_xticklabels([str(y) for y in years], fontsize=9, color=INK_MUTED, rotation=30, ha="right")
        ax_spark.set_yticks([])
        ax_spark.tick_params(length=0)
        for sp in ax_spark.spines.values():
            sp.set_color(INK_SOFT)
            sp.set_linewidth(0.5)
        ax_spark.text(
            0.5,
            1.08,
            "Nvidia $145B → $3,280B",
            transform=ax_spark.transAxes,
            fontsize=9,
            ha="center",
            color=INK_MUTED,
            fontweight="bold",
        )

fig.suptitle(
    "Tech Giant Market Cap · bar-race-animated · python · matplotlib · anyplot.ai",
    fontsize=24,
    fontweight="medium",
    color=INK,
)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
plt.close()
