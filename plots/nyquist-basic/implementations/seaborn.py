""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# Build DataFrame for seaborn-idiomatic plotting
df_pos = pd.DataFrame({"Real": real_part, "Imaginary": imag_part, "Branch": "G(jω), ω ≥ 0"})
df_neg = pd.DataFrame({"Real": real_part, "Imaginary": -imag_part, "Branch": "G(jω), ω < 0"})
df = pd.concat([df_pos, df_neg], ignore_index=True)

# Seaborn theme and palette
palette = sns.color_palette(["#306998", "#306998"])
sns.set_theme(
    style="whitegrid",
    context="talk",
    font_scale=1.2,
    rc={"grid.alpha": 0.15, "grid.linewidth": 0.8, "axes.edgecolor": "#bbbbbb"},
)

fig, ax = plt.subplots(figsize=(10, 10))

# Plot both branches using hue-based seaborn lineplot
sns.lineplot(
    data=df,
    x="Real",
    y="Imaginary",
    hue="Branch",
    palette=palette,
    linewidth=2.5,
    sort=False,
    estimator=None,
    style="Branch",
    dashes={"G(jω), ω ≥ 0": "", "G(jω), ω < 0": (5, 3)},
    ax=ax,
    legend=True,
)

# Adjust mirror branch alpha via the line artist
lines = ax.get_lines()
for line in lines:
    if line.get_linestyle() != "-":
        line.set_alpha(0.4)

# Unit circle
theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(np.cos(theta), np.sin(theta), color="#999999", linewidth=1.2, linestyle=":", alpha=0.6, zorder=1)

# Critical point (-1, 0)
crit_palette = sns.color_palette(["#cc3333"])
ax.plot(-1, 0, marker="x", color=crit_palette[0], markersize=16, markeredgewidth=3, zorder=5)
ax.annotate(
    "Critical point (-1, 0)",
    xy=(-1, 0),
    xytext=(-1.8, 2.5),
    fontsize=14,
    color=crit_palette[0],
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": crit_palette[0], "lw": 1.5},
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

# Frequency annotations at key points — use seaborn scatterplot for markers
freq_labels = [0.1, 0.5, 1.0, 3.0, 10.0]
freq_indices = [np.argmin(np.abs(omega - f)) for f in freq_labels]
freq_df = pd.DataFrame(
    {
        "Real": [real_part[i] for i in freq_indices],
        "Imaginary": [imag_part[i] for i in freq_indices],
        "Frequency": [f"ω = {f} rad/s" for f in freq_labels],
    }
)
sns.scatterplot(
    data=freq_df,
    x="Real",
    y="Imaginary",
    color="#306998",
    s=120,
    zorder=4,
    ax=ax,
    legend=False,
    edgecolor="white",
    linewidth=1.5,
)

# Annotate frequency points with manual offsets to avoid crowding
offsets = {0.1: (0.5, -0.8), 0.5: (0.6, -0.9), 1.0: (0.6, -0.8), 3.0: (0.8, -1.2), 10.0: (1.0, 0.8)}
for i, (_, row) in enumerate(freq_df.iterrows()):
    x, y = row["Real"], row["Imaginary"]
    f = freq_labels[i]
    ox, oy = offsets[f]
    ax.annotate(
        row["Frequency"],
        xy=(x, y),
        xytext=(x + ox, y + oy),
        fontsize=12,
        color="#444444",
        arrowprops={"arrowstyle": "->", "color": "#aaaaaa", "lw": 1},
    )

# Style — use seaborn's despine
ax.set_xlabel("Real Part of G(jω)", fontsize=20)
ax.set_ylabel("Imaginary Part of G(jω)", fontsize=20)
ax.set_title("nyquist-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.set_aspect("equal")
ax.axhline(y=0, color="#cccccc", linewidth=0.8, zorder=0)
ax.axvline(x=0, color="#cccccc", linewidth=0.8, zorder=0)
sns.despine(ax=ax)

# Refine legend — position in upper right away from data
ax.legend(loc="upper right", framealpha=0.9, edgecolor="#cccccc", fontsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
