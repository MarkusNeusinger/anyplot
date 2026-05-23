""" anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 77/100 | Updated: 2026-05-23
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ACCENT = "#009E73"

anyplot_seq = LinearSegmentedColormap.from_list("anyplot_seq", ["#009E73", "#003D94"])

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

np.random.seed(42)

# Data: Europe → Germany → Bavaria  (annual sales revenue, €M)
countries_data = {
    "Germany": {"lon": 10.5, "lat": 51.0, "value": 4200, "bounds": (5.8, 15.0, 47.2, 55.0)},
    "France": {"lon": 2.5, "lat": 46.5, "value": 3100, "bounds": (-5.0, 8.2, 42.2, 51.2)},
    "UK": {"lon": -2.5, "lat": 54.0, "value": 2800, "bounds": (-8.0, 2.0, 49.8, 60.8)},
    "Spain": {"lon": -3.5, "lat": 40.0, "value": 1900, "bounds": (-9.5, 4.5, 36.0, 44.0)},
    "Italy": {"lon": 12.5, "lat": 42.5, "value": 2200, "bounds": (6.5, 18.5, 36.5, 47.5)},
}

germany_states_data = {
    "Bavaria": {"lon": 11.5, "lat": 48.8, "value": 1100, "bounds": (9.0, 13.8, 47.2, 50.5)},
    "Baden-Württ.": {"lon": 8.7, "lat": 48.5, "value": 850, "bounds": (7.5, 10.5, 47.5, 49.8)},
    "NRW": {"lon": 7.5, "lat": 51.5, "value": 1200, "bounds": (5.9, 9.4, 50.3, 52.5)},
    "Hesse": {"lon": 9.0, "lat": 50.6, "value": 680, "bounds": (7.7, 10.2, 49.4, 51.7)},
    "Saxony": {"lon": 13.3, "lat": 51.0, "value": 520, "bounds": (11.9, 15.0, 50.2, 51.7)},
    "Brandenburg": {"lon": 13.0, "lat": 52.5, "value": 340, "bounds": (11.3, 14.8, 51.4, 53.6)},
}

bavaria_cities_data = {
    "Munich": {"lon": 11.58, "lat": 48.14, "value": 450},
    "Nuremberg": {"lon": 11.08, "lat": 49.45, "value": 280},
    "Augsburg": {"lon": 10.90, "lat": 48.37, "value": 160},
    "Regensburg": {"lon": 12.10, "lat": 49.02, "value": 140},
    "Ingolstadt": {"lon": 11.43, "lat": 48.76, "value": 95},
    "Würzburg": {"lon": 9.93, "lat": 49.80, "value": 75},
}

all_values = (
    [c["value"] for c in countries_data.values()]
    + [s["value"] for s in germany_states_data.values()]
    + [c["value"] for c in bavaria_cities_data.values()]
)
vmin, vmax = min(all_values), max(all_values)
norm = plt.Normalize(vmin=vmin, vmax=vmax)

# Figure — exact 3200 × 1800 px canvas
fig, axes = plt.subplots(1, 3, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# --- Panel 1: European countries ---
ax1 = axes[0]
ax1.set_facecolor(PAGE_BG)

for name, data in countries_data.items():
    b = data["bounds"]
    rect = Rectangle(
        (b[0], b[2]),
        b[1] - b[0],
        b[3] - b[2],
        facecolor=anyplot_seq(norm(data["value"])),
        edgecolor=ACCENT if name == "Germany" else INK_SOFT,
        linewidth=3.5 if name == "Germany" else 0.8,
        alpha=0.92 if name == "Germany" else 0.72,
    )
    ax1.add_patch(rect)

for name, data in countries_data.items():
    ax1.text(data["lon"], data["lat"] + 0.8, name, fontsize=6.5, ha="center", fontweight="bold", color=INK)
    ax1.text(data["lon"], data["lat"] - 1.6, f"€{data['value']}M", fontsize=6, ha="center", color=INK_SOFT)

# Centroid scatter via seaborn — visible size+hue encoding
country_df = pd.DataFrame([{"lon": v["lon"], "lat": v["lat"], "value": v["value"]} for v in countries_data.values()])
sns.scatterplot(
    data=country_df,
    x="lon",
    y="lat",
    size="value",
    sizes=(40, 120),
    hue="value",
    palette=anyplot_seq,
    hue_norm=(vmin, vmax),
    edgecolors=PAGE_BG,
    linewidth=0.5,
    alpha=0.6,
    ax=ax1,
    legend=False,
)

ax1.set_xlim(-11, 23)
ax1.set_ylim(33, 64)
ax1.set_title("Level 1: Countries", fontsize=10, fontweight="medium", color=INK, pad=3)
ax1.set_xlabel("Longitude (°)", fontsize=8, color=INK)
ax1.set_ylabel("Latitude (°)", fontsize=8, color=INK)
ax1.tick_params(axis="both", labelsize=7, colors=INK_SOFT)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.spines["left"].set_color(INK_SOFT)
ax1.spines["bottom"].set_color(INK_SOFT)
ax1.text(
    0.04,
    0.97,
    "Europe",
    transform=ax1.transAxes,
    fontsize=7,
    fontweight="bold",
    color=ACCENT,
    va="top",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": ACCENT, "alpha": 0.9},
)

# --- Panel 2: German states ---
ax2 = axes[1]
ax2.set_facecolor(PAGE_BG)

for name, data in germany_states_data.items():
    b = data["bounds"]
    rect = Rectangle(
        (b[0], b[2]),
        b[1] - b[0],
        b[3] - b[2],
        facecolor=anyplot_seq(norm(data["value"])),
        edgecolor=ACCENT if name == "Bavaria" else INK_SOFT,
        linewidth=3.5 if name == "Bavaria" else 0.8,
        alpha=0.92 if name == "Bavaria" else 0.72,
    )
    ax2.add_patch(rect)
    ax2.text(data["lon"], data["lat"] + 0.35, name, fontsize=6.5, ha="center", fontweight="bold", color=INK)
    ax2.text(data["lon"], data["lat"] - 0.65, f"€{data['value']}M", fontsize=6, ha="center", color=INK_SOFT)

# Centroid scatter via seaborn — visible size+hue encoding
state_df = pd.DataFrame([{"lon": v["lon"], "lat": v["lat"], "value": v["value"]} for v in germany_states_data.values()])
sns.scatterplot(
    data=state_df,
    x="lon",
    y="lat",
    size="value",
    sizes=(40, 120),
    hue="value",
    palette=anyplot_seq,
    hue_norm=(vmin, vmax),
    edgecolors=PAGE_BG,
    linewidth=0.5,
    alpha=0.6,
    ax=ax2,
    legend=False,
)

ax2.set_xlim(5.0, 16.0)
ax2.set_ylim(46.5, 55.4)
ax2.set_title("Level 2: States (Germany)", fontsize=10, fontweight="medium", color=INK, pad=3)
ax2.set_xlabel("Longitude (°)", fontsize=8, color=INK)
ax2.set_ylabel("", fontsize=8)
ax2.tick_params(axis="both", labelsize=7, colors=INK_SOFT)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.spines["left"].set_color(INK_SOFT)
ax2.spines["bottom"].set_color(INK_SOFT)
ax2.text(
    0.04,
    0.97,
    "Europe > Germany",
    transform=ax2.transAxes,
    fontsize=7,
    fontweight="bold",
    color=ACCENT,
    va="top",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": ACCENT, "alpha": 0.9},
)

# --- Panel 3: Bavarian cities (seaborn scatter with size + hue) ---
ax3 = axes[2]
ax3.set_facecolor(PAGE_BG)

bav = germany_states_data["Bavaria"]
ax3.add_patch(
    Rectangle(
        (bav["bounds"][0], bav["bounds"][2]),
        bav["bounds"][1] - bav["bounds"][0],
        bav["bounds"][3] - bav["bounds"][2],
        facecolor=anyplot_seq(norm(bav["value"])),
        edgecolor=ACCENT,
        linewidth=1.2,
        alpha=0.25,
    )
)

cities_df = pd.DataFrame(
    [{"name": k, "lon": v["lon"], "lat": v["lat"], "value": v["value"]} for k, v in bavaria_cities_data.items()]
)

sns.scatterplot(
    data=cities_df,
    x="lon",
    y="lat",
    size="value",
    sizes=(50, 320),
    hue="value",
    palette=anyplot_seq,
    hue_norm=(vmin, vmax),
    edgecolors=PAGE_BG,
    linewidth=0.5,
    alpha=0.85,
    ax=ax3,
    legend=False,
)

# City labels — manual offsets to avoid overlap
label_cfg = {
    "Augsburg": {"dx": -0.30, "dy_n": -0.20, "dy_v": -0.40, "ha": "right"},
    "Ingolstadt": {"dx": +0.28, "dy_n": +0.10, "dy_v": -0.12, "ha": "left"},
}
for _, row in cities_df.iterrows():
    cfg = label_cfg.get(row["name"])
    if cfg:
        ax3.text(
            row["lon"] + cfg["dx"],
            row["lat"] + cfg["dy_n"],
            row["name"],
            fontsize=6,
            ha=cfg["ha"],
            va="center",
            fontweight="bold",
            color=INK,
        )
        ax3.text(
            row["lon"] + cfg["dx"],
            row["lat"] + cfg["dy_v"],
            f"€{int(row['value'])}M",
            fontsize=5,
            ha=cfg["ha"],
            va="center",
            color=INK_SOFT,
        )
    else:
        ax3.text(
            row["lon"],
            row["lat"] + 0.20,
            row["name"],
            fontsize=6,
            ha="center",
            va="bottom",
            fontweight="bold",
            color=INK,
        )
        ax3.text(
            row["lon"], row["lat"] - 0.18, f"€{int(row['value'])}M", fontsize=5, ha="center", va="top", color=INK_SOFT
        )

ax3.set_xlim(9.3, 13.2)
ax3.set_ylim(46.9, 50.8)
ax3.set_title("Level 3: Cities (Bavaria)", fontsize=10, fontweight="medium", color=INK, pad=3)
ax3.set_xlabel("Longitude (°)", fontsize=8, color=INK)
ax3.set_ylabel("", fontsize=8)
ax3.tick_params(axis="both", labelsize=7, colors=INK_SOFT)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
ax3.spines["left"].set_color(INK_SOFT)
ax3.spines["bottom"].set_color(INK_SOFT)
ax3.text(
    0.04,
    0.97,
    "Europe > Germany > Bavaria",
    transform=ax3.transAxes,
    fontsize=6.5,
    fontweight="bold",
    color=ACCENT,
    va="top",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": ACCENT, "alpha": 0.9},
)

# Drill-down arrows between panels
for xpos in (0.356, 0.662):
    fig.text(xpos, 0.535, "→", fontsize=16, ha="center", va="center", color=ACCENT, fontweight="bold")

# Main title
fig.suptitle(
    "map-drilldown-geographic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.98
)

# Layout — reserve bottom for colorbar, place it via add_axes to avoid overlap
fig.subplots_adjust(left=0.08, right=0.94, top=0.88, bottom=0.28, wspace=0.33)

sm = plt.cm.ScalarMappable(cmap=anyplot_seq, norm=norm)
cbar_ax = fig.add_axes([0.10, 0.12, 0.82, 0.038])
cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
cbar.set_label("Sales Revenue (€M)", fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
