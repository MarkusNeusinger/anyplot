"""pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-21
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn theme and context for consistent, publication-quality styling
sns.set_theme(style="ticks", context="talk", font_scale=1.1)

# Colorblind-safe palette: blue for GM, orange for PM (Tol bright scheme)
gm_color, pm_color = "#0077BB", "#EE7733"
line_color = "#306998"

# Data — open-loop transfer function: H(s) = K*p1*p2 / (s*(s+p1)*(s+p2))
# Type-1 system with two real poles — classic controls textbook example
K = 40.0
p1 = 2 * np.pi * 5  # pole at 5 Hz
p2 = 2 * np.pi * 50  # pole at 50 Hz

frequency_hz = np.logspace(-1, 3, 600)
omega = 2 * np.pi * frequency_hz
s = 1j * omega

H = K * p1 * p2 / (s * (s + p1) * (s + p2))
magnitude_db = 20 * np.log10(np.abs(H))
phase_deg = np.degrees(np.unwrap(np.angle(H)))

# Gain crossover: where magnitude crosses 0 dB (interpolated)
sign_changes = np.diff(np.sign(magnitude_db))
gc_indices = np.where(sign_changes != 0)[0]
idx = gc_indices[0]
frac = -magnitude_db[idx] / (magnitude_db[idx + 1] - magnitude_db[idx])
gain_cross_freq = frequency_hz[idx] * (frequency_hz[idx + 1] / frequency_hz[idx]) ** frac
phase_at_gain_cross = phase_deg[idx] + frac * (phase_deg[idx + 1] - phase_deg[idx])
phase_margin = 180 + phase_at_gain_cross

# Phase crossover: where phase crosses -180 deg (interpolated)
phase_shift = phase_deg + 180
sign_changes_ph = np.diff(np.sign(phase_shift))
pc_indices = np.where(sign_changes_ph != 0)[0]
idx = pc_indices[0]
frac = -phase_shift[idx] / (phase_shift[idx + 1] - phase_shift[idx])
phase_cross_freq = frequency_hz[idx] * (frequency_hz[idx + 1] / frequency_hz[idx]) ** frac
mag_at_phase_cross = magnitude_db[idx] + frac * (magnitude_db[idx + 1] - magnitude_db[idx])
gain_margin = -mag_at_phase_cross

# Build long-form DataFrame for seaborn — separate panels via hue/faceting
df_mag = pd.DataFrame({"Frequency (Hz)": frequency_hz, "value": magnitude_db, "panel": "Magnitude (dB)"})
df_phase = pd.DataFrame({"Frequency (Hz)": frequency_hz, "value": phase_deg, "panel": "Phase (\u00b0)"})
df = pd.concat([df_mag, df_phase], ignore_index=True)

# Use FacetGrid for dual-panel layout — idiomatic seaborn figure-level approach
g = sns.FacetGrid(
    df, row="panel", height=4.5, aspect=16 / 9 / 1, sharex=True, sharey=False, gridspec_kws={"hspace": 0.1}
)
g.map_dataframe(sns.lineplot, x="Frequency (Hz)", y="value", color=line_color, linewidth=3)

ax_mag = g.axes[0, 0]
ax_phase = g.axes[1, 0]

# Remove FacetGrid row titles and default axis labels
g.set_titles("")
g.set_axis_labels("", "")

# Log scale on shared x-axis
for ax in g.axes.flat:
    ax.set_xscale("log")

# Reference lines
ax_mag.axhline(0, color="#888888", linewidth=1.2, linestyle="--", alpha=0.6)
ax_phase.axhline(-180, color="#888888", linewidth=1.2, linestyle="--", alpha=0.6)

# Gain margin annotation (blue) — vertical line at phase crossover
ax_mag.vlines(phase_cross_freq, mag_at_phase_cross, 0, color=gm_color, linewidth=2.5, alpha=0.85)
ax_mag.plot(phase_cross_freq, mag_at_phase_cross, "o", color=gm_color, markersize=10, zorder=5)
ax_mag.plot(phase_cross_freq, 0, "o", color=gm_color, markersize=10, zorder=5)
gm_label_y = mag_at_phase_cross / 2
ax_mag.annotate(
    f"GM = {gain_margin:.1f} dB",
    xy=(phase_cross_freq, gm_label_y),
    xytext=(phase_cross_freq * 3, gm_label_y + 8),
    fontsize=15,
    fontweight="bold",
    color=gm_color,
    arrowprops={"arrowstyle": "->", "color": gm_color, "lw": 2},
    bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": gm_color, "alpha": 0.9},
)

# Phase margin annotation (orange) — vertical line at gain crossover
ax_phase.vlines(gain_cross_freq, -180, phase_at_gain_cross, color=pm_color, linewidth=2.5, alpha=0.85)
ax_phase.plot(gain_cross_freq, phase_at_gain_cross, "o", color=pm_color, markersize=10, zorder=5)
ax_phase.plot(gain_cross_freq, -180, "o", color=pm_color, markersize=10, zorder=5)
pm_label_y = (phase_at_gain_cross - 180) / 2
ax_phase.annotate(
    f"PM = {phase_margin:.1f}\u00b0",
    xy=(gain_cross_freq, pm_label_y),
    xytext=(gain_cross_freq * 3.5, pm_label_y + 15),
    fontsize=15,
    fontweight="bold",
    color=pm_color,
    arrowprops={"arrowstyle": "->", "color": pm_color, "lw": 2},
    bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": pm_color, "alpha": 0.9},
)

# Crossover frequency vertical markers
for ax in [ax_mag, ax_phase]:
    ax.axvline(gain_cross_freq, color=pm_color, linewidth=1, linestyle=":", alpha=0.4)
    ax.axvline(phase_cross_freq, color=gm_color, linewidth=1, linestyle=":", alpha=0.4)

# Axis labels and title
ax_mag.set_ylabel("Magnitude (dB)", fontsize=20)
ax_mag.set_title("bode-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax_mag.set_xlabel("")
ax_mag.tick_params(axis="both", labelsize=16)

ax_phase.set_xlabel("Frequency (Hz)", fontsize=20)
ax_phase.set_ylabel("Phase (\u00b0)", fontsize=20)
ax_phase.tick_params(axis="both", labelsize=16)
ax_phase.set_yticks([-90, -135, -180, -225, -270])

# Use seaborn's despine for clean spine removal
sns.despine(ax=ax_mag)
sns.despine(ax=ax_phase)

# Subtle grid styling
for ax in [ax_mag, ax_phase]:
    ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
    ax.xaxis.grid(True, alpha=0.15, linewidth=0.5)

# Resize figure to match target canvas
g.figure.set_size_inches(16, 9)

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
