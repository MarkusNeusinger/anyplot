""" anyplot.ai
horizon-basic: Horizon Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import os

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - 8 server metrics over 24 hours with more dramatic variation
np.random.seed(42)
hours = pd.date_range("2024-01-15", periods=24, freq="h")

series_names = ["CPU Load", "Memory", "Network I/O", "Disk I/O", "Requests/s", "Latency", "Queue Depth", "Threads"]
n_series = len(series_names)
n_points = len(hours)

# Generate realistic patterns with increased variation
data = {}
for i, name in enumerate(series_names):
    # Stronger daily cycle patterns
    base = np.sin(np.linspace(0, 2 * np.pi, n_points) + i * np.pi / 4) * 0.5
    noise = np.random.randn(n_points) * 0.2
    # More pronounced spikes
    spikes = np.zeros(n_points)
    if i % 2 == 0:
        spike_idx = np.random.choice(n_points, 4, replace=False)
        spikes[spike_idx] = np.random.uniform(0.7, 1.2, 4) * (1 if np.random.random() > 0.3 else -1)
    data[name] = np.clip(base + noise + spikes, -1.5, 1.5)

# Horizon chart parameters
n_bands = 3
band_height = 1.0

# Color bases with theme-adaptive styling
pos_base = mcolors.to_rgb("#009E73")  # imprint green — positive
neg_base = mcolors.to_rgb("#AE3030")  # imprint red — negative

# Create figure
fig, axes = plt.subplots(n_series, 1, figsize=(16, 9), sharex=True, facecolor=PAGE_BG)
fig.subplots_adjust(hspace=0.08, top=0.92, bottom=0.10, left=0.12, right=0.92)

# Plot each series as a horizon chart
for idx, (name, values) in enumerate(data.items()):
    ax = axes[idx]
    ax.set_facecolor(PAGE_BG)

    # Normalize values to fit in bands
    max_abs = max(abs(values.min()), abs(values.max()), 0.01)
    normalized = values / max_abs

    # Create band boundaries
    band_edges = np.linspace(0, 1, n_bands + 1)

    # Plot positive bands
    for band_idx in range(n_bands):
        lower = band_edges[band_idx]
        upper = band_edges[band_idx + 1]

        band_values = np.clip(normalized, 0, None)
        folded = np.clip(band_values - lower, 0, upper - lower)

        alpha = 0.35 + 0.25 * band_idx
        color = (*pos_base, alpha)

        ax.fill_between(hours, 0, folded, color=color, linewidth=0)

    # Plot negative bands
    for band_idx in range(n_bands):
        lower = band_edges[band_idx]
        upper = band_edges[band_idx + 1]

        band_values = np.clip(-normalized, 0, None)
        folded = np.clip(band_values - lower, 0, upper - lower)

        alpha = 0.35 + 0.25 * band_idx
        color = (*neg_base, alpha)

        ax.fill_between(hours, 0, folded, color=color, linewidth=0)

    # Style each subplot
    ax.set_ylim(0, 1 / n_bands + 0.05)
    ax.set_xlim(hours[0], hours[-1])

    # Add series label on the right with theme-aware color
    ax.text(1.01, 0.5, name, transform=ax.transAxes, fontsize=18, fontweight="bold", va="center", ha="left", color=INK)

    # Remove spines and ticks for clean look
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    if idx < n_series - 1:
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(axis="x", length=0, colors=INK_SOFT)
    else:
        ax.spines["bottom"].set_color(INK_SOFT)
        ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Configure x-axis on bottom subplot
axes[-1].set_xlabel("Time (Hour of Day)", fontsize=20, color=INK)

# Title
fig.suptitle("horizon-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", y=0.97, color=INK)

# Add legend for bands with theme-aware colors
legend_elements = [
    plt.Rectangle((0, 0), 1, 1, facecolor=(*pos_base, 0.35), label="Low +"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*pos_base, 0.60), label="Mid +"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*pos_base, 0.85), label="High +"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*neg_base, 0.35), label="Low −"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*neg_base, 0.60), label="Mid −"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*neg_base, 0.85), label="High −"),
]
leg = fig.legend(
    handles=legend_elements,
    loc="upper center",
    ncol=6,
    fontsize=16,
    frameon=True,
    bbox_to_anchor=(0.53, 0.94),
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
