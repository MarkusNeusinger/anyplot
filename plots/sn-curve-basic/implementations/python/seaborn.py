"""anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # data & fit
C_ULTIMATE = IMPRINT_PALETTE[1]  # Ultimate Strength
C_YIELD = IMPRINT_PALETTE[2]  # Yield Strength
C_ENDURANCE = IMPRINT_PALETTE[3]  # Endurance Limit

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

# Constants: material properties and axis domain of the structural steel example
ULTIMATE_STRENGTH = 450  # MPa
YIELD_STRENGTH = 350  # MPa
ENDURANCE_LIMIT = 200  # MPa
CYCLES_LIMITS = (1e3, 5e7)
STRESS_LIMITS = (150, 600)
N_BOOT = 250  # bootstrap resamples for the prediction interval

# Columns: set these to your table's column names
CYCLES = "Number of Cycles to Failure (N)"  # role: cycles
STRESS = "Stress Amplitude (MPa)"  # role: stress

# Data: replace this block with your own table, for example df = pd.read_csv("fatigue_tests.csv")
# Structural steel fatigue tests, several specimens per stress level (Basquin equation)
np.random.seed(42)
stress_levels = np.array([400, 350, 320, 300, 280, 260, 240, 220, 210, 205])
basquin_a = 1200  # Basquin material constant
basquin_b = -0.12  # Basquin exponent

cycles_list = []
stress_list = []
for level in stress_levels:
    n_specimens = np.random.randint(3, 6)
    base_cycles = (level / basquin_a) ** (1 / basquin_b)
    cycles_list.extend(base_cycles * np.random.lognormal(0, 0.3, n_specimens))
    stress_list.extend([level] * n_specimens)

df = pd.DataFrame({CYCLES: cycles_list, STRESS: stress_list})

# Plot: reads only df and the constants above
# Bootstrap S-N fits for seaborn CI band — seaborn-distinctive statistical layer
fit_cycles_grid = np.logspace(np.log10(CYCLES_LIMITS[0]), 7.7, 25)
valid = df.dropna(subset=[CYCLES, STRESS])
cycles_arr = valid[CYCLES].to_numpy(dtype=float)
stress_arr = valid[STRESS].to_numpy(dtype=float)
stress_floor, stress_ceiling = stress_arr.min() / 2, stress_arr.max() * 2.5  # plausible extrapolation range
boot_rows = []
for _ in range(N_BOOT):
    idx = np.random.choice(len(cycles_arr), len(cycles_arr), replace=True)
    coeffs = np.polyfit(np.log10(cycles_arr[idx]), np.log10(stress_arr[idx]), 1)
    for c in fit_cycles_grid:
        s = 10 ** (coeffs[0] * np.log10(c) + coeffs[1])
        if stress_floor < s < stress_ceiling:
            boot_rows.append({CYCLES: c, STRESS: s})

boot_df = pd.DataFrame(boot_rows)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Infinite life region: subtle shading below endurance limit
ax.axhspan(STRESS_LIMITS[0], ENDURANCE_LIMIT, alpha=0.07, color=C_ENDURANCE, zorder=0)

# S-N fit line with 95% prediction interval — seaborn statistical CI band
sns.lineplot(
    data=boot_df,
    x=CYCLES,
    y=STRESS,
    estimator="mean",
    errorbar=("pi", 95),
    color=BRAND,
    linewidth=2.5,
    ax=ax,
    label="S-N Curve Fit (95% PI)",
    err_kws={"alpha": 0.18},
    zorder=3,
)

# Test data scatter
sns.scatterplot(
    data=df, x=CYCLES, y=STRESS, s=130, color=BRAND, alpha=0.75, edgecolor="none", ax=ax, zorder=5, label="Test Data"
)

# Reference lines — endurance limit thicker and solid as critical design threshold
ax.axhline(
    y=ULTIMATE_STRENGTH,
    color=C_ULTIMATE,
    linewidth=1.8,
    linestyle="--",
    label=f"Ultimate Strength ({ULTIMATE_STRENGTH} MPa)",
)
ax.axhline(
    y=YIELD_STRENGTH, color=C_YIELD, linewidth=1.8, linestyle="--", label=f"Yield Strength ({YIELD_STRENGTH} MPa)"
)
ax.axhline(
    y=ENDURANCE_LIMIT,
    color=C_ENDURANCE,
    linewidth=2.8,
    linestyle="-",
    label=f"Endurance Limit ({ENDURANCE_LIMIT} MPa)",
    zorder=4,
)

# Style
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(*CYCLES_LIMITS)
ax.set_ylim(*STRESS_LIMITS)

ax.set_xlabel(CYCLES, fontsize=10, fontweight="medium", color=INK)
ax.set_ylabel(STRESS, fontsize=10, fontweight="medium", color=INK)
ax.set_title("sn-curve-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

# Major gridlines stronger than minor — which='both' on log scale generates ~18 lines per axis
ax.grid(True, alpha=0.10, linewidth=0.8, color=INK, which="major")
ax.grid(True, alpha=0.04, linewidth=0.4, color=INK, which="minor")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.legend(loc="lower left", fontsize=8, framealpha=0.95, facecolor=ELEVATED_BG, edgecolor=INK_SOFT)

# Controlled margins — avoids bbox_inches='tight' canvas drift
fig.subplots_adjust(left=0.12, right=0.97, top=0.93, bottom=0.13)

# Save — bbox_inches must stay default (None) to preserve 3200×1800 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
