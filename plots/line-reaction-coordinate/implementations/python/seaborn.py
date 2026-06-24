"""anyplot.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-06-24
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.interpolate import PchipInterpolator


# Theme tokens — Imprint palette
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Imprint position 1 — first (and only) data series
EA_COLOR = "#AE3030"  # Imprint position 5 — semantic red for activation barrier
DH_COLOR = "#4467A3"  # Imprint position 3 — blue for enthalpy change

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
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — single-step exothermic reaction: Ea = 70 kJ/mol, ΔH = −30 kJ/mol
reactant_energy = 50.0
transition_energy = 120.0
product_energy = 20.0

control_x = np.array([0.0, 0.12, 0.22, 0.35, 0.47, 0.59, 0.72, 0.82, 0.90, 1.0])
control_y = np.array(
    [
        reactant_energy,
        reactant_energy,
        reactant_energy + 2,
        85,
        transition_energy,
        85,
        product_energy + 5,
        product_energy,
        product_energy,
        product_energy,
    ]
)

reaction_coord = np.linspace(0, 1, 500)
spline = PchipInterpolator(control_x, control_y)
energy = spline(reaction_coord)

df = pd.DataFrame({"Reaction Coordinate": reaction_coord, "Potential Energy (kJ/mol)": energy})

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(
    data=df, x="Reaction Coordinate", y="Potential Energy (kJ/mol)", color=BRAND, linewidth=2.5, ax=ax, zorder=3
)

ax.fill_between(reaction_coord, energy, alpha=0.08, color=BRAND, zorder=2)

# Horizontal dashed reference lines at reactant and product energy levels
ax.hlines(reactant_energy, xmin=-0.02, xmax=0.18, color=INK_SOFT, linestyle="--", linewidth=1.2, alpha=0.6)
ax.hlines(product_energy, xmin=0.82, xmax=1.02, color=INK_SOFT, linestyle="--", linewidth=1.2, alpha=0.6)

# Species labels — direct annotation on chart
ax.text(0.02, reactant_energy + 3, "Reactants\n(50 kJ/mol)", fontsize=9, fontweight="bold", color=INK, va="bottom")
ax.text(
    0.98, product_energy - 3, "Products\n(20 kJ/mol)", fontsize=9, fontweight="bold", color=INK, va="top", ha="right"
)
ax.text(
    0.47,
    transition_energy + 2,
    "Transition State\n(120 kJ/mol)",
    fontsize=9,
    fontweight="bold",
    color=INK,
    va="bottom",
    ha="center",
)

# Activation energy arrow (Ea)
ea_x = 0.13
ax.annotate(
    "",
    xy=(ea_x, transition_energy),
    xytext=(ea_x, reactant_energy),
    arrowprops={"arrowstyle": "<->", "color": EA_COLOR, "lw": 2.0, "shrinkA": 0, "shrinkB": 0},
)
ax.text(
    ea_x - 0.02,
    (reactant_energy + transition_energy) / 2,
    f"$E_a$ = {transition_energy - reactant_energy:.0f} kJ/mol",
    fontsize=8,
    color=EA_COLOR,
    fontweight="bold",
    ha="right",
    va="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.9},
)

# Enthalpy change arrow (ΔH)
dh_x = 0.82
ax.annotate(
    "",
    xy=(dh_x, product_energy),
    xytext=(dh_x, reactant_energy),
    arrowprops={"arrowstyle": "<->", "color": DH_COLOR, "lw": 2.0, "shrinkA": 0, "shrinkB": 0},
)
ax.text(
    dh_x - 0.02,
    (reactant_energy + product_energy) / 2,
    f"$\\Delta H$ = {product_energy - reactant_energy:.0f} kJ/mol",
    fontsize=8,
    color=DH_COLOR,
    fontweight="bold",
    ha="right",
    va="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.9},
)

# Style
title = "line-reaction-coordinate · python · seaborn · anyplot.ai"
ax.set_xlabel("Reaction Coordinate", fontsize=10, color=INK)
ax.set_ylabel("Potential Energy (kJ/mol)", fontsize=10, color=INK)
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(0, 145)
ax.set_xticks([])
ax.xaxis.grid(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
