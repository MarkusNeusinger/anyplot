"""anyplot.ai — feynman-basic
Feynman Diagram for Particle Interactions
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome — Imprint palette
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — particle types (positions 1–4)
FERMION_COLOR = "#009E73"  # pos 1: brand green
PHOTON_COLOR = "#C475FD"  # pos 2: lavender
GLUON_COLOR = "#4467A3"  # pos 3: blue
BOSON_COLOR = "#BD8233"  # pos 4: ochre

# Two-process layout: top QED (e+e- annihilation), bottom QCD (gg -> H)
vertices = {"v1": (0.28, 0.74), "v2": (0.72, 0.74), "v3": (0.28, 0.26), "v4": (0.72, 0.26)}

propagators = [
    # QED: e-e+ -> gamma -> mu-mu+
    {"from": (0.04, 0.92), "to": "v1", "type": "fermion", "label": r"$e^-$", "arrow_fwd": True},
    {"from": (0.04, 0.56), "to": "v1", "type": "fermion", "label": r"$e^+$", "arrow_fwd": False},
    {"from": "v1", "to": "v2", "type": "photon", "label": r"$\gamma$"},
    {"from": "v2", "to": (0.96, 0.92), "type": "fermion", "label": r"$\mu^-$", "arrow_fwd": True},
    {"from": "v2", "to": (0.96, 0.56), "type": "fermion", "label": r"$\mu^+$", "arrow_fwd": False},
    # QCD: gg -> H -> bb-bar
    {"from": (0.04, 0.44), "to": "v3", "type": "gluon", "label": r"$g$"},
    {"from": (0.04, 0.08), "to": "v3", "type": "gluon", "label": r"$g$"},
    {"from": "v3", "to": "v4", "type": "boson", "label": r"$H$"},
    {"from": "v4", "to": (0.96, 0.44), "type": "fermion", "label": r"$b$", "arrow_fwd": True},
    {"from": "v4", "to": (0.96, 0.08), "type": "fermion", "label": r"$\bar{b}$", "arrow_fwd": False},
]

# Canvas: landscape 3200×1800 px (figsize=(8, 4.5), dpi=400)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_xlim(-0.08, 1.08)
ax.set_ylim(-0.08, 1.08)

for prop in propagators:
    start = vertices[prop["from"]] if isinstance(prop["from"], str) else prop["from"]
    end = vertices[prop["to"]] if isinstance(prop["to"], str) else prop["to"]
    sx, sy = start
    ex, ey = end
    mx, my = (sx + ex) / 2, (sy + ey) / 2
    dx, dy = ex - sx, ey - sy
    length = np.sqrt(dx**2 + dy**2)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux  # perpendicular unit vector

    if prop["type"] == "fermion":
        arrow_fwd = prop.get("arrow_fwd", True)
        if arrow_fwd:
            ax.annotate(
                "",
                xy=(ex, ey),
                xytext=(sx, sy),
                arrowprops={"arrowstyle": "-|>", "color": FERMION_COLOR, "lw": 2.5, "mutation_scale": 20},
            )
        else:
            ax.annotate(
                "",
                xy=(sx, sy),
                xytext=(ex, ey),
                arrowprops={"arrowstyle": "-|>", "color": FERMION_COLOR, "lw": 2.5, "mutation_scale": 20},
            )
        ax.text(
            mx + px * 0.06,
            my + py * 0.06,
            prop["label"],
            fontsize=14,
            ha="center",
            va="center",
            color=FERMION_COLOR,
            fontweight="bold",
        )

    elif prop["type"] == "photon":
        t = np.linspace(0, 1, 500)
        wave = 0.035 * np.sin(2 * np.pi * 8 * t) * np.sin(np.pi * t) ** 0.3
        ax.plot(sx + t * dx + wave * px, sy + t * dy + wave * py, color=PHOTON_COLOR, lw=2.5, solid_capstyle="round")
        ax.text(
            mx - px * 0.07,
            my - py * 0.07,
            prop["label"],
            fontsize=14,
            ha="center",
            va="center",
            color=PHOTON_COLOR,
            fontweight="bold",
        )

    elif prop["type"] == "gluon":
        t = np.linspace(0, 1, 3000)
        phase = 2 * np.pi * 9 * t
        envelope = np.sin(np.pi * t) ** 0.4
        along_mod = 0.025 * 0.7 * np.sin(phase) * envelope
        perp_disp = 0.025 * np.cos(phase) * envelope
        ax.plot(
            sx + t * dx - along_mod * ux + perp_disp * px,
            sy + t * dy - along_mod * uy + perp_disp * py,
            color=GLUON_COLOR,
            lw=2.0,
            solid_capstyle="round",
        )
        ax.text(
            mx + px * 0.06,
            my + py * 0.06,
            prop["label"],
            fontsize=14,
            ha="center",
            va="center",
            color=GLUON_COLOR,
            fontweight="bold",
        )

    elif prop["type"] == "boson":
        ax.plot([sx, ex], [sy, ey], color=BOSON_COLOR, lw=2.5, linestyle=(0, (8, 5)), dash_capstyle="round")
        ax.text(
            mx - px * 0.06,
            my - py * 0.06,
            prop["label"],
            fontsize=14,
            ha="center",
            va="center",
            color=BOSON_COLOR,
            fontweight="bold",
        )

# Vertex dots (theme-adaptive ink)
for vx, vy in vertices.values():
    ax.plot(vx, vy, "o", color=INK, markersize=10, zorder=5)

# Separator between QED and QCD processes
ax.axhline(y=0.50, xmin=0.05, xmax=0.95, color=INK_MUTED, lw=0.8, linestyle="--", alpha=0.5)

# Process labels
ax.text(0.005, 0.74, "QED", fontsize=9, ha="left", va="center", color=INK_MUTED, fontstyle="italic", rotation=90)
ax.text(0.005, 0.26, "QCD", fontsize=9, ha="left", va="center", color=INK_MUTED, fontstyle="italic", rotation=90)

# Time arrow (inside axes area, above legend)
ax.annotate("", xy=(0.95, -0.03), xytext=(0.05, -0.03), arrowprops={"arrowstyle": "->", "color": INK_MUTED, "lw": 1.2})
ax.text(0.5, -0.05, "time", fontsize=9, ha="center", va="top", color=INK_MUTED, fontstyle="italic")

# Title (48 chars < 67 threshold — default 12pt)
ax.set_title("feynman-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", pad=10, color=INK)
ax.axis("off")

# Legend (frameless for minimal aesthetic)
legend_handles = [
    Line2D(
        [0],
        [0],
        color=FERMION_COLOR,
        lw=2.5,
        marker=">",
        markersize=6,
        markeredgecolor=FERMION_COLOR,
        label="Fermion (solid + arrow)",
    ),
    Line2D([0], [0], color=PHOTON_COLOR, lw=2.5, label="Photon (wavy)"),
    Line2D([0], [0], color=GLUON_COLOR, lw=2.0, label="Gluon (coiled)"),
    Line2D([0], [0], color=BOSON_COLOR, lw=2.5, linestyle="--", label="Boson (dashed)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=INK, markersize=7, lw=0, label="Vertex"),
]
leg = ax.legend(
    handles=legend_handles,
    fontsize=8,
    loc="lower center",
    ncol=5,
    frameon=False,
    handlelength=2.5,
    columnspacing=1.5,
    bbox_to_anchor=(0.5, 0.0),
    bbox_transform=ax.transAxes,
)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Reserve bottom 8% of figure for legend below the axes
plt.tight_layout(rect=[0, 0.08, 1, 1])
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
