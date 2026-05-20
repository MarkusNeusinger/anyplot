""" anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito pos 1 — data points & fit line
C2 = "#D55E00"  # Okabe-Ito pos 2 — Ultimate Strength
C3 = "#0072B2"  # Okabe-Ito pos 3 — Yield Strength
C4 = "#CC79A7"  # Okabe-Ito pos 4 — Endurance Limit

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
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data — structural steel fatigue test (Basquin equation)
np.random.seed(42)

ultimate_strength = 450
yield_strength = 350
endurance_limit = 200

stress_levels = np.array([400, 350, 320, 300, 280, 260, 240, 220, 210, 205])

A = 1200  # material constant
b = -0.12  # Basquin exponent

cycles_list = []
stress_list = []

for stress in stress_levels:
    n_specimens = np.random.randint(3, 6)
    base_cycles = (stress / A) ** (1 / b)
    scatter = np.random.lognormal(0, 0.3, n_specimens)
    cycles = base_cycles * scatter
    cycles_list.extend(cycles)
    stress_list.extend([stress] * n_specimens)

cycles = np.array(cycles_list)
stress_arr = np.array(stress_list)

fit_stress = np.linspace(205, 420, 100)
fit_cycles = (fit_stress / A) ** (1 / b)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.scatterplot(x=cycles, y=stress_arr, s=100, color=BRAND, alpha=0.7, edgecolor="none", ax=ax, label="Test Data")
ax.plot(fit_cycles, fit_stress, color=BRAND, linewidth=2.5, linestyle="-", label="S-N Curve Fit")

ax.axhline(
    y=ultimate_strength, color=C2, linewidth=2, linestyle="--", label=f"Ultimate Strength ({ultimate_strength} MPa)"
)
ax.axhline(y=yield_strength, color=C3, linewidth=2, linestyle="--", label=f"Yield Strength ({yield_strength} MPa)")
ax.axhline(y=endurance_limit, color=C4, linewidth=2, linestyle="--", label=f"Endurance Limit ({endurance_limit} MPa)")

# Style
ax.set_xscale("log")
ax.set_yscale("log")

ax.set_xlim(1e3, 1e8)
ax.set_ylim(150, 600)

ax.set_xlabel("Number of Cycles to Failure (N)", fontsize=10, color=INK)
ax.set_ylabel("Stress Amplitude (MPa)", fontsize=10, color=INK)
ax.set_title("sn-curve-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.grid(True, alpha=0.10, linewidth=0.8, color=INK, which="both")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.legend(loc="lower left", fontsize=8, framealpha=0.95, facecolor=ELEVATED_BG, edgecolor=INK_SOFT)

plt.tight_layout()

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
