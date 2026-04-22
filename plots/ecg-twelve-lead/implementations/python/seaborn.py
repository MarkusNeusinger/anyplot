""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-19
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns


# Style - seaborn theme with ECG paper appearance
sns.set_theme(style="white", rc={"axes.facecolor": "#FFF5F0", "figure.facecolor": "#FFF5F0"})
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

# Long-format DataFrame for seaborn FacetGrid
lead_order = ["I", "aVR", "V1", "V4", "II", "aVL", "V2", "V5", "III", "aVF", "V3", "V6"]
df_ecg = pd.concat(
    [pd.DataFrame({"Time (s)": time, "Voltage (mV)": leads_data[name], "Lead": name}) for name in lead_order],
    ignore_index=True,
)

# Colors
ecg_paper = "#FFF5F0"
grid_light = "#F5C6C0"
grid_bold = "#E8908A"
signal_color = "#1A1A2E"

# Plot - seaborn relplot with FacetGrid for clinical 3x4 layout
g = sns.relplot(
    data=df_ecg,
    x="Time (s)",
    y="Voltage (mV)",
    col="Lead",
    col_wrap=4,
    col_order=lead_order,
    kind="line",
    color=signal_color,
    linewidth=1.5,
    height=2.1,
    aspect=1.78,
    facet_kws={"sharex": True, "sharey": True},
)

# Style each facet as ECG paper grid
g.set_titles("")
g.set_axis_labels("", "")
for ax, lead_name in zip(g.axes.flat, lead_order, strict=True):
    ax.set_facecolor(ecg_paper)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.04))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.grid(which="major", color=grid_bold, linewidth=0.8, alpha=0.7)
    ax.grid(which="minor", color=grid_light, linewidth=0.3, alpha=0.5)
    ax.set_ylim(-1.8, 2.0)
    ax.set_xlim(0, duration)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(axis="both", which="both", length=0)
    for spine in ax.spines.values():
        spine.set_color(grid_bold)
        spine.set_linewidth(0.5)
    ax.text(
        0.03,
        0.95,
        lead_name,
        transform=ax.transAxes,
        fontsize=20,
        fontweight="bold",
        color="#333333",
        va="top",
        zorder=10,
        bbox={"boxstyle": "square,pad=0.15", "facecolor": ecg_paper, "edgecolor": "none", "alpha": 0.85},
    )

# Calibration marker (1mV pulse) in first panel
cal_ax = g.axes.flat[0]
cal_x = 0.02
cal_w = 0.08
cal_ax.plot(
    [cal_x, cal_x, cal_x + cal_w, cal_x + cal_w], [-1.4, -0.4, -0.4, -1.4], color=signal_color, linewidth=1.5, zorder=6
)
cal_ax.text(cal_x + cal_w / 2, -0.2, "1 mV", fontsize=16, ha="center", color="#555555", zorder=10)

# Rhythm strip - Lead II continuous across full bottom
fig = g.figure
fig.subplots_adjust(bottom=0.16, hspace=0.12, wspace=0.04)
rhythm_ax = fig.add_axes([0.065, 0.02, 0.87, 0.10], facecolor=ecg_paper)

rhythm_time = np.linspace(0, duration * 4, int(sampling_rate * duration * 4))
np.random.seed(42)
rhythm_beat_starts = np.arange(0, rhythm_time[-1] + rr_interval, rr_interval)
rhythm_signal = np.zeros_like(rhythm_time)
gain_ii = np.array([lead_configs["II"][k] for k in wave_keys])
for beat_start in rhythm_beat_starts:
    dt = rhythm_time - beat_start
    for i in range(5):
        rhythm_signal += gain_ii[i] * np.exp(-((dt - wave_centers[i]) ** 2) / (2 * wave_widths[i] ** 2))
rhythm_signal += np.random.normal(0, 0.01, len(rhythm_time))

df_rhythm = pd.DataFrame({"Time (s)": rhythm_time, "Voltage (mV)": rhythm_signal})
sns.lineplot(data=df_rhythm, x="Time (s)", y="Voltage (mV)", ax=rhythm_ax, color=signal_color, linewidth=1.5)

# Style rhythm strip with ECG paper grid (wider intervals for 10s span)
rhythm_ax.set_facecolor(ecg_paper)
rhythm_ax.xaxis.set_major_locator(ticker.MultipleLocator(1.0))
rhythm_ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.2))
rhythm_ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
rhythm_ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
rhythm_ax.grid(which="major", color=grid_bold, linewidth=0.8, alpha=0.7)
rhythm_ax.grid(which="minor", color=grid_light, linewidth=0.3, alpha=0.5)
rhythm_ax.set_ylim(-1.8, 2.0)
rhythm_ax.set_xlim(0, rhythm_time[-1])
rhythm_ax.set_xticklabels([])
rhythm_ax.set_yticklabels([])
rhythm_ax.tick_params(axis="both", which="both", length=0)
for spine in rhythm_ax.spines.values():
    spine.set_color(grid_bold)
    spine.set_linewidth(0.5)
rhythm_ax.set_xlabel("")
rhythm_ax.set_ylabel("")
rhythm_ax.text(
    0.005,
    0.9,
    "II (rhythm)",
    transform=rhythm_ax.transAxes,
    fontsize=16,
    fontweight="bold",
    color="#333333",
    va="top",
    zorder=10,
    bbox={"boxstyle": "square,pad=0.15", "facecolor": ecg_paper, "edgecolor": "none", "alpha": 0.85},
)

# Title and footer
fig.suptitle(
    "ecg-twelve-lead \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", color="#333333", y=0.99
)
fig.text(0.99, 0.005, "25 mm/s  |  10 mm/mV", fontsize=16, ha="right", va="bottom", color="#888888")

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=ecg_paper)
