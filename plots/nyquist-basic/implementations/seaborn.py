""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import signal


# Data — open-loop transfer function: G(s) = 10 / ((s+1)(0.5s+1)(0.2s+1))
num = [10.0]
den = np.polymul(np.polymul([1.0, 1.0], [0.5, 1.0]), [0.2, 1.0])
system = signal.TransferFunction(num, den)

omega = np.logspace(-2, 2, 800)
_, H = signal.freqresp(system, omega)

real_part = H.real
imag_part = H.imag

# Plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(10, 10))

sns.lineplot(x=real_part, y=imag_part, ax=ax, color="#306998", linewidth=2.5, sort=False, estimator=None)

# Mirror (negative frequencies)
sns.lineplot(
    x=real_part,
    y=-imag_part,
    ax=ax,
    color="#306998",
    linewidth=2.5,
    linestyle="--",
    alpha=0.4,
    sort=False,
    estimator=None,
)

# Unit circle
theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(np.cos(theta), np.sin(theta), color="#999999", linewidth=1.2, linestyle=":", alpha=0.6, zorder=1)

# Critical point (-1, 0)
ax.plot(-1, 0, marker="x", color="#cc3333", markersize=16, markeredgewidth=3, zorder=5)
ax.annotate(
    "(-1, 0)",
    xy=(-1, 0),
    xytext=(-1.8, 0.6),
    fontsize=14,
    color="#cc3333",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#cc3333", "lw": 1.5},
)

# Direction arrows along the curve
arrow_indices = [80, 250, 450]
for idx in arrow_indices:
    ax.annotate(
        "",
        xy=(real_part[idx + 8], imag_part[idx + 8]),
        xytext=(real_part[idx], imag_part[idx]),
        arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 2.5},
    )

# Frequency annotations at key points
freq_labels = [0.1, 0.5, 1.0, 3.0, 10.0]
for f in freq_labels:
    idx = np.argmin(np.abs(omega - f))
    ax.plot(real_part[idx], imag_part[idx], "o", color="#306998", markersize=7, zorder=4)
    offset_x = 0.3
    offset_y = -0.3 if imag_part[idx] < 0 else 0.3
    ax.annotate(
        f"ω={f}",
        xy=(real_part[idx], imag_part[idx]),
        xytext=(real_part[idx] + offset_x, imag_part[idx] + offset_y),
        fontsize=12,
        color="#555555",
        arrowprops={"arrowstyle": "->", "color": "#aaaaaa", "lw": 1},
    )

# Style
ax.set_xlabel("Real", fontsize=20)
ax.set_ylabel("Imaginary", fontsize=20)
ax.set_title("nyquist-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.axhline(y=0, color="#cccccc", linewidth=0.8)
ax.axvline(x=0, color="#cccccc", linewidth=0.8)
ax.grid(True, alpha=0.15, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
