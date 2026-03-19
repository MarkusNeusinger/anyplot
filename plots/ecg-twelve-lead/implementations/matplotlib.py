""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
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
gs = fig.add_gridspec(4, 4, hspace=0.05, wspace=0.05, left=0.04, right=0.98, top=0.92, bottom=0.04)

fine_grid_x = np.arange(0, duration + 0.04, 0.04)
fine_grid_y = np.arange(-2, 2.1, 0.1)
bold_grid_x = np.arange(0, duration + 0.2, 0.2)
bold_grid_y = np.arange(-2, 2.1, 0.5)

for row_idx, row_leads in enumerate(grid_layout):
    for col_idx, lead_name in enumerate(row_leads):
        ax = fig.add_subplot(gs[row_idx, col_idx])
        ax.set_facecolor(ecg_bg)

        # ECG paper grid
        for xv in fine_grid_x:
            ax.axvline(x=xv, color="#F5C4B8", linewidth=0.3, alpha=0.6)
        for yv in fine_grid_y:
            ax.axhline(y=yv, color="#F5C4B8", linewidth=0.3, alpha=0.6)
        for xv in bold_grid_x:
            ax.axvline(x=xv, color="#E8A090", linewidth=0.7, alpha=0.7)
        for yv in bold_grid_y:
            ax.axhline(y=yv, color="#E8A090", linewidth=0.7, alpha=0.7)

        ax.plot(t, leads[lead_name], color="#1a1a1a", linewidth=1.2)

        ax.text(
            0.03,
            0.92,
            lead_name,
            transform=ax.transAxes,
            fontsize=14,
            fontweight="bold",
            color="#333333",
            va="top",
            bbox={"boxstyle": "square,pad=0.15", "facecolor": ecg_bg, "edgecolor": "none"},
        )

        ax.set_xlim(0, duration)
        ax.set_ylim(-1.5, 1.8)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_color("#CCBBBB")

# Rhythm strip (Lead II, full width)
ax_rhythm = fig.add_subplot(gs[3, :])
ax_rhythm.set_facecolor(ecg_bg)

fine_grid_x_long = np.arange(0, 10.0 + 0.04, 0.04)
bold_grid_x_long = np.arange(0, 10.0 + 0.2, 0.2)

for xv in fine_grid_x_long:
    ax_rhythm.axvline(x=xv, color="#F5C4B8", linewidth=0.3, alpha=0.6)
for yv in fine_grid_y:
    ax_rhythm.axhline(y=yv, color="#F5C4B8", linewidth=0.3, alpha=0.6)
for xv in bold_grid_x_long:
    ax_rhythm.axvline(x=xv, color="#E8A090", linewidth=0.7, alpha=0.7)
for yv in bold_grid_y:
    ax_rhythm.axhline(y=yv, color="#E8A090", linewidth=0.7, alpha=0.7)

ax_rhythm.plot(t_long, signal_long, color="#1a1a1a", linewidth=1.2)

ax_rhythm.text(
    0.003,
    0.92,
    "II (rhythm)",
    transform=ax_rhythm.transAxes,
    fontsize=14,
    fontweight="bold",
    color="#333333",
    va="top",
    bbox={"boxstyle": "square,pad=0.15", "facecolor": ecg_bg, "edgecolor": "none"},
)

ax_rhythm.set_xlim(0, 10.0)
ax_rhythm.set_ylim(-1.5, 1.8)
ax_rhythm.set_xticks([])
ax_rhythm.set_yticks([])
for spine in ax_rhythm.spines.values():
    spine.set_linewidth(0.5)
    spine.set_color("#CCBBBB")

# Calibration marker: 1mV pulse
ax_rhythm.plot([0, 0, 0.2, 0.2], [-1.2, -0.2, -0.2, -1.2], color="#1a1a1a", linewidth=1.5)
ax_rhythm.text(0.1, -0.05, "1 mV", fontsize=9, ha="center", color="#555555")

# Style
fig.suptitle("ecg-twelve-lead · matplotlib · pyplots.ai", fontsize=20, fontweight="medium", y=0.97, color="#333333")
fig.text(0.98, 0.97, "25 mm/s  ·  10 mm/mV  ·  Normal Sinus Rhythm", fontsize=11, ha="right", va="top", color="#888888")

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
