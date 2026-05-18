""" anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens (read from environment)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series is always #009E73
BRAND = "#009E73"  # violin fill
ACCENT = "#D55E00"  # swarm points

# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

conditions = ["Control", "Treatment A", "Treatment B", "Treatment C"]
n_per_group = 50

# Generate different distributions for each condition
data = {
    "Control": np.random.normal(450, 60, n_per_group),
    "Treatment A": np.random.normal(380, 45, n_per_group),
    "Treatment B": np.random.normal(420, 80, n_per_group),
    "Treatment C": np.concatenate(
        [np.random.normal(350, 30, n_per_group // 2), np.random.normal(450, 30, n_per_group // 2)]
    ),  # Bimodal
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Prepare data for violin plot
violin_data = [data[cond] for cond in conditions]
positions = np.arange(len(conditions))

# Draw violin plot with transparency
parts = ax.violinplot(violin_data, positions=positions, showmeans=False, showmedians=False, showextrema=False)

# Style violins with Okabe-Ito brand color and transparency
for pc in parts["bodies"]:
    pc.set_facecolor(BRAND)
    pc.set_edgecolor(INK_SOFT)
    pc.set_alpha(0.4)
    pc.set_linewidth(2)

# Overlay swarm points
for cond, pos in zip(conditions, positions, strict=True):
    y = data[cond]
    # Add jitter to spread points horizontally (swarm-like effect)
    # Calculate density-based jitter
    n_points = len(y)
    jitter = np.zeros(n_points)

    # Sort points and assign horizontal positions based on local density
    sorted_indices = np.argsort(y)
    sorted_y = y[sorted_indices]

    # Calculate jitter based on nearby point density
    bandwidth = (np.max(y) - np.min(y)) / 20
    for j, (idx, val) in enumerate(zip(sorted_indices, sorted_y, strict=True)):
        # Count nearby points
        nearby = np.sum(np.abs(sorted_y - val) < bandwidth)
        # Assign alternating jitter based on position within group
        local_idx = np.sum(np.abs(sorted_y[: j + 1] - val) < bandwidth) - 1
        max_jitter = 0.25 * (nearby / n_points) ** 0.5 + 0.05
        jitter[idx] = (local_idx % 2 * 2 - 1) * max_jitter * ((local_idx // 2 + 1) / (nearby / 2 + 1))

    x = np.full(n_points, pos) + jitter
    ax.scatter(
        x,
        y,
        s=110,
        alpha=0.8,
        color=ACCENT,
        edgecolor=INK_SOFT,
        linewidth=0.8,
        zorder=3,
        label="Individual observations" if pos == 0 else "",
    )

# Add median lines
for i, pos in enumerate(positions):
    median = np.median(violin_data[i])
    ax.hlines(median, pos - 0.2, pos + 0.2, color=INK, linewidth=3, zorder=4)

# Styling
ax.set_xticks(positions)
ax.set_xticklabels(conditions, fontsize=18, color=INK_SOFT)
ax.set_xlabel("Experimental Condition", fontsize=20, color=INK)
ax.set_ylabel("Reaction Time (ms)", fontsize=20, color=INK)
ax.set_title("violin-swarm · Python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Grid styling
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Legend
leg = ax.legend(loc="upper right", fontsize=16, title="Distribution", title_fontsize=16)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_alpha(0.9)
    plt.setp(leg.get_texts(), color=INK_SOFT)
    plt.setp(leg.get_title(), color=INK)

# Set y-axis limits with padding
all_values = np.concatenate(violin_data)
y_min, y_max = np.min(all_values), np.max(all_values)
y_padding = (y_max - y_min) * 0.1
ax.set_ylim(y_min - y_padding, y_max + y_padding)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
