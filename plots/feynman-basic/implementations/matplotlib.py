"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-07
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


# Colors for each particle type
FERMION_COLOR = "#306998"
PHOTON_COLOR = "#D4442A"
GLUON_COLOR = "#E8871E"
BOSON_COLOR = "#7B4F9D"
VERTEX_COLOR = "#1a1a1a"

# Data - Two processes showcasing all 4 particle types
# Process 1 (top): QED e-e+ annihilation: e- + e+ -> gamma -> mu- + mu+
# Process 2 (bottom): Gluon fusion to Higgs: g + g -> H -> b + b-bar
vertices = {"v1": (0.28, 0.74), "v2": (0.72, 0.74), "v3": (0.28, 0.26), "v4": (0.72, 0.26)}

propagators = [
    # QED process: fermions + photon
    {"from": (0.04, 0.92), "to": "v1", "type": "fermion", "label": r"$e^-$", "arrow_fwd": True},
    {"from": (0.04, 0.56), "to": "v1", "type": "fermion", "label": r"$e^+$", "arrow_fwd": False},
    {"from": "v1", "to": "v2", "type": "photon", "label": r"$\gamma$"},
    {"from": "v2", "to": (0.96, 0.92), "type": "fermion", "label": r"$\mu^-$", "arrow_fwd": True},
    {"from": "v2", "to": (0.96, 0.56), "type": "fermion", "label": r"$\mu^+$", "arrow_fwd": False},
    # Gluon fusion: gluons + Higgs boson + fermions
    {"from": (0.04, 0.44), "to": "v3", "type": "gluon", "label": r"$g$"},
    {"from": (0.04, 0.08), "to": "v3", "type": "gluon", "label": r"$g$"},
    {"from": "v3", "to": "v4", "type": "boson", "label": r"$H$"},
    {"from": "v4", "to": (0.96, 0.44), "type": "fermion", "label": r"$b$", "arrow_fwd": True},
    {"from": "v4", "to": (0.96, 0.08), "type": "fermion", "label": r"$\bar{b}$", "arrow_fwd": False},
]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#F8F7F5")
ax.set_facecolor("#F8F7F5")
ax.set_xlim(-0.08, 1.08)
ax.set_ylim(-0.08, 1.08)

# Draw propagators
for prop in propagators:
    start = vertices[prop["from"]] if isinstance(prop["from"], str) else prop["from"]
    end = vertices[prop["to"]] if isinstance(prop["to"], str) else prop["to"]
    sx, sy = start
    ex, ey = end
    mx, my = (sx + ex) / 2, (sy + ey) / 2
    dx, dy = ex - sx, ey - sy
    length = np.sqrt(dx**2 + dy**2)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux

    if prop["type"] == "fermion":
        arrow_fwd = prop.get("arrow_fwd", True)
        if arrow_fwd:
            ax.annotate(
                "",
                xy=(ex, ey),
                xytext=(sx, sy),
                arrowprops={"arrowstyle": "-|>", "color": FERMION_COLOR, "lw": 3, "mutation_scale": 25},
            )
        else:
            ax.annotate(
                "",
                xy=(sx, sy),
                xytext=(ex, ey),
                arrowprops={"arrowstyle": "-|>", "color": FERMION_COLOR, "lw": 3, "mutation_scale": 25},
            )
        label_offset = 0.06
        ax.text(
            mx + px * label_offset,
            my + py * label_offset,
            prop["label"],
            fontsize=22,
            ha="center",
            va="center",
            color=FERMION_COLOR,
            fontweight="bold",
        )

    elif prop["type"] == "photon":
        t = np.linspace(0, 1, 500)
        n_waves = 8
        wave_amp = 0.035
        wave = wave_amp * np.sin(2 * np.pi * n_waves * t)
        envelope = np.sin(np.pi * t) ** 0.3
        wave *= envelope
        ax.plot(sx + t * dx + wave * px, sy + t * dy + wave * py, color=PHOTON_COLOR, lw=3, solid_capstyle="round")
        ax.text(
            mx - px * 0.07,
            my - py * 0.07,
            prop["label"],
            fontsize=22,
            ha="center",
            va="center",
            color=PHOTON_COLOR,
            fontweight="bold",
        )

    elif prop["type"] == "gluon":
        t = np.linspace(0, 1, 3000)
        n_coils = 9
        coil_r = 0.025
        phase = 2 * np.pi * n_coils * t
        # Prolate cycloid creates coiled/looped spring pattern
        along_mod = coil_r * 0.7 * np.sin(phase)
        perp_disp = coil_r * np.cos(phase)
        envelope = np.sin(np.pi * t) ** 0.4
        perp_disp *= envelope
        along_mod *= envelope
        gx = sx + t * dx - along_mod * ux + perp_disp * px
        gy = sy + t * dy - along_mod * uy + perp_disp * py
        ax.plot(gx, gy, color=GLUON_COLOR, lw=2.5, solid_capstyle="round")
        ax.text(
            mx + px * 0.06,
            my + py * 0.06,
            prop["label"],
            fontsize=22,
            ha="center",
            va="center",
            color=GLUON_COLOR,
            fontweight="bold",
        )

    elif prop["type"] == "boson":
        ax.plot([sx, ex], [sy, ey], color=BOSON_COLOR, lw=3, linestyle=(0, (8, 5)), dash_capstyle="round")
        ax.text(
            mx - px * 0.06,
            my - py * 0.06,
            prop["label"],
            fontsize=22,
            ha="center",
            va="center",
            color=BOSON_COLOR,
            fontweight="bold",
        )

# Vertices
for vx, vy in vertices.values():
    ax.plot(vx, vy, "o", color=VERTEX_COLOR, markersize=14, zorder=5)

# Subtle separator between the two processes
ax.axhline(y=0.50, xmin=0.05, xmax=0.95, color="#CCCCCC", lw=0.8, linestyle="--", alpha=0.6)

# Process labels
ax.text(0.005, 0.74, "QED", fontsize=14, ha="left", va="center", color="#999999", fontstyle="italic", rotation=90)
ax.text(0.005, 0.26, "QCD", fontsize=14, ha="left", va="center", color="#999999", fontstyle="italic", rotation=90)

# Style
ax.set_title(
    "feynman-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20, color="#333333"
)
ax.axis("off")

# Legend with all 4 particle types
legend_handles = [
    Line2D(
        [0],
        [0],
        color=FERMION_COLOR,
        lw=3,
        marker=">",
        markersize=8,
        markeredgecolor=FERMION_COLOR,
        label="Fermion (solid + arrow)",
    ),
    Line2D([0], [0], color=PHOTON_COLOR, lw=3, label="Photon (wavy)"),
    Line2D([0], [0], color=GLUON_COLOR, lw=3, label="Gluon (coiled)"),
    Line2D([0], [0], color=BOSON_COLOR, lw=3, linestyle="--", label="Boson (dashed)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=VERTEX_COLOR, markersize=10, lw=0, label="Vertex"),
]
ax.legend(
    handles=legend_handles, fontsize=15, loc="lower center", ncol=5, frameon=False, handlelength=2.5, columnspacing=1.5
)

# Time axis arrow
ax.annotate("", xy=(0.95, -0.04), xytext=(0.05, -0.04), arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.5})
ax.text(0.5, -0.065, "time", fontsize=16, ha="center", va="top", color="#888888", fontstyle="italic")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
