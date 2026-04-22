""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from scipy import signal


# Data — second-order system with delay approximation: G(s) = 2 / (s+1)(0.5s+1)(0.2s+1)
num = [2.0]
den = np.polymul(np.polymul([1, 1], [0.5, 1]), [0.2, 1])
system = signal.TransferFunction(num, den)

omega = np.logspace(-1.5, 2, 800)
_, H = signal.freqresp(system, w=omega)

real = H.real
imag = H.imag

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

ax.plot(real, imag, color="#306998", linewidth=3, label="G(jω)", zorder=3)
ax.plot(real, -imag, color="#306998", linewidth=3, alpha=0.35, linestyle="--", label="G(−jω)", zorder=3)

# Direction arrows along the curve
for frac in [0.08, 0.2, 0.4, 0.65]:
    idx = int(frac * len(omega))
    ax.annotate(
        "",
        xy=(real[idx + 1], imag[idx + 1]),
        xytext=(real[idx], imag[idx]),
        arrowprops={"arrowstyle": "-|>", "color": "#306998", "lw": 2.5, "mutation_scale": 22},
        zorder=4,
    )

# Unit circle
unit_circle = Circle((0, 0), 1, fill=False, color="#999999", linewidth=1.5, linestyle=":", zorder=2)
ax.add_patch(unit_circle)

# Critical point (-1, 0)
ax.plot(
    -1, 0, marker="x", color="#D32F2F", markersize=18, markeredgewidth=3.5, zorder=5, label="Critical point (−1, 0)"
)

# Frequency annotations at key points
freq_annotations = [(0.3, (15, 12)), (1.0, (15, 12)), (2.0, (-15, -18)), (5.0, (-15, 14)), (10.0, (12, 12))]
for freq_val, (ox, oy) in freq_annotations:
    idx = np.argmin(np.abs(omega - freq_val))
    ax.plot(real[idx], imag[idx], "o", color="#306998", markersize=8, zorder=5)
    ha = "left" if ox > 0 else "right"
    va = "bottom" if oy > 0 else "top"
    ax.annotate(
        f"ω={freq_val:g}",
        xy=(real[idx], imag[idx]),
        xytext=(ox, oy),
        textcoords="offset points",
        fontsize=14,
        color="#444444",
        fontweight="medium",
        ha=ha,
        va=va,
        zorder=5,
    )

# Style
ax.set_xlabel("Real", fontsize=20)
ax.set_ylabel("Imaginary", fontsize=20)
ax.set_title("nyquist-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")
ax.axhline(0, color="#cccccc", linewidth=0.8, zorder=1)
ax.axvline(0, color="#cccccc", linewidth=0.8, zorder=1)
ax.legend(fontsize=16, loc="lower left", framealpha=0.9)
ax.grid(True, alpha=0.15, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
