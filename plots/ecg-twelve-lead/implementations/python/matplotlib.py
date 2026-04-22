""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


np.random.seed(42)

# Data - synthetic ECG using Gaussian-based P-QRS-T model
sampling_rate = 1000
duration = 2.5
t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

# Beat parameters: (amplitude, center_within_beat, width)
wave_params = [
    (0.15, 0.16, 0.025),  # P wave
    (-0.10, 0.24, 0.008),  # Q wave
    (1.00, 0.26, 0.012),  # R wave
    (-0.20, 0.28, 0.008),  # S wave
    (0.25, 0.40, 0.040),  # T wave
]

beat_period = 0.8  # ~75 bpm
n_beats = int(np.ceil(duration / beat_period)) + 1

# Build signal template by summing Gaussian peaks for each beat
signal_template = np.zeros_like(t)
for i in range(n_beats):
    t_shifted = t - i * beat_period
    for amp, center, width in wave_params:
        signal_template += amp * np.exp(-((t_shifted - center) ** 2) / (2 * width**2))

baseline = 0.02 * np.sin(2 * np.pi * 0.3 * t)
noise = np.random.normal(0, 0.01, len(t))

# Lead-specific scaling (scale_factor, invert_flag)
lead_config = {
    "I": (0.8, False),
    "II": (1.0, False),
    "III": (0.6, False),
    "aVR": (0.7, True),
    "aVL": (0.4, False),
    "aVF": (0.8, False),
    "V1": (0.5, True),
    "V2": (0.9, False),
    "V3": (1.1, False),
    "V4": (1.2, False),
    "V5": (1.0, False),
    "V6": (0.8, False),
}

leads = {}
for name, (scale, invert) in lead_config.items():
    sig = signal_template * scale + baseline + noise * scale
    if invert:
        sig = -sig
    sig += np.random.normal(0, 0.005, len(t))
    leads[name] = sig

# Rhythm strip signal (10 seconds of Lead II)
t_long = np.linspace(0, 10.0, int(sampling_rate * 10.0), endpoint=False)
n_beats_long = int(np.ceil(10.0 / beat_period)) + 1
signal_long = np.zeros_like(t_long)
for i in range(n_beats_long):
    t_shifted = t_long - i * beat_period
    for amp, center, width in wave_params:
        signal_long += amp * np.exp(-((t_shifted - center) ** 2) / (2 * width**2))
signal_long += 0.02 * np.sin(2 * np.pi * 0.3 * t_long) + np.random.normal(0, 0.01, len(t_long))

# Clinical 3x4 grid layout
grid_layout = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]

# Plot
ecg_bg = "#FFF5EE"
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(4, 4, hspace=0.08, wspace=0.08, left=0.04, right=0.98, top=0.91, bottom=0.04)


def setup_ecg_grid(ax, x_min, x_max, y_min=-1.5, y_max=1.8):
    """Configure ECG paper grid using matplotlib's native tick/grid system."""
    ax.set_facecolor(ecg_bg)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # Major grid: bold lines at 5mm intervals (0.2s horizontal, 0.5mV vertical)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))

    # Minor grid: fine lines at 1mm intervals (0.04s horizontal, 0.1mV vertical)
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.04))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))

    ax.grid(which="minor", color="#F5C4B8", linewidth=0.3, alpha=0.6)
    ax.grid(which="major", color="#E8A090", linewidth=0.7, alpha=0.7)

    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(axis="both", length=0)

    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
        spine.set_color("#CCBBBB")


for row_idx, row_leads in enumerate(grid_layout):
    for col_idx, lead_name in enumerate(row_leads):
        ax = fig.add_subplot(gs[row_idx, col_idx])
        setup_ecg_grid(ax, 0, duration)

        ax.plot(t, leads[lead_name], color="#1a1a1a", linewidth=1.2)

        ax.text(
            0.03,
            0.93,
            lead_name,
            transform=ax.transAxes,
            fontsize=20,
            fontweight="bold",
            color="#222222",
            va="top",
            bbox={"boxstyle": "square,pad=0.15", "facecolor": ecg_bg, "edgecolor": "none", "alpha": 0.9},
        )

# Rhythm strip (Lead II, full width)
ax_rhythm = fig.add_subplot(gs[3, :])
setup_ecg_grid(ax_rhythm, 0, 10.0)

ax_rhythm.plot(t_long, signal_long, color="#1a1a1a", linewidth=1.2)

ax_rhythm.text(
    0.003,
    0.93,
    "II (rhythm)",
    transform=ax_rhythm.transAxes,
    fontsize=20,
    fontweight="bold",
    color="#222222",
    va="top",
    bbox={"boxstyle": "square,pad=0.15", "facecolor": ecg_bg, "edgecolor": "none", "alpha": 0.9},
)

# Calibration marker: 1mV pulse
ax_rhythm.plot([0, 0, 0.2, 0.2], [-1.2, -0.2, -0.2, -1.2], color="#1a1a1a", linewidth=1.8)
ax_rhythm.text(0.1, -0.0, "1 mV", fontsize=16, ha="center", color="#444444", fontweight="medium")

# Heart rate annotation on rhythm strip
ax_rhythm.text(
    0.997,
    0.93,
    "HR: ~75 bpm",
    transform=ax_rhythm.transAxes,
    fontsize=16,
    ha="right",
    va="top",
    color="#666666",
    fontstyle="italic",
)

# Title and metadata
fig.suptitle(
    "ecg-twelve-lead · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    x=0.04,
    y=0.97,
    ha="left",
    color="#333333",
)
fig.text(0.98, 0.97, "25 mm/s  ·  10 mm/mV  ·  Normal Sinus Rhythm", fontsize=16, ha="right", va="top", color="#888888")

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
