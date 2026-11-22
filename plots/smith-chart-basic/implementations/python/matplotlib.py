"""anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-20
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Constants
Z0 = 50  # reference impedance in ohms

FREQUENCY = "Frequency (Hz)"  # role: frequency
Z_REAL = "Resistance (ohm)"  # role: z_real
Z_IMAG = "Reactance (ohm)"  # role: z_imag

# Data: replace this block with your own table, for example df = pd.read_csv("s11.csv")
frequency = np.linspace(1e9, 6e9, 50)
df = pd.DataFrame(
    {
        FREQUENCY: frequency,
        Z_REAL: 50
        + 30 * np.sin(2 * np.pi * (frequency - 1e9) / 2e9)
        + 10 * np.cos(4 * np.pi * (frequency - 1e9) / 5e9),
        Z_IMAG: 20 * np.cos(2 * np.pi * (frequency - 1e9) / 1.5e9) + 15 * np.sin(3 * np.pi * (frequency - 1e9) / 5e9),
    }
)

# Plot
z_norm = (df[Z_REAL].to_numpy() + 1j * df[Z_IMAG].to_numpy()) / Z0
gamma = (z_norm - 1) / (z_norm + 1)
freq_ghz = df[FREQUENCY].to_numpy() / 1e9

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")

# Smith chart grid — constant resistance circles
theta = np.linspace(0, 2 * np.pi, 500)
for r in [0, 0.2, 0.5, 1, 2, 5]:
    center = r / (r + 1)
    radius = 1 / (r + 1)
    x_c = center + radius * np.cos(theta)
    y_c = radius * np.sin(theta)
    mask = x_c**2 + y_c**2 <= 1.001
    ax.plot(np.where(mask, x_c, np.nan), np.where(mask, y_c, np.nan), color=INK_MUTED, linewidth=0.7, alpha=0.35)
    if r > 0:
        # label at the circle's left crossing of the real axis, so each sits on its own circle
        ax.text(center - radius + 0.015, 0.015, f"{r}", fontsize=7, color=INK_MUTED, ha="left", va="bottom")

# Constant reactance arcs
arc_theta = np.linspace(0, np.pi, 500)
for x in [0.2, 0.5, 1, 2, 5]:
    center_y = 1 / x
    radius = 1 / x
    x_arc = 1 + radius * np.cos(arc_theta + np.pi)

    # Inductive (upper half)
    y_arc_pos = center_y + radius * np.sin(arc_theta + np.pi)
    mask = x_arc**2 + y_arc_pos**2 <= 1.001
    ax.plot(
        np.where(mask, x_arc, np.nan), np.where(mask, y_arc_pos, np.nan), color=INK_MUTED, linewidth=0.7, alpha=0.35
    )

    # Capacitive (lower half)
    y_arc_neg = -center_y + radius * np.sin(arc_theta)
    mask = x_arc**2 + y_arc_neg**2 <= 1.001
    ax.plot(
        np.where(mask, x_arc, np.nan), np.where(mask, y_arc_neg, np.nan), color=INK_MUTED, linewidth=0.7, alpha=0.35
    )

    if x <= 1:
        angle = 2 * np.arctan(1 / x)
        lx, ly = np.cos(angle), np.sin(angle)
        ax.text(lx, ly + 0.06, f"+j{x}", fontsize=7, color=INK_MUTED, ha="center", va="bottom")
        ax.text(lx, -ly - 0.06, f"-j{x}", fontsize=7, color=INK_MUTED, ha="center", va="top")

# Real axis
ax.axhline(y=0, color=INK_MUTED, linewidth=0.7, alpha=0.35)

# Unit circle boundary
ax.plot(np.cos(theta), np.sin(theta), color=INK_SOFT, linewidth=1.5)

# VSWR circles via matplotlib.patches.Circle — distinctive matplotlib feature
for vswr in [1.5, 2, 3]:
    gamma_mag = (vswr - 1) / (vswr + 1)
    vswr_circle = mpatches.Circle(
        (0, 0), gamma_mag, fill=False, linestyle="--", edgecolor=IMPRINT_PALETTE[1], linewidth=1.0, alpha=0.55, zorder=3
    )
    ax.add_patch(vswr_circle)
    ax.text(0, gamma_mag + 0.04, f"VSWR={vswr}", fontsize=7, color=IMPRINT_PALETTE[1], ha="center", alpha=0.8)

# Matched condition marker
ax.plot(0, 0, "o", color=IMPRINT_PALETTE[0], markersize=7, zorder=6, label="Matched (Z=Z₀)")

# Impedance locus via LineCollection colored by frequency — distinctive matplotlib feature
# Imprint sequential colormap for continuous frequency
points = np.array([gamma.real, gamma.imag]).T.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)
norm = Normalize(vmin=freq_ghz[0], vmax=freq_ghz[-1])
lc = LineCollection(segments, cmap=imprint_seq, norm=norm, linewidth=2.5, zorder=5)
lc.set_array(freq_ghz[:-1])
ax.add_collection(lc)

# Key frequency markers, color-matched to the locus colormap
key_indices = np.linspace(0, len(df) - 1, 5).round().astype(int)
ax.scatter(
    gamma.real[key_indices],
    gamma.imag[key_indices],
    c=freq_ghz[key_indices],
    cmap=imprint_seq,
    norm=norm,
    s=40,
    edgecolors=PAGE_BG,
    linewidths=0.8,
    zorder=7,
)

# Frequency labels at key points
for idx in key_indices:
    x_pos, y_pos = gamma.real[idx], gamma.imag[idx]
    # push each label radially outward from the chart center, anchored on its outer corner
    direction = gamma[idx] / abs(gamma[idx])
    direction /= abs(direction)
    offset_x, offset_y = 0.12 * direction.real, 0.12 * direction.imag
    ax.annotate(
        f"{freq_ghz[idx]:.1f} GHz",
        (x_pos, y_pos),
        xytext=(x_pos + offset_x, y_pos + offset_y),
        fontsize=7,
        color=INK,
        ha="left" if direction.real >= 0 else "right",
        va="bottom" if direction.imag >= 0 else "top",
        arrowprops={"arrowstyle": "->", "color": INK_SOFT, "lw": 0.8},
        zorder=10,
    )

# Colorbar — frequency scale for the Imprint locus
cbar = plt.colorbar(lc, ax=ax, shrink=0.72, pad=0.02, fraction=0.03)
cbar.set_label("Frequency (GHz)", fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=7, labelcolor=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_xlim(-1.3, 1.3)
ax.set_ylim(-1.3, 1.3)
ax.set_xlabel("Real(Γ)", fontsize=10, color=INK)
ax.set_ylabel("Imag(Γ)", fontsize=10, color=INK)
ax.set_title("smith-chart-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xticks([])
ax.set_yticks([])

for spine in ax.spines.values():
    spine.set_visible(False)

# Cardinal direction labels
ax.text(1.18, 0, "Open\n(Γ=1)", fontsize=7, ha="center", va="center", color=INK_SOFT)
ax.text(-1.18, 0, "Short\n(Γ=-1)", fontsize=7, ha="center", va="center", color=INK_SOFT)
ax.text(0, 1.26, "+jX (Inductive)", fontsize=7, ha="center", va="center", color=INK_MUTED)
ax.text(0, -1.26, "-jX (Capacitive)", fontsize=7, ha="center", va="center", color=INK_MUTED)

# Legend
locus_handle = Line2D([], [], color=imprint_seq(0.5), linewidth=2.5, label="Impedance Locus")
handles, _ = ax.get_legend_handles_labels()
leg = ax.legend(handles=[*handles, locus_handle], fontsize=7, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
