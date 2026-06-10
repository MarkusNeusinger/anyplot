"""anyplot.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-06-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens — see default-style-guide.md "Theme-adaptive Chrome"
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — semantic exception applied:
# #009E73 (brand green) = normal/healthy curve; #AE3030 (matte red) = inverted/recession signal
BRAND = "#009E73"  # Jan 2022 normal curve — Imprint position 1
INVERTED_COLOR = "#AE3030"  # Oct 2023 inverted curve — semantic red (recession indicator)
NORM_COLOR = "#4467A3"  # Jan 2025 normalizing curve — Imprint position 3

# Data — U.S. Treasury yield curves across three monetary-policy regimes
maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = np.array([1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])

# Normal upward-sloping curve (Jan 2022) — pre-hiking cycle
yields_normal = np.array([0.08, 0.21, 0.47, 0.78, 1.18, 1.42, 1.72, 1.90, 1.93, 2.28, 2.25])

# Inverted curve (Oct 2023) — peak-rate environment, recession signal
yields_inverted = np.array([5.54, 5.55, 5.52, 5.46, 5.05, 4.80, 4.62, 4.65, 4.73, 5.07, 4.95])

# Normalizing curve (Jan 2025) — Fed pivoting, curve re-steepening
yields_normalizing = np.array([4.36, 4.34, 4.32, 4.22, 4.20, 4.23, 4.38, 4.47, 4.58, 4.85, 4.84])

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

curves = [
    (yields_normal, BRAND, "Jan 2022 (Normal)"),
    (yields_inverted, INVERTED_COLOR, "Oct 2023 (Inverted)"),
    (yields_normalizing, NORM_COLOR, "Jan 2025 (Normalizing)"),
]

for yields, color, label in curves:
    ax.plot(
        maturity_years,
        yields,
        color=color,
        linewidth=2.5,
        label=label,
        marker="o",
        markersize=5,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1.0,
    )

# Shade inversion region: from 3M peak (5.55%) down to 5Y trough
trough_idx = 6  # index of 5Y maturity
ax.fill_between(
    maturity_years[: trough_idx + 1],
    yields_inverted[: trough_idx + 1],
    yields_inverted[1],  # 3M peak = 5.55%
    alpha=0.10,
    color=INVERTED_COLOR,
)

# Annotation highlighting the inversion
ax.annotate(
    "Yield curve inversion",
    xy=(3, 4.80),
    xytext=(8, 5.50),
    fontsize=8,
    color=INVERTED_COLOR,
    fontweight="medium",
    arrowprops={"arrowstyle": "->", "color": INVERTED_COLOR, "lw": 1.2},
)

# Style
title = "line-yield-curve · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

ax.set_xlabel("Maturity", fontsize=10, color=INK)
ax.set_ylabel("Yield (%)", fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)

ax.set_xscale("log")
ax.set_xticks(maturity_years)
ax.set_xticklabels(maturities)
ax.minorticks_off()
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT, length=0)
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT, length=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, frameon=True, loc="lower right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.97, top=0.93, bottom=0.12)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
