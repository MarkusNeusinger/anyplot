""" anyplot.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 76/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
REACT_COLOR = IMPRINT_PALETTE[1]  # Reactance arcs
VSWR_COLOR = IMPRINT_PALETTE[2]  # VSWR reference circle

# Imprint sequential colormap for the frequency sweep
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Apply seaborn theme for chrome elements
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
Z0 = 50  # reference impedance in ohms
VSWR = 3  # reference standing-wave ratio drawn as a constant-|Γ| circle
N_KEY_POINTS = 5  # frequency labels along the locus

# Columns: set these to your table's column names
FREQUENCY = "Frequency (GHz)"  # role: frequency
Z_REAL = "Resistance (Ω)"  # role: z_real
Z_IMAG = "Reactance (Ω)"  # role: z_imag

# Data: replace this block with your own table, for example df = pd.read_csv("s11.csv")
# Antenna impedance sweep 1–6 GHz
n_points = 100
t = np.linspace(0, 1.8 * np.pi, n_points)
df = pd.DataFrame(
    {
        FREQUENCY: np.linspace(1, 6, n_points),
        Z_REAL: 50 + 30 * np.sin(t) + 15 * np.cos(2 * t) + 10 * (t / (2 * np.pi)),
        Z_IMAG: 40 * np.sin(1.5 * t) + 20 * np.cos(t) - 15 * (t / (2 * np.pi)),
    }
)

# Plot: reads only df and the constants above
z_norm = (df[Z_REAL].to_numpy() + 1j * df[Z_IMAG].to_numpy()) / Z0
gamma = (z_norm - 1) / (z_norm + 1)
locus = pd.DataFrame({"gamma_real": gamma.real, "gamma_imag": gamma.imag, FREQUENCY: df[FREQUENCY]})
f_min, f_max = df[FREQUENCY].min(), df[FREQUENCY].max()

# Square canvas (2400×2400 px)
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Smith chart grid — constant resistance circles
theta = np.linspace(0, 2 * np.pi, 300)
for r in [0, 0.2, 0.5, 1, 2, 5]:
    cx = r / (r + 1) + (1 / (r + 1)) * np.cos(theta)
    cy = (1 / (r + 1)) * np.sin(theta)
    mask = cx**2 + cy**2 <= 1.001
    ax.plot(cx[mask], cy[mask], color=INK_SOFT, linewidth=0.8, alpha=0.6, zorder=1)
    if r > 0:
        lx = r / (r + 1) - 1 / (r + 1) + 0.02
        if lx > -0.95:
            ax.text(lx, 0.03, f"r={r}", fontsize=8, color=INK_SOFT, va="bottom", zorder=2)

# Constant reactance arcs
arc_theta = np.linspace(-np.pi / 2, np.pi / 2, 300)
for x in [0.2, 0.5, 1, 2, 5]:
    radius = 1 / x
    arc_x = 1 + radius * np.cos(arc_theta)
    arc_y_pos = (1 / x) + radius * np.sin(arc_theta)
    arc_y_neg = -(1 / x) + radius * np.sin(arc_theta)

    mask_pos = (arc_x**2 + arc_y_pos**2 <= 1.001) & (arc_x >= -0.001)
    ax.plot(arc_x[mask_pos], arc_y_pos[mask_pos], color=REACT_COLOR, linewidth=0.8, alpha=0.6, zorder=1)

    mask_neg = (arc_x**2 + arc_y_neg**2 <= 1.001) & (arc_x >= -0.001)
    ax.plot(arc_x[mask_neg], arc_y_neg[mask_neg], color=REACT_COLOR, linewidth=0.8, alpha=0.6, zorder=1)

    if x <= 2:
        ang = np.arctan(1 / x)
        lxp = 0.87 * np.cos(ang)
        lyp = 0.87 * np.sin(ang)
        ax.text(lxp, lyp + 0.03, f"x={x}", fontsize=8, color=REACT_COLOR, va="bottom", ha="center")
        ax.text(lxp, -lyp - 0.03, f"x=-{x}", fontsize=8, color=REACT_COLOR, va="top", ha="center")

# Unit circle boundary and real axis
ax.plot(np.cos(theta), np.sin(theta), color=INK_SOFT, linewidth=1.5, zorder=1)
ax.axhline(0, color=INK_SOFT, linewidth=1.0, alpha=0.6, zorder=1)

# VSWR circle: constant |Γ| = (VSWR - 1) / (VSWR + 1)
vswr_r = (VSWR - 1) / (VSWR + 1)
ax.plot(vswr_r * np.cos(theta), vswr_r * np.sin(theta), "--", color=VSWR_COLOR, linewidth=1.5, zorder=2)
ax.text(0.36, 0.37, f"VSWR {VSWR}:1", fontsize=8, color=VSWR_COLOR, fontweight="bold")

# Thin background line for trajectory continuity
ax.plot(locus["gamma_real"], locus["gamma_imag"], color=INK_SOFT, linewidth=1.2, alpha=0.4, zorder=4)

# Frequency-gradient scatter: seaborn continuous hue encoding with the Imprint sequential colormap,
# so the sweep direction reads from green (low) to blue (high).
sns.scatterplot(
    data=locus,
    x="gamma_real",
    y="gamma_imag",
    hue=FREQUENCY,
    palette=imprint_seq,
    hue_norm=(f_min, f_max),
    s=40,
    ax=ax,
    zorder=5,
    legend=False,
    edgecolor="none",
)

# Colorbar to decode frequency gradient
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=plt.Normalize(f_min, f_max))
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.5, aspect=20, pad=0.05)
cbar.set_label(FREQUENCY, fontsize=8, color=INK)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Key frequency markers, outlined in the page color for contrast against the gradient
key_pos = np.unique(np.linspace(0, len(locus) - 1, N_KEY_POINTS).astype(int))
markers = locus.iloc[key_pos]
sns.scatterplot(
    data=markers,
    x="gamma_real",
    y="gamma_imag",
    s=100,
    color=INK,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    ax=ax,
    zorder=10,
    legend=False,
)

# Frequency annotations: offsets in points, taken in order along the sweep
label_offsets = [(8, -18), (10, 8), (8, -14), (-45, 8), (-45, -12)]
for i, (_, row) in enumerate(markers.iterrows()):
    ox, oy = label_offsets[i % len(label_offsets)]
    ax.annotate(
        f"{row[FREQUENCY]:.1f} GHz",
        (row["gamma_real"], row["gamma_imag"]),
        textcoords="offset points",
        xytext=(ox, oy),
        fontsize=8,
        fontweight="bold",
        color=INK,
    )

# Center marker — matched condition Z = Z₀
ax.scatter([0], [0], s=80, color=INK, marker="+", linewidths=2, zorder=10)
ax.annotate("Z₀ (50 Ω)", (0, 0), textcoords="offset points", xytext=(-38, -14), fontsize=8, color=INK)

# Style
ax.set_xlim(-1.15, 1.15)
ax.set_ylim(-1.15, 1.15)
ax.set_aspect("equal")
ax.set_xlabel("Real(Γ)", fontsize=10, color=INK)
ax.set_ylabel("Imag(Γ)", fontsize=10, color=INK)
ax.set_title("smith-chart-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.grid(False)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Legend (locus entry replaced by colorbar above)
ax.plot([], [], color=INK_SOFT, linewidth=0.8, alpha=0.6, label="Constant R circles")
ax.plot([], [], color=REACT_COLOR, linewidth=0.8, alpha=0.6, label="Constant X arcs")
ax.plot([], [], color=VSWR_COLOR, linewidth=1.5, linestyle="--", label=f"VSWR {VSWR}:1 circle")
legend = ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)

plt.tight_layout()

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
