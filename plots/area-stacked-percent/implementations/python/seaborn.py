""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (positions 1-4 for 4 categories)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Market share evolution of renewable energy sources
np.random.seed(42)
years = np.arange(2015, 2025)

# Generate synthetic data showing interesting transitions
solar = np.array([10, 12, 15, 18, 22, 26, 30, 35, 40, 45])
wind = np.array([20, 22, 24, 26, 28, 30, 32, 33, 34, 35])
hydro = np.array([50, 48, 45, 42, 38, 34, 30, 27, 23, 18])
other = np.array([20, 18, 16, 14, 12, 10, 8, 5, 3, 2])

# Create DataFrame and normalize to 100%
df_wide = pd.DataFrame({"Year": years, "Solar": solar, "Wind": wind, "Hydro": hydro, "Other": other})

# Calculate percentages (normalize to 100%)
total = df_wide[["Solar", "Wind", "Hydro", "Other"]].sum(axis=1)
for col in ["Solar", "Wind", "Hydro", "Other"]:
    df_wide[col] = df_wide[col] / total * 100

# Calculate cumulative values for stacking
df_wide["Other_top"] = df_wide["Other"]
df_wide["Hydro_top"] = df_wide["Other"] + df_wide["Hydro"]
df_wide["Wind_top"] = df_wide["Other"] + df_wide["Hydro"] + df_wide["Wind"]
df_wide["Solar_top"] = 100

df_wide["Other_bottom"] = 0
df_wide["Hydro_bottom"] = df_wide["Other"]
df_wide["Wind_bottom"] = df_wide["Other"] + df_wide["Hydro"]
df_wide["Solar_bottom"] = df_wide["Other"] + df_wide["Hydro"] + df_wide["Wind"]

# Configure seaborn theme
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
    },
)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot stacked areas in order: Solar (brand green), Wind, Hydro, Other
categories = ["Solar", "Wind", "Hydro", "Other"]
colors_map = dict(zip(categories, IMPRINT, strict=True))

for cat in categories:
    ax.fill_between(
        df_wide["Year"],
        df_wide[f"{cat}_bottom"],
        df_wide[f"{cat}_top"],
        label=cat,
        color=colors_map[cat],
        alpha=0.85,
        linewidth=0.5,
        edgecolor=colors_map[cat],
    )

# Style
ax.set_xlabel("Year", fontsize=20, color=INK)
ax.set_ylabel("Share (%)", fontsize=20, color=INK)
ax.set_title("area-stacked-percent · seaborn · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

ax.set_ylim(0, 100)
ax.set_xlim(2015, 2024)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

ax.legend(loc="upper left", fontsize=16, framealpha=0.95, facecolor=PAGE_BG, edgecolor=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
