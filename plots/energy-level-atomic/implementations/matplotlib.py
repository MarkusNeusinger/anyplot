""" pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-02-27
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data — Hydrogen atom energy levels: E_n = -13.6 / n^2 (eV)
n_values = np.arange(1, 7)
energies = -13.6 / n_values**2  # all negative

# Sqrt-compressed display positions: y = -sqrt(|E|)
# Preserves ordering (n=1 at bottom, ionization at top) while spreading upper levels
y_pos = -np.sqrt(np.abs(energies))
ion_y = 0.0  # ionization at E=0 → y=0

# Balmer series transitions with spectral colors
balmer_data = [
    (3, 2, "#D63333"),  # H-alpha  656 nm (red)
    (4, 2, "#3A9BDC"),  # H-beta   486 nm (cyan-blue)
    (5, 2, "#6A5ACD"),  # H-gamma  434 nm (blue-violet)
    (6, 2, "#7B3FA0"),  # H-delta  410 nm (violet)
]

# Lyman series transitions (UV, single color)
lyman_data = [(2, 1), (3, 1), (4, 1), (5, 1), (6, 1)]
lyman_color = "#D4880F"

# Lookup: quantum number → display y position
y_of = {n: -np.sqrt(13.6 / n**2) for n in range(1, 7)}

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

left = 0.18
right = 0.82
gap = 0.06  # arrow gap from level lines

# Energy level lines
for n, energy, y in zip(n_values, energies, y_pos, strict=True):
    ax.plot([left, right], [y, y], color="#306998", linewidth=2.5, solid_capstyle="round", zorder=3)
    ax.text(right + 0.02, y, f"n = {n}", fontsize=18, va="center", ha="left", color="#306998", fontweight="medium")
    ax.text(left - 0.02, y, f"{energy:.2f} eV", fontsize=16, va="center", ha="right", color="#555555")

# Ionization limit (dashed)
ax.plot([left, right], [ion_y, ion_y], color="#888888", linewidth=1.5, linestyle="--", zorder=2)
ax.text(right + 0.02, ion_y, "Ionization (0 eV)", fontsize=16, va="center", ha="left", color="#888888")

# Lyman series arrows (left side)
lyman_x = np.linspace(0.24, 0.40, len(lyman_data))
for (upper, lower), xp in zip(lyman_data, lyman_x, strict=True):
    ax.annotate(
        "",
        xy=(xp, y_of[lower] + gap),
        xytext=(xp, y_of[upper] - gap),
        arrowprops={"arrowstyle": "->,head_width=0.3,head_length=0.15", "color": lyman_color, "lw": 2.2},
        zorder=4,
    )

# Balmer series arrows (right side, colored by wavelength)
balmer_x = np.linspace(0.55, 0.72, len(balmer_data))
for (upper, lower, color), xp in zip(balmer_data, balmer_x, strict=True):
    ax.annotate(
        "",
        xy=(xp, y_of[lower] + gap),
        xytext=(xp, y_of[upper] - gap),
        arrowprops={"arrowstyle": "->,head_width=0.3,head_length=0.15", "color": color, "lw": 2.2},
        zorder=4,
    )

# Series labels in clear space
ax.text(
    0.32,
    (y_of[1] + y_of[2]) / 2,
    "Lyman series\n(UV)",
    fontsize=16,
    ha="center",
    va="center",
    color=lyman_color,
    fontstyle="italic",
)
ax.text(
    0.76,
    (y_of[3] + y_of[4]) / 2,
    "Balmer series\n(Visible)",
    fontsize=16,
    ha="center",
    va="center",
    color="#3A9BDC",
    fontstyle="italic",
)

# Legend for transition colors
legend_handles = [
    mpatches.Patch(color="#D63333", label="H-\u03b1  656 nm"),
    mpatches.Patch(color="#3A9BDC", label="H-\u03b2  486 nm"),
    mpatches.Patch(color="#6A5ACD", label="H-\u03b3  434 nm"),
    mpatches.Patch(color="#7B3FA0", label="H-\u03b4  410 nm"),
    mpatches.Patch(color=lyman_color, label="Lyman (UV)"),
]
ax.legend(handles=legend_handles, fontsize=16, loc="lower right", framealpha=0.9, edgecolor="#CCCCCC", fancybox=False)

# Style
ax.set_ylabel("Energy (eV)", fontsize=20)
ax.set_title("energy-level-atomic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_xlim(0.05, 1.08)
ax.set_ylim(y_of[1] - 0.3, ion_y + 0.4)
ax.set_xticks([])

# Custom y-ticks showing real energy values on compressed axis
tick_energies = np.array([0, -0.5, -1, -2, -4, -8, -14])
tick_y = -np.sqrt(np.abs(tick_energies))
ax.set_yticks(tick_y)
ax.set_yticklabels([f"{e:g}" for e in tick_energies])
ax.tick_params(axis="y", labelsize=16)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
