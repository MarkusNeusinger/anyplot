"""pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - U.S. Treasury yield curves on three dates
maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = np.array([1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])

# Normal upward-sloping curve (Jan 2022)
yields_normal = np.array([0.08, 0.21, 0.47, 0.78, 1.18, 1.42, 1.72, 1.90, 1.93, 2.28, 2.25])

# Inverted curve (Oct 2023) - short-term rates exceed long-term
yields_inverted = np.array([5.54, 5.55, 5.52, 5.46, 5.05, 4.80, 4.62, 4.65, 4.73, 5.07, 4.95])

# Normalizing curve (Jan 2025) - transition back toward normal
yields_normalizing = np.array([4.36, 4.34, 4.32, 4.22, 4.20, 4.23, 4.38, 4.47, 4.58, 4.85, 4.84])

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

colors = ["#306998", "#C44E52", "#8C8C8C"]
labels = ["Jan 2022 (Normal)", "Oct 2023 (Inverted)", "Jan 2025 (Normalizing)"]
all_yields = [yields_normal, yields_inverted, yields_normalizing]

for yields, color, label in zip(all_yields, colors, labels, strict=True):
    ax.plot(
        maturity_years,
        yields,
        color=color,
        linewidth=3,
        label=label,
        marker="o",
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=1.5,
    )

# Shade the inversion: area between 3M peak and the trough at 7Y
peak_yield = yields_inverted[1]  # 3M = 5.55 (peak)
trough_idx = 6  # 5Y = 4.62 (trough)
ax.fill_between(
    maturity_years[: trough_idx + 1], yields_inverted[: trough_idx + 1], peak_yield, alpha=0.10, color="#C44E52"
)

# Annotation for inversion
ax.annotate(
    "Yield curve inversion",
    xy=(3, 4.80),
    xytext=(8, 5.50),
    fontsize=14,
    color="#C44E52",
    fontweight="medium",
    arrowprops={"arrowstyle": "->", "color": "#C44E52", "lw": 1.5},
)

# Style
ax.set_xlabel("Maturity", fontsize=20)
ax.set_ylabel("Yield (%)", fontsize=20)
ax.set_title("line-yield-curve · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")

ax.set_xscale("log")
ax.set_xticks(maturity_years)
ax.set_xticklabels(maturities, fontsize=14)
ax.minorticks_off()
ax.tick_params(axis="y", labelsize=16)
ax.tick_params(axis="both", length=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

ax.legend(fontsize=16, frameon=False, loc="center right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
