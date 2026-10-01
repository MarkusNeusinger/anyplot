"""anyplot.ai
line-tanabe-sugano: Tanabe-Sugano Diagram for Crystal Field Theory
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-10-01
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
SPIN_ALLOWED = "#009E73"  # Imprint palette position 1 — ALWAYS first series
SPIN_FORBIDDEN = "#C475FD"  # Imprint palette position 2

# Data — octahedral Tanabe-Sugano matrices for d² (V³⁺), energies in units of the
# Racah parameter B with the Racah A dropped as an additive constant. Each block
# holds the terms of one symmetry; diagonalizing it gives the avoided crossings.
c_over_b = 4.5
field_strength = np.linspace(0.0, 40.0, 361)  # Δ_o / B
flat = np.ones_like(field_strength)
off_e = 2 * np.sqrt(3) * flat
off_a1 = np.sqrt(6) * (2 + c_over_b) * flat

blocks = [
    (["$^{3}T_{1g}(F)$", "$^{3}T_{1g}(P)$"], True, [[-5 * flat, 6 * flat], [6 * flat, 4 + field_strength]]),
    (["$^{3}T_{2g}$"], True, [[-8 + field_strength]]),
    (["$^{3}A_{2g}$"], True, [[-8 + 2 * field_strength]]),
    (
        ["$^{1}E_{g}(D)$", "$^{1}E_{g}(G)$"],
        False,
        [[(1 + 2 * c_over_b) * flat, off_e], [off_e, 2 * c_over_b + 2 * field_strength]],
    ),
    (
        ["$^{1}T_{2g}(D)$", "$^{1}T_{2g}(G)$"],
        False,
        [[(1 + 2 * c_over_b) * flat, off_e], [off_e, 2 * c_over_b + field_strength]],
    ),
    (["$^{1}T_{1g}$"], False, [[4 + 2 * c_over_b + field_strength]]),
    (
        ["$^{1}A_{1g}(G)$", "$^{1}A_{1g}(S)$"],
        False,
        [[(8 + 4 * c_over_b) * flat, off_a1], [off_a1, 10 + 5 * c_over_b + 2 * field_strength]],
    ),
]

terms = []
for labels, spin_allowed, rows in blocks:
    roots = np.linalg.eigvalsh(np.moveaxis(np.array(rows), -1, 0))
    for root, label in zip(roots.T, labels, strict=True):
        terms.append((label, spin_allowed, root))

ground_energy = np.min([root for _, _, root in terms], axis=0)

# Plot — square canvas, near-square plot area with a gutter for the term labels
field_max, energy_max = 40.0, 80.0
label_nudge = {"$^{3}T_{1g}(F)$": 2.6, "$^{1}E_{g}(D)$": 2.5, "$^{1}T_{2g}(D)$": -2.5}

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.095, right=0.975, bottom=0.085, top=0.90)

for label, spin_allowed, root in terms:
    reduced_energy = root - ground_energy
    ax.plot(
        field_strength,
        reduced_energy,
        color=SPIN_ALLOWED if spin_allowed else SPIN_FORBIDDEN,
        linewidth=2.8 if spin_allowed else 1.4,
        linestyle="-" if spin_allowed else (0, (5, 3)),
        zorder=3,
    )
    # Term label with a leader line, at the right edge or where the curve leaves the frame
    last = np.flatnonzero(reduced_energy <= energy_max)[-1]
    if last == field_strength.size - 1:
        anchor = (field_max, reduced_energy[-1])
        text_at = (field_max + 1.6, reduced_energy[-1] + label_nudge.get(label, 0.0))
        ha, va = "left", "center"
    else:
        anchor = (field_strength[last], energy_max)
        text_at = (field_strength[last] - 2.2, energy_max - 0.5)
        ha, va = "right", "top"
    ax.annotate(
        label,
        xy=anchor,
        xytext=text_at,
        ha=ha,
        va=va,
        fontsize=9,
        color=INK,
        arrowprops={"arrowstyle": "-", "linewidth": 0.7, "color": INK_SOFT, "shrinkA": 2},
    )

# Style
ax.set_xlim(0, 46.5)
ax.set_ylim(0, energy_max)
ax.set_xticks(np.arange(0, 41, 10))
ax.set_yticks(np.arange(0, 81, 20))
ax.set_xlabel("Ligand-Field Strength  $\\Delta_o/B$", fontsize=10, color=INK)
ax.set_ylabel("Term Energy  $E/B$", fontsize=10, color=INK)
ax.set_title(
    "line-tanabe-sugano · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=26
)
ax.text(
    0.5,
    1.012,
    "$d^{2}$ (V$^{3+}$) in an octahedral field, $C/B$ = 4.5",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=10,
    color=INK_SOFT,
)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.set_axisbelow(True)
ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)

handles = [
    Line2D([], [], color=SPIN_ALLOWED, linewidth=2.8, label="Spin-allowed (triplet)"),
    Line2D([], [], color=SPIN_FORBIDDEN, linewidth=1.4, linestyle=(0, (5, 3)), label="Spin-forbidden (singlet)"),
]
legend = ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(0.865, 0.02), fontsize=8)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
plt.setp(legend.get_texts(), color=INK_SOFT)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
