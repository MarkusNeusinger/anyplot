""" pyplots.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-02-18
"""

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# ── Seaborn configuration ──
sns.set_style("white")
sns.set_context("poster", font_scale=0.85, rc={"axes.titlesize": 26, "axes.titleweight": "bold", "legend.fontsize": 13})

np.random.seed(42)

# ── Configuration ──
sectors = ["AI & ML", "Cloud & Infra", "Sustainability", "Biotech"]
rings = ["Adopt", "Trial", "Assess", "Hold"]

ring_radii = {"Adopt": 1.0, "Trial": 2.0, "Assess": 3.0, "Hold": 4.0}
ring_importance = {"Adopt": 4, "Trial": 3, "Assess": 2, "Hold": 1}

sector_base = sns.color_palette(["#306998", "#E8793A", "#4CAF50", "#9C27B0"])
sector_palette = dict(zip(sectors, sector_base, strict=True))
sector_markers = {"AI & ML": "o", "Cloud & Infra": "s", "Sustainability": "D", "Biotech": "^"}

total_angle_deg = 270
sector_width_deg = total_angle_deg / len(sectors)
start_angle_deg = 135

# Ring backgrounds via seaborn light_palette — distinctive color generation
ring_bg_colors = [
    sns.light_palette("#4CAF50", n_colors=6)[1],
    sns.light_palette("#FF9800", n_colors=6)[1],
    sns.light_palette("#FDD835", n_colors=6)[1],
    sns.light_palette("#E53935", n_colors=6)[1],
]
# Near-term → future gradient via seaborn blend_palette
ring_accent = sns.blend_palette(["#4CAF50", "#FDD835", "#E53935"], n_colors=5)
ring_boundaries = [0.5, 1.5, 2.5, 3.5, 4.5]

# ── Innovation data ──
innovations = [
    ("LLM Agents", "Adopt", "AI & ML"),
    ("RAG Pipelines", "Adopt", "AI & ML"),
    ("Multimodal Models", "Trial", "AI & ML"),
    ("Federated Learning", "Assess", "AI & ML"),
    ("Neuromorphic Chips", "Hold", "AI & ML"),
    ("AI Code Review", "Trial", "AI & ML"),
    ("Synthetic Data Gen", "Assess", "AI & ML"),
    ("Platform Eng.", "Adopt", "Cloud & Infra"),
    ("eBPF Observability", "Trial", "Cloud & Infra"),
    ("Wasm Edge", "Assess", "Cloud & Infra"),
    ("Confid. Compute", "Trial", "Cloud & Infra"),
    ("Serverless GPUs", "Assess", "Cloud & Infra"),
    ("Quantum Network", "Hold", "Cloud & Infra"),
    ("RISC-V Servers", "Hold", "Cloud & Infra"),
    ("Carbon Accounting", "Adopt", "Sustainability"),
    ("Green Software", "Trial", "Sustainability"),
    ("Digital Twins", "Assess", "Sustainability"),
    ("Circular Supply", "Trial", "Sustainability"),
    ("Ocean Carbon Cap.", "Hold", "Sustainability"),
    ("Energy Harvest IoT", "Assess", "Sustainability"),
    ("mRNA Therapeutics", "Adopt", "Biotech"),
    ("CRISPR Diagnostics", "Trial", "Biotech"),
    ("Organ-on-Chip", "Assess", "Biotech"),
    ("Biocomputing", "Hold", "Biotech"),
    ("Precision Nutrition", "Trial", "Biotech"),
    ("Longevity Biomarkers", "Assess", "Biotech"),
    ("Phage Therapy", "Hold", "Biotech"),
]

# ── Build DataFrame with computed polar positions ──
records = []
for name, ring, sector in innovations:
    sector_idx = sectors.index(sector)
    same_group = [(n, r, s) for n, r, s in innovations if s == sector and r == ring]
    item_idx = same_group.index((name, ring, sector))
    n_in_group = len(same_group)

    sector_start = np.deg2rad(start_angle_deg - sector_idx * sector_width_deg)
    sector_end = np.deg2rad(start_angle_deg - (sector_idx + 1) * sector_width_deg)
    margin = 0.10 * (sector_start - sector_end)
    usable_start = sector_start - margin
    usable_end = sector_end + margin

    if n_in_group == 1:
        angle = (usable_start + usable_end) / 2
    elif n_in_group == 2:
        spread = 0.80
        mid = (usable_start + usable_end) / 2
        half = spread * (usable_start - usable_end) / 2
        angle = mid + half if item_idx == 0 else mid - half
    else:
        angle = usable_start + (usable_end - usable_start) * item_idx / (n_in_group - 1)

    if n_in_group == 2:
        radial_jitter = 0.24 if item_idx == 0 else -0.24
    else:
        radial_jitter = np.random.uniform(-0.22, 0.22)
    radius = ring_radii[ring] + radial_jitter

    records.append(
        {
            "name": name,
            "ring": ring,
            "sector": sector,
            "angle": angle,
            "radius": radius,
            "importance": ring_importance[ring],
        }
    )

df = pd.DataFrame(records)

# ── Create polar figure ──
fig = plt.figure(figsize=(14, 14))
ax = fig.add_subplot(111, projection="polar")
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

# ── Ring background fills ──
theta_fill = np.linspace(0, 2 * np.pi, 200)
for i in range(len(rings)):
    ax.fill_between(
        theta_fill, ring_boundaries[i], ring_boundaries[i + 1], color=ring_bg_colors[i], alpha=0.35, zorder=0
    )

# Ring boundary lines with gradient coloring (green→yellow→red)
for i, rb in enumerate(ring_boundaries):
    lw = 1.4 if i == 1 else 0.8
    ax.plot(
        theta_fill,
        np.full_like(theta_fill, rb),
        color=sns.desaturate(ring_accent[i], 0.5),
        linewidth=lw,
        alpha=0.5,
        zorder=1,
    )

# Sector divider lines
for i in range(len(sectors) + 1):
    angle = np.deg2rad(start_angle_deg - i * sector_width_deg)
    ax.plot([angle, angle], [0.5, 4.5], color="gray", linewidth=1.0, alpha=0.5, zorder=1)

# ── Plot innovations using seaborn scatterplot with multi-encoding ──
size_map = {1: 150, 2: 250, 3: 340, 4: 440}
sns.scatterplot(
    data=df,
    x="angle",
    y="radius",
    hue="sector",
    style="sector",
    size="importance",
    sizes=size_map,
    markers=sector_markers,
    palette=sector_palette,
    edgecolor="white",
    linewidth=1.5,
    alpha=0.9,
    legend=False,
    ax=ax,
    zorder=5,
)

# ── Subtle halo per sector (seaborn scatter layer) ──
for sector_name in sectors:
    sector_df = df[df["sector"] == sector_name]
    sns.scatterplot(
        data=sector_df,
        x="angle",
        y="radius",
        color=sector_palette[sector_name],
        s=600,
        alpha=0.08,
        legend=False,
        ax=ax,
        zorder=3,
    )

# ── Axes setup ──
ax.set_ylim(0, 6.0)
ax.set_yticks([])
ax.set_xticks([])
ax.set_xlabel("")
ax.set_ylabel("")
ax.grid(False)
ax.spines["polar"].set_visible(False)

fig.canvas.draw()

# ── Innovation labels with inline collision detection ──
placed_boxes = []
DPI = fig.dpi
PT = DPI / 72.0
FONT_SIZE = 13
CHAR_W = FONT_SIZE * 0.62 * PT
CHAR_H = FONT_SIZE * 1.3 * PT
BOX_PAD = 4 * PT

df_sorted = df.sort_values("radius", ascending=False).reset_index(drop=True)

for _, row in df_sorted.iterrows():
    angle, radius, name = row["angle"], row["radius"], row["name"]
    angle_deg = np.rad2deg(angle) % 360
    dx, dy = ax.transData.transform((angle, radius))

    if 30 < angle_deg < 150:
        ha, base_x = "left", 10
    elif 210 < angle_deg < 330:
        ha, base_x = "right", -10
    else:
        ha, base_x = "center", 0

    best_pos, best_score = (12, base_x), float("inf")
    for y in [12, -12, 18, -18, 25, -25, 33, -33]:
        for dx_adj in [0, 8, -8, 15, -15]:
            x_off = base_x + dx_adj
            va_c = "bottom" if y > 0 else "top"
            cx = dx + x_off * PT
            cy = dy + y * PT
            w = len(name) * CHAR_W + BOX_PAD * 2
            h = CHAR_H + BOX_PAD * 2
            x0 = cx if ha == "left" else (cx - w if ha == "right" else cx - w / 2)
            y0 = cy if va_c == "bottom" else cy - h
            m = 2 * PT
            score = sum(
                1
                for bx in placed_boxes
                if not (x0 + w + m < bx[0] or bx[0] + bx[2] + m < x0 or y0 + h + m < bx[1] or bx[1] + bx[3] + m < y0)
            )
            if score < best_score:
                best_score = score
                best_pos = (y, x_off)
                if score == 0:
                    break
        if best_score == 0:
            break

    y_off, x_off = best_pos
    va = "bottom" if y_off > 0 else "top"

    ax.annotate(
        name,
        xy=(angle, radius),
        xytext=(x_off, y_off),
        textcoords="offset points",
        fontsize=FONT_SIZE,
        color="#2C2C2C",
        fontweight="medium",
        ha=ha,
        va=va,
        bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "none", "alpha": 0.88},
        arrowprops={"arrowstyle": "-", "color": "#bbbbbb", "linewidth": 0.5},
        zorder=6,
    )
    cx_f = dx + x_off * PT
    cy_f = dy + y_off * PT
    w_f = len(name) * CHAR_W + BOX_PAD * 2
    h_f = CHAR_H + BOX_PAD * 2
    x0_f = cx_f if ha == "left" else (cx_f - w_f if ha == "right" else cx_f - w_f / 2)
    y0_f = cy_f if va == "bottom" else cy_f - h_f
    placed_boxes.append((x0_f, y0_f, w_f, h_f))

# ── Sector header labels ──
for i, sector_name in enumerate(sectors):
    mid_angle = np.deg2rad(start_angle_deg - (i + 0.5) * sector_width_deg)
    ax.text(
        mid_angle,
        5.4,
        sector_name,
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color=sector_palette[sector_name],
        zorder=7,
    )

# ── Ring labels ──
label_angle = np.deg2rad(start_angle_deg - total_angle_deg - 8)
for ring_name, ring_r in zip(rings, [1.0, 2.0, 3.0, 4.0], strict=True):
    ax.text(
        label_angle,
        ring_r,
        ring_name,
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="#555555",
        bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.88},
        zorder=7,
    )

# ── Directional storytelling cues ──
dir_angle = np.deg2rad(start_angle_deg - total_angle_deg - 22)
ax.text(
    dir_angle,
    0.7,
    "◂ Ready",
    fontsize=10,
    color=sns.desaturate("#4CAF50", 0.6),
    fontweight="bold",
    ha="center",
    va="center",
    zorder=7,
)
ax.text(
    dir_angle,
    4.7,
    "Emerging ▸",
    fontsize=10,
    color=sns.desaturate("#E53935", 0.6),
    fontweight="bold",
    ha="center",
    va="center",
    zorder=7,
)

# ── Title ──
ax.set_title(
    "radar-innovation-timeline · seaborn · pyplots.ai", fontsize=26, fontweight="bold", pad=35, color="#1a1a1a"
)

# ── Combined legend ──
sector_handles = [
    mlines.Line2D(
        [],
        [],
        marker=sector_markers[s],
        color="w",
        markerfacecolor=sector_palette[s],
        markeredgecolor="white",
        markersize=13,
        label=s,
    )
    for s in sectors
]

spacer = mlines.Line2D([], [], color="none", label=" ")

ring_sizes_legend = {"Adopt (Now)": 440, "Trial (Next)": 340, "Assess (Explore)": 250, "Hold (Watch)": 150}
ring_handles = [
    mlines.Line2D(
        [],
        [],
        marker="o",
        color="w",
        markerfacecolor="#999999",
        markeredgecolor="white",
        markersize=np.sqrt(sz) / 3,
        label=label,
    )
    for label, sz in ring_sizes_legend.items()
]

all_handles = sector_handles + [spacer] + ring_handles
legend = ax.legend(
    handles=all_handles,
    loc="lower right",
    bbox_to_anchor=(1.22, 0.02),
    fontsize=13,
    title="Sectors & Time Horizons",
    title_fontsize=15,
    framealpha=0.95,
    edgecolor="lightgray",
    fancybox=True,
    handletextpad=1.0,
    borderpad=1.0,
)
legend._legend_box.sep = 8

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
