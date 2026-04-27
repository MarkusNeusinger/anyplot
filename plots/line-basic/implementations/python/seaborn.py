""" anyplot.ai
line-basic: Basic Line Plot
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 90/100 | Updated: 2026-04-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

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

# Data — monthly temperatures across 5 years; seaborn aggregates mean + 95% CI
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
records = []
for _year in range(2019, 2024):
    base_temp = 15 + 12 * np.sin((months - 4) * np.pi / 6)
    temps = base_temp + np.random.randn(12) * 2.5
    for month, temp in zip(months, temps, strict=True):
        records.append({"Month": month, "Temperature (°C)": temp})

df = pd.DataFrame(records)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(
    data=df,
    x="Month",
    y="Temperature (°C)",
    ax=ax,
    linewidth=3,
    color=BRAND,
    marker="o",
    markersize=12,
    errorbar="ci",
    err_kws={"alpha": 0.20},
    label="Mean ± 95% CI",
)

# Style
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Temperature (°C)", fontsize=20, color=INK)
ax.set_title("line-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.set_xticks(months)
ax.set_xticklabels(month_labels)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

legend = ax.legend(fontsize=16, framealpha=1.0)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
