"""pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-15
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path


# Data
np.random.seed(42)
hours = 8760

base_load = 400
peak_load = 1200

hourly_load = np.concatenate(
    [
        np.random.normal(1100, 60, int(hours * 0.05)),
        np.random.normal(900, 80, int(hours * 0.15)),
        np.random.normal(750, 70, int(hours * 0.30)),
        np.random.normal(600, 50, int(hours * 0.30)),
        np.random.normal(480, 30, int(hours * 0.20)),
    ]
)
hourly_load = np.clip(hourly_load, base_load, peak_load)
extra = hours - len(hourly_load)
if extra > 0:
    hourly_load = np.concatenate([hourly_load, np.random.normal(500, 40, extra)])
hourly_load = hourly_load[:hours]
load_mw = np.sort(hourly_load)[::-1]
hour = np.arange(hours)

peak_threshold = 950
intermediate_threshold = 600

peak_end = np.searchsorted(-load_mw, -peak_threshold)
base_start = np.searchsorted(-load_mw, -intermediate_threshold)

total_energy_gwh = np.trapezoid(load_mw, hour) / 1000

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.set_facecolor("#fafafa")
ax.set_facecolor("#fafafa")

# Gradient fill under the curve using imshow + clip path
gradient_cmap = LinearSegmentedColormap.from_list("load_gradient", ["#D32F2F", "#F57C00", "#1976D2"], N=256)
gradient_img = ax.imshow(
    np.linspace(0, 1, 256).reshape(1, -1),
    aspect="auto",
    cmap=gradient_cmap,
    extent=[0, hours, base_load - 30, load_mw[0]],
    alpha=0.28,
    zorder=1,
)
# Clip gradient to area under curve
verts = list(zip(hour, load_mw, strict=False))
verts.append((hours, base_load - 30))
verts.append((0, base_load - 30))
verts.append(verts[0])
clip_path = Path(verts)
clip_patch = PathPatch(clip_path, transform=ax.transData, facecolor="none", edgecolor="none")
ax.add_patch(clip_patch)
gradient_img.set_clip_path(clip_patch)

# Region boundary fills with subtle coloring
ax.fill_between(hour[: peak_end + 1], load_mw[: peak_end + 1], peak_threshold, color="#D32F2F", alpha=0.15, zorder=2)
ax.fill_between(
    hour[peak_end : base_start + 1],
    load_mw[peak_end : base_start + 1],
    intermediate_threshold,
    color="#F57C00",
    alpha=0.15,
    zorder=2,
)
ax.fill_between(hour[base_start:], load_mw[base_start:], base_load, color="#1976D2", alpha=0.15, zorder=2)

# Main curve with path effects for depth
curve_shadow = [pe.SimpleLineShadow(offset=(1.5, -1.5), shadow_color="#00000022", linewidth=4)]
ax.plot(hour, load_mw, color="#1a1a2e", linewidth=2.8, zorder=5, path_effects=curve_shadow + [pe.Normal()])

# Capacity tier lines with refined styling
tier_props = [
    (peak_threshold, "#D32F2F", "Peak Capacity"),
    (intermediate_threshold, "#E65100", "Intermediate Capacity"),
    (base_load, "#1565C0", "Base Capacity"),
]

for y_val, color, label in tier_props:
    ax.axhline(y=y_val, color=color, linestyle="--", linewidth=1.2, alpha=0.55, zorder=3)
    ax.text(
        hours * 0.62,
        y_val + 14,
        f"{label}  {y_val:,} MW",
        fontsize=13,
        color=color,
        fontweight="semibold",
        path_effects=[pe.withStroke(linewidth=3, foreground="#fafafaee")],
        zorder=6,
    )

# Region labels with path effects for legibility
region_labels = [
    (peak_end * 0.45, peak_threshold + 80, "PEAK\nLOAD", "#D32F2F"),
    ((peak_end + base_start) / 2, (peak_threshold + intermediate_threshold) / 2 + 10, "INTERMEDIATE\nLOAD", "#E65100"),
    ((base_start + hours) / 2 - 200, (intermediate_threshold + base_load) / 2 + 10, "BASE\nLOAD", "#1565C0"),
]

for x, y, text, color in region_labels:
    ax.text(
        x,
        y,
        text,
        fontsize=15,
        fontweight="bold",
        color=color,
        ha="center",
        va="center",
        alpha=0.7,
        linespacing=0.85,
        path_effects=[pe.withStroke(linewidth=4, foreground="#fafafa")],
        zorder=6,
    )

# Energy annotation with refined box
energy_text = f"Total Energy\n{total_energy_gwh:,.0f} GWh/year"
ax.annotate(
    energy_text,
    xy=(hours * 0.45, load_mw[int(hours * 0.45)]),
    xytext=(hours * 0.72, peak_threshold + 60),
    fontsize=15,
    fontweight="bold",
    color="#1a1a2e",
    ha="center",
    linespacing=1.3,
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#bbbbbb", "linewidth": 1.2, "alpha": 0.92},
    arrowprops={"arrowstyle": "->", "color": "#888888", "connectionstyle": "arc3,rad=0.2", "linewidth": 1.2},
    zorder=7,
)

# Peak demand callout
ax.annotate(
    f"Peak: {load_mw[0]:,.0f} MW",
    xy=(0, load_mw[0]),
    xytext=(hours * 0.12, load_mw[0] + 25),
    fontsize=13,
    fontweight="semibold",
    color="#D32F2F",
    arrowprops={"arrowstyle": "->", "color": "#D32F2F", "linewidth": 1.0},
    path_effects=[pe.withStroke(linewidth=3, foreground="#fafafa")],
    zorder=7,
)

# Style
ax.set_xlabel("Hours of Year (ranked by load)", fontsize=20, labelpad=10)
ax.set_ylabel("Power Demand (MW)", fontsize=20, labelpad=10)
ax.set_title("line-load-duration · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, hours)
ax.set_ylim(base_load - 30, peak_load + 80)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#cccccc")
ax.spines["bottom"].set_color("#cccccc")

# FuncFormatter for readable axis ticks
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x / 1000:.0f}k" if x >= 1000 else f"{x:.0f}"))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:,.0f}"))

ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color="#999999")
ax.tick_params(axis="both", colors="#555555")

# Custom legend with region patches
legend_elements = [
    Patch(facecolor="#D32F2F", alpha=0.4, label="Peak Load"),
    Patch(facecolor="#F57C00", alpha=0.4, label="Intermediate Load"),
    Patch(facecolor="#1976D2", alpha=0.4, label="Base Load"),
]
ax.legend(handles=legend_elements, fontsize=15, loc="upper right", framealpha=0.92, edgecolor="#cccccc", fancybox=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
