""" pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns


# Data — U.S. Treasury yield curves on three dates
maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = [1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

curves = {
    "2021-07-15 (Normal)": [0.05, 0.05, 0.06, 0.09, 0.25, 0.46, 0.83, 1.13, 1.34, 1.86, 1.99],
    "2023-07-15 (Inverted)": [5.28, 5.40, 5.47, 5.40, 4.87, 4.55, 4.18, 4.07, 3.98, 4.22, 4.05],
    "2024-09-15 (Flat)": [4.96, 4.92, 4.72, 4.25, 3.60, 3.48, 3.44, 3.52, 3.65, 4.03, 4.01],
}

rows = []
for date_label, yields in curves.items():
    for m_label, m_years, y_pct in zip(maturities, maturity_years, yields, strict=True):
        rows.append({"date": date_label, "maturity": m_label, "maturity_years": m_years, "yield_pct": y_pct})

df = pd.DataFrame(rows)

# Plot
palette = ["#306998", "#C74B50", "#5A9E6F"]
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(
    data=df,
    x="maturity_years",
    y="yield_pct",
    hue="date",
    style="date",
    markers=True,
    dashes=False,
    palette=palette,
    linewidth=3,
    markersize=10,
    ax=ax,
)

# Shade 2Y-10Y inversion region (classic recession indicator)
inv_yields = np.array(curves["2023-07-15 (Inverted)"])
inv_mat = np.array(maturity_years)
idx_2y = list(maturity_years).index(2)
idx_10y = list(maturity_years).index(10)
yield_2y = inv_yields[idx_2y]
yield_10y = inv_yields[idx_10y]
if yield_2y > yield_10y:
    ax.fill_between([2, 10], yield_10y, yield_2y, alpha=0.10, color="#C74B50", zorder=0)
    ax.annotate(
        "2Y–10Y Inversion",
        xy=(6, (yield_2y + yield_10y) / 2),
        fontsize=13,
        color="#C74B50",
        alpha=0.85,
        ha="center",
        va="center",
    )

# Style
ax.set_xlabel("Maturity", fontsize=20)
ax.set_ylabel("Yield (%)", fontsize=20)
ax.set_title("U.S. Treasury Yield Curves · line-yield-curve · seaborn · pyplots.ai", fontsize=22, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

ax.set_xscale("log")
ax.set_xticks(maturity_years)
ax.set_xticklabels(maturities, fontsize=14)
ax.xaxis.set_minor_locator(mticker.NullLocator())
ax.xaxis.set_minor_formatter(mticker.NullFormatter())

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

ax.legend(title="Date", fontsize=14, title_fontsize=16, loc="center left", frameon=False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
