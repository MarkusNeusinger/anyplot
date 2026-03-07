"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Electron-positron annihilation: e- + e+ -> gamma -> mu- + mu+
vertices = {"v1": (0.25, 0.5), "v2": (0.75, 0.5)}

propagators = [
    {"from": (0.0, 0.85), "to": "v1", "type": "fermion", "label": r"$e^-$", "arrow_forward": True},
    {"from": (0.0, 0.15), "to": "v1", "type": "fermion", "label": r"$e^+$", "arrow_forward": False},
    {"from": "v1", "to": "v2", "type": "photon", "label": r"$\gamma$"},
    {"from": "v2", "to": (1.0, 0.85), "type": "fermion", "label": r"$\mu^-$", "arrow_forward": True},
    {"from": "v2", "to": (1.0, 0.15), "type": "fermion", "label": r"$\mu^+$", "arrow_forward": False},
]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
ax.set_xlim(-0.12, 1.12)
ax.set_ylim(-0.05, 1.05)
ax.set_aspect("equal")

for prop in propagators:
    start = vertices[prop["from"]] if isinstance(prop["from"], str) else prop["from"]
    end = vertices[prop["to"]] if isinstance(prop["to"], str) else prop["to"]
    sx, sy = start
    ex, ey = end
    mx, my = (sx + ex) / 2, (sy + ey) / 2
    dx, dy = ex - sx, ey - sy

    if prop["type"] == "fermion":
        arrow_forward = prop.get("arrow_forward", True)
        if arrow_forward:
            ax.annotate(
                "",
                xy=(ex, ey),
                xytext=(sx, sy),
                arrowprops={"arrowstyle": "-|>", "color": "#306998", "lw": 3, "mutation_scale": 25},
            )
        else:
            ax.annotate(
                "",
                xy=(sx, sy),
                xytext=(ex, ey),
                arrowprops={"arrowstyle": "-|>", "color": "#306998", "lw": 3, "mutation_scale": 25},
            )

        offset_x = -dy * 0.06
        offset_y = dx * 0.06
        ax.text(
            mx + offset_x,
            my + offset_y,
            prop["label"],
            fontsize=22,
            ha="center",
            va="center",
            color="#306998",
            fontweight="bold",
        )

    elif prop["type"] == "photon":
        length = np.sqrt(dx**2 + dy**2)
        t = np.linspace(0, 1, 500)
        wave_amp = 0.035
        n_waves = 8

        base_x = sx + t * dx
        base_y = sy + t * dy
        perp_x, perp_y = -dy / length, dx / length

        wave = wave_amp * np.sin(2 * np.pi * n_waves * t)
        envelope = np.sin(np.pi * t) ** 0.3
        wave *= envelope

        ax.plot(base_x + wave * perp_x, base_y + wave * perp_y, color="#D4442A", lw=3, solid_capstyle="round")
        ax.text(
            mx - perp_x * 0.07,
            my - perp_y * 0.07,
            prop["label"],
            fontsize=22,
            ha="center",
            va="center",
            color="#D4442A",
            fontweight="bold",
        )

for vx, vy in vertices.values():
    ax.plot(vx, vy, "o", color="#1a1a1a", markersize=14, zorder=5)

# Style
ax.set_title("feynman-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.axis("off")

fermion_patch = plt.Line2D([0], [0], color="#306998", lw=3, label="Fermion (solid + arrow)")
photon_patch = plt.Line2D([0], [0], color="#D4442A", lw=3, label="Photon (wavy)")
vertex_patch = plt.Line2D(
    [0], [0], marker="o", color="w", markerfacecolor="#1a1a1a", markersize=10, lw=0, label="Vertex"
)
ax.legend(handles=[fermion_patch, photon_patch, vertex_patch], fontsize=16, loc="lower center", ncol=3, frameon=False)

ax.annotate("", xy=(0.95, -0.02), xytext=(0.05, -0.02), arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.5})
ax.text(0.5, -0.05, "time", fontsize=16, ha="center", va="top", color="#888888", style="italic")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
