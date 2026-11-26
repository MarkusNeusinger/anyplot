"""anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-20
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, LogLocator
from matplotlib.transforms import blended_transform_factory


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: typical values for an aluminium alloy (MPa)
ULTIMATE_STRENGTH = 330
YIELD_STRENGTH = 280
ENDURANCE_LIMIT = 80

# Columns: set these to your table's column names
CYCLES = "Number of Cycles to Failure (N)"  # role: cycles
STRESS = "Stress Amplitude (MPa)"  # role: stress

# Data: replace this block with your own table, for example df = pd.read_csv("fatigue_tests.csv")
rng = np.random.default_rng(7)
stress_levels = [250, 220, 190, 165, 145, 125, 110, 100, 92]
basquin_a, basquin_b = 480, 0.1
rows = []
for level in stress_levels:
    n_mean = (level / basquin_a) ** (-1 / basquin_b)
    for _ in range(rng.integers(2, 5)):
        rows.append((n_mean * np.exp(rng.normal(0, 0.3)), level + rng.normal(0, 3)))
df = pd.DataFrame(rows, columns=[CYCLES, STRESS])

# Plot: reads only df and the constants above
cycles = df[CYCLES].to_numpy()
stress = df[STRESS].to_numpy()

# Basquin fit on log-log axes, drawn only while it stays above the endurance limit
valid = np.isfinite(cycles) & np.isfinite(stress)
slope, intercept = np.polyfit(np.log10(cycles[valid]), np.log10(stress[valid]), 1)
x_lo = 10 ** np.floor(np.log10(np.nanmin(cycles)))
x_hi = 10 ** np.ceil(np.log10(np.nanmax(cycles)))
fit_cycles = np.logspace(np.log10(x_lo), np.log10(x_hi), 200)
fit_stress = 10 ** (slope * np.log10(fit_cycles) + intercept)
above_limit = fit_stress >= ENDURANCE_LIMIT
fit_cycles, fit_stress = fit_cycles[above_limit], fit_stress[above_limit]

y_lo = min(np.nanmin(stress), ENDURANCE_LIMIT) * 0.75
y_hi = ULTIMATE_STRENGTH * 1.4

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Fatigue region shading: stronger on the dark page so the bands stay visible
shade = 1.0 if THEME == "light" else 1.6
ax.axhspan(y_lo, ENDURANCE_LIMIT, alpha=0.07 * shade, color=IMPRINT_PALETTE[0], zorder=0)
ax.axhspan(ENDURANCE_LIMIT, YIELD_STRENGTH, alpha=0.05 * shade, color=IMPRINT_PALETTE[1], zorder=0)
ax.axhspan(YIELD_STRENGTH, y_hi, alpha=0.05 * shade, color=IMPRINT_PALETTE[2], zorder=0)

ax.scatter(
    cycles,
    stress,
    s=100,
    color=IMPRINT_PALETTE[0],
    alpha=0.75,
    edgecolors=PAGE_BG,
    linewidths=0.5,
    label="Test Data",
    zorder=5,
)
ax.plot(fit_cycles, fit_stress, color=IMPRINT_PALETTE[1], linewidth=2.0, label="Basquin Fit", zorder=4)

ax.axhline(
    ULTIMATE_STRENGTH,
    color=IMPRINT_PALETTE[2],
    linestyle="--",
    linewidth=1.5,
    label=f"Ultimate Strength ({ULTIMATE_STRENGTH} MPa)",
    zorder=3,
)
ax.axhline(
    YIELD_STRENGTH,
    color=IMPRINT_PALETTE[3],
    linestyle="--",
    linewidth=1.5,
    label=f"Yield Strength ({YIELD_STRENGTH} MPa)",
    zorder=3,
)
ax.axhline(
    ENDURANCE_LIMIT,
    color=IMPRINT_PALETTE[4],
    linestyle="--",
    linewidth=2.5,
    label=f"Endurance Limit ({ENDURANCE_LIMIT} MPa)",
    zorder=3,
)

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(x_lo, x_hi)
ax.set_ylim(y_lo, y_hi)
ax.xaxis.grid(False)

# Style
ax.set_xlabel(CYCLES, fontsize=10, color=INK)
ax.set_ylabel(STRESS, fontsize=10, color=INK)
ax.set_title("sn-curve-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 3, 5)))
ax.yaxis.set_minor_locator(LogLocator(base=10, subs=()))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
ax.yaxis.grid(True, which="major", alpha=0.15, linewidth=0.7, color=INK)

leg = ax.legend(fontsize=8, loc="lower left", bbox_to_anchor=(0.01, 0.2))
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Fatigue region labels: x in axes fraction, y just inside each band
REGION_BBOX = {"boxstyle": "round,pad=0.2", "facecolor": PAGE_BG, "alpha": 0.75, "edgecolor": "none"}
for x_frac, label, y_pos in [
    (0.14, "Low-Cycle Fatigue", ULTIMATE_STRENGTH * 1.05),
    (0.50, "High-Cycle Fatigue", ULTIMATE_STRENGTH * 1.05),
    (0.88, "Infinite Life", ENDURANCE_LIMIT * 0.86),
]:
    ax.text(
        x_frac,
        y_pos,
        label,
        transform=blended_transform_factory(ax.transAxes, ax.transData),
        fontsize=8,
        ha="center",
        va="bottom" if y_pos > ENDURANCE_LIMIT else "top",
        color=INK_MUTED,
        style="italic",
        bbox=REGION_BBOX,
    )

plt.tight_layout()

# Save: no bbox_inches="tight" to keep the exact 3200×1800 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
