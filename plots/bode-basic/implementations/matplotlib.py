""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-21
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Third-order open-loop transfer function:
# H(s) = K / ((s/w1 + 1)(s/w2 + 1)(s/w3 + 1))
# Three poles at 1, 10, and 80 Hz with gain K=20
K = 20
poles_hz = np.array([1.0, 10.0, 80.0])
poles_rad = 2 * np.pi * poles_hz

frequency_hz = np.logspace(-1, 3, 500)
omega = 2 * np.pi * frequency_hz
jw = 1j * omega

H = K / np.prod([(jw / p + 1) for p in poles_rad], axis=0)
magnitude_db = 20 * np.log10(np.abs(H))
phase_deg = np.degrees(np.unwrap(np.angle(H)))

# Compute gain crossover (0 dB crossing)
sign_changes_mag = np.diff(np.sign(magnitude_db))
gain_crossover_idx = np.where(sign_changes_mag != 0)[0]
if len(gain_crossover_idx) > 0:
    gc_idx = gain_crossover_idx[0]
    gain_crossover_freq = frequency_hz[gc_idx]
    phase_at_gc = phase_deg[gc_idx]
    phase_margin = 180 + phase_at_gc
else:
    gain_crossover_freq = None

# Compute phase crossover (-180 deg crossing)
sign_changes_phase = np.diff(np.sign(phase_deg + 180))
phase_crossover_idx = np.where(sign_changes_phase != 0)[0]
if len(phase_crossover_idx) > 0:
    pc_idx = phase_crossover_idx[0]
    phase_crossover_freq = frequency_hz[pc_idx]
    gain_at_pc = magnitude_db[pc_idx]
    gain_margin = -gain_at_pc
else:
    phase_crossover_freq = None

# Plot
fig, (ax_mag, ax_phase) = plt.subplots(
    2, 1, figsize=(16, 9), sharex=True, gridspec_kw={"height_ratios": [1, 1], "hspace": 0.08}
)

# Magnitude plot
ax_mag.semilogx(frequency_hz, magnitude_db, color="#306998", linewidth=3)
ax_mag.axhline(y=0, color="#888888", linewidth=1, linestyle="--", alpha=0.6)

# Gain margin annotation
if phase_crossover_freq is not None:
    ax_mag.vlines(phase_crossover_freq, gain_at_pc, 0, colors="#D4513D", linewidth=2.5)
    ax_mag.plot(phase_crossover_freq, gain_at_pc, "o", color="#D4513D", markersize=10, zorder=5)
    ax_mag.annotate(
        f"GM = {gain_margin:.1f} dB",
        xy=(phase_crossover_freq, (gain_at_pc + 0) / 2),
        xytext=(phase_crossover_freq * 3, (gain_at_pc + 0) / 2 + 8),
        fontsize=16,
        color="#D4513D",
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": "#D4513D", "lw": 2},
    )

# Phase plot
ax_phase.semilogx(frequency_hz, phase_deg, color="#306998", linewidth=3)
ax_phase.axhline(y=-180, color="#888888", linewidth=1, linestyle="--", alpha=0.6)

# Phase margin annotation
if gain_crossover_freq is not None:
    ax_phase.vlines(gain_crossover_freq, -180, phase_at_gc, colors="#2E8B57", linewidth=2.5)
    ax_phase.plot(gain_crossover_freq, phase_at_gc, "o", color="#2E8B57", markersize=10, zorder=5)
    ax_phase.annotate(
        f"PM = {phase_margin:.1f}°",
        xy=(gain_crossover_freq, (-180 + phase_at_gc) / 2),
        xytext=(gain_crossover_freq * 6, (-180 + phase_at_gc) / 2 + 20),
        fontsize=16,
        color="#2E8B57",
        fontweight="bold",
        arrowprops={"arrowstyle": "->", "color": "#2E8B57", "lw": 2},
    )

# Style - Magnitude
ax_mag.set_ylabel("Magnitude (dB)", fontsize=20)
ax_mag.set_title("bode-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax_mag.tick_params(axis="both", labelsize=16)
ax_mag.spines["top"].set_visible(False)
ax_mag.spines["right"].set_visible(False)
ax_mag.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax_mag.xaxis.grid(True, alpha=0.15, linewidth=0.8)

# Style - Phase
ax_phase.set_xlabel("Frequency (Hz)", fontsize=20)
ax_phase.set_ylabel("Phase (°)", fontsize=20)
ax_phase.tick_params(axis="both", labelsize=16)
ax_phase.spines["top"].set_visible(False)
ax_phase.spines["right"].set_visible(False)
ax_phase.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax_phase.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax_phase.set_yticks([0, -45, -90, -135, -180, -225, -270])

# Save
fig.subplots_adjust(left=0.1, right=0.95, top=0.93, bottom=0.1)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
