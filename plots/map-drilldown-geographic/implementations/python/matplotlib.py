"""anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-23
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BOX_TEXT = "#F0EFE8"  # light text on dark anyplot_seq boxes (good contrast on both ends)
HIGHLIGHT = "#9418DB"  # anyplot palette position 2 — selected-region indicator

# anyplot sequential colormap: green → dark azure (single-polarity continuous)
anyplot_seq = LinearSegmentedColormap.from_list("anyplot_seq", ["#009E73", "#003D94"])

# Data: Three-level hierarchy — Annual Sales Drill-down (World → USA → California)
world_regions = {"North America": 245, "South America": 68, "Europe": 189, "Africa": 42, "Asia": 312, "Oceania": 34}
world_labels = {
    "North America": "N.AM",
    "South America": "S.AM",
    "Europe": "EUR",
    "Africa": "AFR",
    "Asia": "ASIA",
    "Oceania": "OCE",
}
world_values_text = {
    "North America": "$245B",
    "South America": "$68B",
    "Europe": "$189B",
    "Africa": "$42B",
    "Asia": "$312B",
    "Oceania": "$34B",
}
world_positions = {
    "North America": (1, 2),
    "South America": (1, 0),
    "Europe": (2, 2),
    "Africa": (2, 1),
    "Asia": (3, 2),
    "Oceania": (3, 0),
}

us_states = {
    "California": 42500,
    "Texas": 31200,
    "New York": 28900,
    "Florida": 19800,
    "Illinois": 16500,
    "Pennsylvania": 14200,
    "Ohio": 12800,
    "Georgia": 11500,
    "Michigan": 10200,
    "Washington": 9800,
}
state_labels = {
    "California": "CA",
    "Texas": "TX",
    "New York": "NY",
    "Florida": "FL",
    "Illinois": "IL",
    "Pennsylvania": "PA",
    "Ohio": "OH",
    "Georgia": "GA",
    "Michigan": "MI",
    "Washington": "WA",
}
state_values_text = {
    "California": "$42.5M",
    "Texas": "$31.2M",
    "New York": "$28.9M",
    "Florida": "$19.8M",
    "Illinois": "$16.5M",
    "Pennsylvania": "$14.2M",
    "Ohio": "$12.8M",
    "Georgia": "$11.5M",
    "Michigan": "$10.2M",
    "Washington": "$9.8M",
}
state_positions = {
    "California": (0, 2),
    "Washington": (0, 3),
    "Texas": (1, 1),
    "Florida": (2, 0),
    "Illinois": (1, 2),
    "New York": (2, 3),
    "Pennsylvania": (2, 2),
    "Ohio": (1, 3),
    "Georgia": (2, 1),
    "Michigan": (0, 4),
}

ca_cities = {
    "Los Angeles": 12800,
    "San Francisco": 8600,
    "San Diego": 5200,
    "San Jose": 4800,
    "Sacramento": 2400,
    "Oakland": 2100,
    "Fresno": 1800,
    "Long Beach": 1600,
    "Irvine": 1400,
    "Santa Monica": 1200,
}
city_labels = {
    "Los Angeles": "LA",
    "San Francisco": "SF",
    "San Diego": "SD",
    "San Jose": "SJ",
    "Sacramento": "SAC",
    "Oakland": "OAK",
    "Fresno": "FRE",
    "Long Beach": "LB",
    "Irvine": "IRV",
    "Santa Monica": "SM",
}
city_values_text = {
    "Los Angeles": "$12.8M",
    "San Francisco": "$8.6M",
    "San Diego": "$5.2M",
    "San Jose": "$4.8M",
    "Sacramento": "$2.4M",
    "Oakland": "$2.1M",
    "Fresno": "$1.8M",
    "Long Beach": "$1.6M",
    "Irvine": "$1.4M",
    "Santa Monica": "$1.2M",
}
city_positions = {
    "Los Angeles": (1, 1),
    "San Francisco": (0, 3),
    "San Diego": (1, 0),
    "San Jose": (0, 2),
    "Sacramento": (1, 3),
    "Oakland": (0, 4),
    "Fresno": (1, 2),
    "Long Beach": (2, 1),
    "Irvine": (2, 0),
    "Santa Monica": (0, 1),
}

# Global color normalization: all values converted to $M for consistent cross-level scale
world_regions_m = {k: v * 1000 for k, v in world_regions.items()}
all_values_m = list(world_regions_m.values()) + list(us_states.values()) + list(ca_cities.values())
global_vmin = min(all_values_m)
global_vmax = max(all_values_m)
global_norm = Normalize(vmin=global_vmin, vmax=global_vmax)

# Figure — 3200 × 1800 px (landscape 16:9)
fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
gs = fig.add_gridspec(1, 3, left=0.04, right=0.88, top=0.84, bottom=0.14, wspace=0.20)
axes = [fig.add_subplot(gs[0, i]) for i in range(3)]
for ax in axes:
    ax.set_facecolor(PAGE_BG)

# ---- Panel 1: World Regions ----
patches1, colors1 = [], []
for name in world_positions:
    col, row = world_positions[name]
    patches1.append(
        mpatches.FancyBboxPatch(
            (col * 1.2, row * 1.2),
            1.0,
            1.0,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            linewidth=1.5,
            edgecolor=PAGE_BG,
        )
    )
    colors1.append(anyplot_seq(global_norm(world_regions_m[name])))

axes[0].add_collection(PatchCollection(patches1, facecolors=colors1, edgecolors=PAGE_BG, linewidths=1.5))

for name in world_positions:
    col, row = world_positions[name]
    cx, cy = col * 1.2 + 0.5, row * 1.2 + 0.5
    axes[0].text(
        cx, cy + 0.12, world_labels[name], ha="center", va="center", fontsize=7, fontweight="bold", color=BOX_TEXT
    )
    axes[0].text(cx, cy - 0.14, world_values_text[name], ha="center", va="center", fontsize=6, color=BOX_TEXT)

hcol, hrow = world_positions["North America"]
axes[0].add_patch(
    mpatches.FancyBboxPatch(
        (hcol * 1.2 - 0.06, hrow * 1.2 - 0.06),
        1.12,
        1.12,
        boxstyle="round,pad=0.02,rounding_size=0.13",
        linewidth=3.5,
        edgecolor=HIGHLIGHT,
        facecolor="none",
        zorder=10,
    )
)

axes[0].set_xlim(0.9, 4.9)
axes[0].set_ylim(-0.3, 3.8)
axes[0].set_aspect("equal")
axes[0].axis("off")
axes[0].set_title("Level 1: World Regions", fontsize=9, fontweight="bold", color=INK, pad=6)
axes[0].text(0.5, -0.11, "World", transform=axes[0].transAxes, ha="center", fontsize=7, color=INK_MUTED, style="italic")

# ---- Panel 2: US States ----
patches2, colors2 = [], []
for name in state_positions:
    col, row = state_positions[name]
    patches2.append(
        mpatches.FancyBboxPatch(
            (col * 1.2, row * 1.2),
            1.0,
            1.0,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            linewidth=1.5,
            edgecolor=PAGE_BG,
        )
    )
    colors2.append(anyplot_seq(global_norm(us_states[name])))

axes[1].add_collection(PatchCollection(patches2, facecolors=colors2, edgecolors=PAGE_BG, linewidths=1.5))

for name in state_positions:
    col, row = state_positions[name]
    cx, cy = col * 1.2 + 0.5, row * 1.2 + 0.5
    axes[1].text(
        cx, cy + 0.12, state_labels[name], ha="center", va="center", fontsize=7, fontweight="bold", color=BOX_TEXT
    )
    axes[1].text(cx, cy - 0.14, state_values_text[name], ha="center", va="center", fontsize=6, color=BOX_TEXT)

hcol2, hrow2 = state_positions["California"]
axes[1].add_patch(
    mpatches.FancyBboxPatch(
        (hcol2 * 1.2 - 0.06, hrow2 * 1.2 - 0.06),
        1.12,
        1.12,
        boxstyle="round,pad=0.02,rounding_size=0.13",
        linewidth=3.5,
        edgecolor=HIGHLIGHT,
        facecolor="none",
        zorder=10,
    )
)

axes[1].set_xlim(-0.5, 4.0)
axes[1].set_ylim(-0.8, 6.2)
axes[1].set_aspect("equal")
axes[1].axis("off")
axes[1].set_title("Level 2: US States", fontsize=9, fontweight="bold", color=INK, pad=6)
axes[1].text(
    0.5,
    -0.11,
    "World ▶ United States",
    transform=axes[1].transAxes,
    ha="center",
    fontsize=7,
    color=INK_MUTED,
    style="italic",
)

# ---- Panel 3: California Cities ----
patches3, colors3 = [], []
for name in city_positions:
    col, row = city_positions[name]
    patches3.append(
        mpatches.FancyBboxPatch(
            (col * 1.2, row * 1.2),
            1.0,
            1.0,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            linewidth=1.5,
            edgecolor=PAGE_BG,
        )
    )
    colors3.append(anyplot_seq(global_norm(ca_cities[name])))

axes[2].add_collection(PatchCollection(patches3, facecolors=colors3, edgecolors=PAGE_BG, linewidths=1.5))

for name in city_positions:
    col, row = city_positions[name]
    cx, cy = col * 1.2 + 0.5, row * 1.2 + 0.5
    axes[2].text(
        cx, cy + 0.12, city_labels[name], ha="center", va="center", fontsize=7, fontweight="bold", color=BOX_TEXT
    )
    axes[2].text(cx, cy - 0.14, city_values_text[name], ha="center", va="center", fontsize=6, color=BOX_TEXT)

axes[2].set_xlim(-0.5, 4.0)
axes[2].set_ylim(-0.8, 6.2)
axes[2].set_aspect("equal")
axes[2].axis("off")
axes[2].set_title("Level 3: CA Cities", fontsize=9, fontweight="bold", color=INK, pad=6)
axes[2].text(
    0.5,
    -0.11,
    "World ▶ United States ▶ California",
    transform=axes[2].transAxes,
    ha="center",
    fontsize=7,
    color=INK_MUTED,
    style="italic",
)

# Colorbar — consistent scale across all three hierarchy levels
sm = plt.cm.ScalarMappable(cmap=anyplot_seq, norm=global_norm)
sm.set_array([])
cbar_ax = fig.add_axes([0.905, 0.18, 0.020, 0.52])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label("Annual Sales", fontsize=7, color=INK_SOFT, labelpad=3)
cbar.ax.tick_params(labelsize=6, colors=INK_SOFT, length=2)
cbar.set_ticks([global_vmin, (global_vmin + global_vmax) / 2, global_vmax])
cbar.set_ticklabels(["$1.2M", "$157B", "$312B"])
cbar.outline.set_edgecolor(INK_SOFT)
cbar.outline.set_linewidth(0.5)

# Drill-down arrows between panels
for i in range(2):
    x_start = axes[i].get_position().x1 + 0.005
    x_end = axes[i + 1].get_position().x0 - 0.005
    y_mid = 0.46
    fig.patches.append(
        mpatches.FancyArrowPatch(
            (x_start, y_mid),
            (x_end, y_mid),
            transform=fig.transFigure,
            arrowstyle="-|>",
            color=HIGHLIGHT,
            lw=2,
            mutation_scale=14,
            zorder=100,
        )
    )

# Title and subtitle
fig.suptitle(
    "map-drilldown-geographic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.97
)
fig.text(
    0.46,
    0.90,
    "Annual Sales Drill-down: World → North America → California    ▸ = selected for next level",
    ha="center",
    fontsize=8,
    color=INK_SOFT,
)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
