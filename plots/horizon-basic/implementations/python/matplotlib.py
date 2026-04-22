""" pyplots.ai
horizon-basic: Horizon Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Simulating 8 server metrics over 24 hours (hourly readings)
np.random.seed(42)
hours = pd.date_range("2024-01-15", periods=24, freq="h")

# Create realistic server metrics (normalized deviation from baseline)
series_names = ["CPU Load", "Memory", "Network I/O", "Disk I/O", "Requests/s", "Latency", "Queue Depth", "Threads"]
n_series = len(series_names)
n_points = len(hours)

# Generate realistic patterns with different behaviors
data = {}
for i, name in enumerate(series_names):
    # Base pattern with daily cycle
    base = np.sin(np.linspace(0, 2 * np.pi, n_points) + i * np.pi / 4) * 0.3
    # Add some noise and spikes
    noise = np.random.randn(n_points) * 0.15
    # Occasional spikes for some metrics
    spikes = np.zeros(n_points)
    if i % 2 == 0:
        spike_idx = np.random.choice(n_points, 3, replace=False)
        spikes[spike_idx] = np.random.uniform(0.5, 1.0, 3) * (1 if np.random.random() > 0.3 else -1)
    data[name] = base + noise + spikes

# Horizon chart parameters
n_bands = 3  # Number of bands for positive and negative values
band_height = 1.0  # Height of each series panel

# Define colors: Blue for positive (Python Blue), Red/Orange for negative
pos_base = mcolors.to_rgb("#306998")  # Python Blue
neg_base = mcolors.to_rgb("#E74C3C")  # Red for negative

# Create figure
fig, axes = plt.subplots(n_series, 1, figsize=(16, 9), sharex=True)
fig.subplots_adjust(hspace=0.1, top=0.92, bottom=0.08, left=0.12, right=0.95)

# Plot each series as a horizon chart
for idx, (name, values) in enumerate(data.items()):
    ax = axes[idx]

    # Normalize values to fit in bands
    max_abs = max(abs(values.min()), abs(values.max()), 0.01)
    normalized = values / max_abs  # Now in range [-1, 1]

    # Create band boundaries
    band_edges = np.linspace(0, 1, n_bands + 1)

    # Plot positive bands (folded and overlaid)
    for band_idx in range(n_bands):
        lower = band_edges[band_idx]
        upper = band_edges[band_idx + 1]

        # Get values that fall in this band (when positive)
        band_values = np.clip(normalized, 0, None)  # Only positive
        # Fold: values in band [lower, upper] map to [0, 1/n_bands]
        folded = np.clip(band_values - lower, 0, upper - lower)

        # Color intensity increases with band number
        alpha = 0.4 + 0.2 * band_idx
        color = (*pos_base, alpha)

        ax.fill_between(hours, 0, folded, color=color, linewidth=0)

    # Plot negative bands (folded and overlaid, mirrored above baseline)
    for band_idx in range(n_bands):
        lower = band_edges[band_idx]
        upper = band_edges[band_idx + 1]

        # Get values that fall in this band (when negative)
        band_values = np.clip(-normalized, 0, None)  # Flip negative to positive
        # Fold: values in band [lower, upper] map to [0, 1/n_bands]
        folded = np.clip(band_values - lower, 0, upper - lower)

        # Color intensity increases with band number
        alpha = 0.4 + 0.2 * band_idx
        color = (*neg_base, alpha)

        ax.fill_between(hours, 0, folded, color=color, linewidth=0)

    # Style each subplot
    ax.set_ylim(0, 1 / n_bands + 0.05)
    ax.set_xlim(hours[0], hours[-1])

    # Add series label on the right
    ax.text(1.01, 0.5, name, transform=ax.transAxes, fontsize=14, fontweight="bold", va="center", ha="left")

    # Remove spines and ticks for cleaner look
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    if idx < n_series - 1:
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(axis="x", length=0)
    else:
        ax.spines["bottom"].set_color("#666666")
        ax.tick_params(axis="x", labelsize=14)

# Configure x-axis on bottom subplot
axes[-1].set_xlabel("Time (Hour of Day)", fontsize=18)

# Title
fig.suptitle("horizon-basic · matplotlib · pyplots.ai", fontsize=22, fontweight="bold", y=0.97)

# Add legend for bands
legend_elements = [
    plt.Rectangle((0, 0), 1, 1, facecolor=(*pos_base, 0.4), label="Low +"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*pos_base, 0.6), label="Mid +"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*pos_base, 0.8), label="High +"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*neg_base, 0.4), label="Low −"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*neg_base, 0.6), label="Mid −"),
    plt.Rectangle((0, 0), 1, 1, facecolor=(*neg_base, 0.8), label="High −"),
]
fig.legend(handles=legend_elements, loc="upper center", ncol=6, fontsize=12, frameon=False, bbox_to_anchor=(0.53, 0.94))

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
