""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns


# Style - use seaborn theme and context for base styling
sns.set_theme(style="whitegrid", rc={"axes.facecolor": "#FFF5F0", "figure.facecolor": "#FFF5F0"})
sns.set_context("talk", font_scale=1.1)

# Data - synthetic ECG waveform generation using Gaussian model
np.random.seed(42)
sampling_rate = 1000
duration = 2.5
time = np.linspace(0, duration, int(sampling_rate * duration))
heart_rate = 72
rr_interval = 60.0 / heart_rate

wave_centers = np.array([0.10, 0.22, 0.25, 0.28, 0.42])
wave_widths = np.array([0.012, 0.005, 0.008, 0.006, 0.025])
wave_keys = ["p", "q", "r", "s", "t"]

lead_configs = {
    "I": {"p": 0.15, "q": -0.08, "r": 0.9, "s": -0.15, "t": 0.25},
    "II": {"p": 0.20, "q": -0.10, "r": 1.2, "s": -0.20, "t": 0.35},
    "III": {"p": 0.08, "q": -0.05, "r": 0.6, "s": -0.10, "t": 0.15},
    "aVR": {"p": -0.15, "q": 0.05, "r": -0.5, "s": 0.10, "t": -0.25},
    "aVL": {"p": 0.05, "q": -0.06, "r": 0.5, "s": -0.08, "t": 0.12},
    "aVF": {"p": 0.12, "q": -0.08, "r": 0.8, "s": -0.15, "t": 0.22},
    "V1": {"p": 0.10, "q": -0.04, "r": 0.3, "s": -0.8, "t": -0.15},
    "V2": {"p": 0.12, "q": -0.05, "r": 0.5, "s": -0.6, "t": 0.20},
    "V3": {"p": 0.12, "q": -0.06, "r": 0.8, "s": -0.4, "t": 0.30},
    "V4": {"p": 0.14, "q": -0.08, "r": 1.1, "s": -0.25, "t": 0.35},
    "V5": {"p": 0.14, "q": -0.08, "r": 1.0, "s": -0.18, "t": 0.30},
    "V6": {"p": 0.12, "q": -0.06, "r": 0.8, "s": -0.12, "t": 0.25},
}

beat_starts = np.arange(0, time[-1] + rr_interval, rr_interval)
leads_data = {}
for lead_name, gains in lead_configs.items():
    signal = np.zeros_like(time)
    gain_values = np.array([gains[k] for k in wave_keys])
    for beat_start in beat_starts:
        dt = time - beat_start
        for i in range(5):
            signal += gain_values[i] * np.exp(-((dt - wave_centers[i]) ** 2) / (2 * wave_widths[i] ** 2))
    leads_data[lead_name] = signal + np.random.normal(0, 0.01, len(time))

# Rhythm strip data (Lead II, 4x duration)
rhythm_time = np.linspace(0, duration * 4, int(sampling_rate * duration * 4))
np.random.seed(42)
rhythm_beat_starts = np.arange(0, rhythm_time[-1] + rr_interval, rr_interval)
rhythm_signal = np.zeros_like(rhythm_time)
gain_values_ii = np.array([lead_configs["II"][k] for k in wave_keys])
for beat_start in rhythm_beat_starts:
    dt = rhythm_time - beat_start
    for i in range(5):
        rhythm_signal += gain_values_ii[i] * np.exp(-((dt - wave_centers[i]) ** 2) / (2 * wave_widths[i] ** 2))
rhythm_signal += np.random.normal(0, 0.01, len(rhythm_time))

# Clinical 3x4 grid layout
grid_layout = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]

# Plot
ecg_paper_color = "#FFF5F0"
grid_light_color = "#F5C6C0"
grid_bold_color = "#E8908A"
signal_color = "#1A1A2E"

fig, axes = plt.subplots(
    4,
    4,
    figsize=(16, 9),
    facecolor=ecg_paper_color,
    gridspec_kw={"height_ratios": [1, 1, 1, 0.85], "hspace": 0.08, "wspace": 0.04},
)


def style_ecg_axis(ax):
    """Apply ECG paper grid styling to an axis."""
    ax.set_facecolor(ecg_paper_color)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.04))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.grid(which="major", color=grid_bold_color, linewidth=0.8, alpha=0.7)
    ax.grid(which="minor", color=grid_light_color, linewidth=0.3, alpha=0.5)
    ax.set_ylim(-1.8, 2.0)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(axis="both", which="both", length=0)
    for spine in ax.spines.values():
        spine.set_color(grid_bold_color)
        spine.set_linewidth(0.5)


# Plot 12 leads using seaborn lineplot
for row_idx in range(3):
    for col_idx in range(4):
        ax = axes[row_idx, col_idx]
        lead_name = grid_layout[row_idx][col_idx]
        signal = leads_data[lead_name]

        df = pd.DataFrame({"Time (s)": time, "Voltage (mV)": signal})
        sns.lineplot(data=df, x="Time (s)", y="Voltage (mV)", ax=ax, color=signal_color, linewidth=1.2, zorder=5)
        style_ecg_axis(ax)
        ax.set_xlim(0, duration)
        ax.set_xlabel("")
        ax.set_ylabel("")

        ax.text(
            0.03,
            0.95,
            lead_name,
            transform=ax.transAxes,
            fontsize=20,
            fontweight="bold",
            color="#333333",
            verticalalignment="top",
            zorder=10,
            bbox={"boxstyle": "square,pad=0.15", "facecolor": ecg_paper_color, "edgecolor": "none", "alpha": 0.85},
        )

# Rhythm strip (Lead II full-length) across the bottom row
for col_idx in range(4):
    ax = axes[3, col_idx]
    seg_start = col_idx * len(rhythm_time) // 4
    seg_end = (col_idx + 1) * len(rhythm_time) // 4
    t_seg = rhythm_time[seg_start:seg_end]
    s_seg = rhythm_signal[seg_start:seg_end]

    df_rhythm = pd.DataFrame({"Time (s)": t_seg, "Voltage (mV)": s_seg})
    sns.lineplot(data=df_rhythm, x="Time (s)", y="Voltage (mV)", ax=ax, color=signal_color, linewidth=1.2, zorder=5)
    style_ecg_axis(ax)
    ax.set_xlim(t_seg[0], t_seg[-1])
    ax.set_xlabel("")
    ax.set_ylabel("")

axes[3, 0].text(
    0.03,
    0.95,
    "II (rhythm)",
    transform=axes[3, 0].transAxes,
    fontsize=16,
    fontweight="bold",
    color="#333333",
    verticalalignment="top",
    zorder=10,
    bbox={"boxstyle": "square,pad=0.15", "facecolor": ecg_paper_color, "edgecolor": "none", "alpha": 0.85},
)

# Calibration marker (1mV pulse)
cal_ax = axes[0, 0]
cal_x_start = 0.02
cal_width = 0.08
cal_ax.plot(
    [cal_x_start, cal_x_start, cal_x_start + cal_width, cal_x_start + cal_width],
    [-1.4, -0.4, -0.4, -1.4],
    color=signal_color,
    linewidth=1.5,
    zorder=6,
)
cal_ax.text(cal_x_start + cal_width / 2, -0.2, "1 mV", fontsize=12, ha="center", color="#555555", zorder=10)

# Title and footer
fig.suptitle(
    "ecg-twelve-lead \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", color="#333333", y=0.98
)
fig.text(0.99, 0.01, "25 mm/s  |  10 mm/mV", fontsize=12, ha="right", va="bottom", color="#888888")

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=ecg_paper_color)
