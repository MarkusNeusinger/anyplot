"""anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: matplotlib | Python 3.13
Quality: 94/100 | Updated: 2026-05-19
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # Okabe-Ito #1 — test data points
COLOR_FIT = "#D55E00"  # Okabe-Ito #2 — Basquin fit line
COLOR_ULT = "#0072B2"  # Okabe-Ito #3 — Ultimate Strength
COLOR_YLD = "#CC79A7"  # Okabe-Ito #4 — Yield Strength
COLOR_END = "#E69F00"  # Okabe-Ito #5 — Endurance Limit

# Data: Simulated fatigue test results for structural steel specimens
np.random.seed(42)

stress_levels = np.array([450, 400, 350, 320, 300, 280, 260, 250, 240, 230, 220, 210])

cycles_data = []
stress_data = []

for s_level in stress_levels:
    # Basquin equation: N = (S/A)^(-1/b)
    A, b = 1200, 0.12
    N_mean = (s_level / A) ** (-1 / b)
    n_samples = np.random.randint(2, 5)
    for _ in range(n_samples):
        cycle_scatter = np.exp(np.random.normal(0, 0.3))
        cycles_data.append(N_mean * cycle_scatter)
        stress_data.append(s_level + np.random.normal(0, 5))

cycles = np.array(cycles_data)
stress = np.array(stress_data)

# Basquin log-linear fit
coeffs = np.polyfit(np.log10(cycles), np.log10(stress), 1)
fit_cycles = np.logspace(2, 8, 100)
fit_stress = 10 ** (coeffs[0] * np.log10(fit_cycles) + coeffs[1])

# Material property reference values (typical structural steel, MPa)
ultimate_strength = 500
yield_strength = 350
endurance_limit = 200

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.scatter(
    cycles, stress, s=80, color=BRAND, alpha=0.75, edgecolors=PAGE_BG, linewidths=0.5, label="Test Data", zorder=5
)

ax.plot(fit_cycles, fit_stress, color=COLOR_FIT, linewidth=2.0, label="Basquin Fit", zorder=4)

ax.axhline(
    y=ultimate_strength,
    color=COLOR_ULT,
    linestyle="--",
    linewidth=1.5,
    label=f"Ultimate Strength ({ultimate_strength} MPa)",
    zorder=3,
)
ax.axhline(
    y=yield_strength,
    color=COLOR_YLD,
    linestyle="--",
    linewidth=1.5,
    label=f"Yield Strength ({yield_strength} MPa)",
    zorder=3,
)
ax.axhline(
    y=endurance_limit,
    color=COLOR_END,
    linestyle="--",
    linewidth=1.5,
    label=f"Endurance Limit ({endurance_limit} MPa)",
    zorder=3,
)

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(1e2, 1e8)
ax.set_ylim(150, 650)

# Style
ax.set_xlabel("Number of Cycles to Failure (N)", fontsize=10, color=INK)
ax.set_ylabel("Stress Amplitude (MPa)", fontsize=10, color=INK)
ax.set_title("sn-curve-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.grid(True, which="major", alpha=0.12, linewidth=0.6, color=INK)
ax.grid(True, which="minor", alpha=0.06, linewidth=0.4, color=INK)

leg = ax.legend(fontsize=8, loc="upper right")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Fatigue region labels
ax.annotate("Low-Cycle\nFatigue", xy=(4e2, 420), fontsize=7, ha="center", color=INK_MUTED, style="italic")
ax.annotate("High-Cycle\nFatigue", xy=(1e5, 290), fontsize=7, ha="center", color=INK_MUTED, style="italic")
ax.annotate("Infinite Life", xy=(5e7, 170), fontsize=7, ha="center", color=INK_MUTED, style="italic")

plt.tight_layout()

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
