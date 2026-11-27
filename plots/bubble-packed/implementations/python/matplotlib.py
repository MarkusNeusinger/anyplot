"""anyplot.ai
bubble-packed: Basic Packed Bubble Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-29
"""

import os

import matplotlib.collections as mcoll
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — 8 hues, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MAX_RADIUS = 2.0  # radius of the largest circle in layout units; area stays proportional to value

# Columns: set these to your table's column names
WARD = "Ward"  # role: label
ADMISSIONS = "Admissions per month"  # role: value
SPECIALTY = "Specialty"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("wards.csv")
df = pd.DataFrame(
    {
        WARD: [
            "General Medicine",
            "Cardiology",
            "Oncology",
            "Neurology",
            "Respiratory",
            "General Surgery",
            "Orthopaedics",
            "Urology",
            "ENT",
            "Emergency",
            "Intensive Care",
            "High Dependency",
            "Maternity",
            "Paediatrics",
            "Gynaecology",
            "Neonatal",
        ],
        ADMISSIONS: [920, 610, 450, 330, 380, 780, 560, 240, 150, 840, 230, 130, 690, 470, 260, 190],
        SPECIALTY: ["Medical"] * 5 + ["Surgical"] * 4 + ["Emergency & critical care"] * 3 + ["Women & children"] * 4,
    }
)

# Plot: reads only df and the constants above
groups = list(dict.fromkeys(df[SPECIALTY]))
group_colors = {g: IMPRINT_PALETTE[i] for i, g in enumerate(groups)}

# Largest first gives the simulation a stable core; radius from sqrt so area follows value
df = df.sort_values(ADMISSIONS, ascending=False, kind="stable").reset_index(drop=True)
n = len(df)
radii = MAX_RADIUS * np.sqrt(df[ADMISSIONS].to_numpy(dtype=float) / df[ADMISSIONS].max())
group_ids = np.array([groups.index(g) for g in df[SPECIALTY]])

# Initial positions on a spiral, then a deterministic force simulation with group clustering
angles = np.linspace(0, 4 * np.pi, n)
spiral_r = np.linspace(0, 3, n)
positions = np.column_stack([spiral_r * np.cos(angles), spiral_r * np.sin(angles)])

for iteration in range(1500):
    progress = iteration / 1500
    pull_strength = 0.05 * (1 - progress * 0.8)
    group_pull = 0.04 * (1 - progress * 0.5)

    group_centers = {gid: positions[group_ids == gid].mean(axis=0) for gid in range(len(groups))}

    for i in range(n):
        dist = np.linalg.norm(positions[i])
        if dist > 0.01:
            positions[i] -= pull_strength * (radii[i] / radii[0]) ** 2 * positions[i] / dist
        to_group = group_centers[group_ids[i]] - positions[i]
        gd = np.linalg.norm(to_group)
        if gd > 0.01:
            positions[i] += group_pull * to_group / gd

    for i in range(n):
        for j in range(i + 1, n):
            delta = positions[j] - positions[i]
            dist = np.linalg.norm(delta)
            gap = 0.04 if group_ids[i] == group_ids[j] else 0.12
            min_dist = radii[i] + radii[j] + gap
            if 0.001 < dist < min_dist:
                shift = (min_dist - dist) / 2 * delta / dist
                positions[i] -= shift
                positions[j] += shift

# Center the layout on its bounding box
lo = (positions - radii[:, None]).min(axis=0)
hi = (positions + radii[:, None]).max(axis=0)
positions -= (lo + hi) / 2
half_extent = (hi - lo).max() / 2 + 1.0

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_xlim(-half_extent, half_extent)
ax.set_ylim(-half_extent, half_extent)
ax.set_aspect("equal")
ax.axis("off")
fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.10)

collection = mcoll.PatchCollection(
    [mpatches.Circle(tuple(positions[i]), radii[i]) for i in range(n)],
    facecolors=[group_colors[g] for g in df[SPECIALTY]],
    edgecolors=PAGE_BG,
    linewidths=2.0,
    alpha=0.92,
    zorder=2,
)
ax.add_collection(collection)

# Points per layout unit, to decide which circles can hold their label
fig.canvas.draw()
pt_per_unit = ax.get_window_extent().width / fig.dpi * 72 / (2 * half_extent)

external = []
for i in range(n):
    name = df[WARD][i]
    words = name.split(" ")
    display = "\n".join(words)
    fontsize = 9 if radii[i] < 1.4 else 11
    widest = max(len(w) for w in words) * 0.62 * fontsize
    needed = max(widest, 0.9 * fontsize * len(words)) + 4
    if needed < 2.0 * radii[i] * pt_per_unit:
        fill = group_colors[df[SPECIALTY][i]]
        rgb = [int(fill[k : k + 2], 16) / 255 for k in (1, 3, 5)]
        luminance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        text_color = "#1A1A17" if luminance > 0.35 else "#F0EFE8"
        stroke = pe.withStroke(linewidth=1.0, foreground=(0, 0, 0, 0.15) if luminance > 0.35 else (1, 1, 1, 0.15))
        ax.text(
            positions[i, 0],
            positions[i, 1] + radii[i] * 0.16,
            display,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color=text_color,
            path_effects=[stroke],
            zorder=3,
        )
        ax.text(
            positions[i, 0],
            positions[i, 1] - radii[i] * (0.30 + 0.20 * (len(words) - 1)),
            f"{df[ADMISSIONS][i]:,}",
            ha="center",
            va="center",
            fontsize=fontsize - 1,
            color=text_color,
            path_effects=[stroke],
            zorder=3,
        )
    else:
        external.append(i)

# External labels with leader lines: nearest free spot whose text box clears every circle and label
placed = []
for i in external:
    cx, cy = positions[i]
    half_w = max(len(w) for w in df[WARD][i].split(" ")) * 0.62 * 9 / pt_per_unit / 2 + 0.1
    half_h = 11 / pt_per_unit + 0.1
    best_angle, best_pos, best_score = 0.0, None, None
    for extra in np.arange(0.5, 9.0, 0.25):
        for angle in np.linspace(0, 2 * np.pi, 36, endpoint=False):
            lx, ly = cx + (radii[i] + extra) * np.cos(angle), cy + (radii[i] + extra) * np.sin(angle)
            if abs(lx) + half_w > half_extent or abs(ly) + half_h > half_extent:
                continue
            nearest = np.clip(positions - [lx, ly], [-half_w, -half_h], [half_w, half_h]) + [lx, ly]
            if np.any(np.hypot(*(nearest - positions).T) < radii + 0.05):
                continue
            if any(abs(lx - px) < half_w + qw and abs(ly - py) < half_h + qh for px, py, qw, qh in placed):
                continue
            # prefer a leader line that crosses no other circle, then the shortest one
            ray = np.array([lx - cx, ly - cy])
            t = np.clip((positions - [cx, cy]) @ ray / (ray @ ray), 0, 1)
            gap = np.hypot(*(positions - [cx, cy] - t[:, None] * ray).T) - radii
            crossed = int(np.sum((gap < 0.05) & (np.arange(n) != i)))
            if best_score is None or (crossed, extra) < best_score:
                best_angle, best_pos, best_score = angle, (lx, ly), (crossed, extra)
    lx, ly = best_pos if best_pos else (cx, cy)
    placed.append((lx, ly, half_w, half_h))
    ax.annotate(
        f"{df[WARD][i]}\n{df[ADMISSIONS][i]:,}",
        xy=(cx + radii[i] * np.cos(best_angle), cy + radii[i] * np.sin(best_angle)),
        xytext=(lx, ly),
        fontsize=9,
        fontweight="bold",
        color=INK_SOFT,
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "-", "color": INK_MUTED, "lw": 1.2, "shrinkA": 4, "shrinkB": 0},
        zorder=4,
    )

# Title
title = "bubble-packed · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
fig.suptitle(title, fontsize=title_fontsize, fontweight="medium", color=INK, y=0.975)

# Legend for groups, centered under the cluster
legend_handles = [
    mpatches.Patch(facecolor=color, edgecolor=PAGE_BG, linewidth=1.5, label=group)
    for group, color in group_colors.items()
]
leg = fig.legend(
    handles=legend_handles,
    title=SPECIALTY,
    loc="lower center",
    ncol=len(groups),
    fontsize=9,
    title_fontsize=9,
    fancybox=False,
    borderpad=0.7,
    handlelength=1.5,
    handleheight=1.1,
    columnspacing=1.6,
    bbox_to_anchor=(0.5, 0.012),
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
