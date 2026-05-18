"""anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data: quarterly energy consumption by source with measurement uncertainty
np.random.seed(42)

# Time axis: 8 years of quarterly data (32 quarters)
quarters = pd.date_range(start="2016-01-01", periods=32, freq="QS")

# Base consumption patterns for each energy source (in TWh)
# Solar: growing trend with seasonal variation
solar_base = 20 + np.linspace(0, 40, 32) + 8 * np.sin(np.linspace(0, 8 * np.pi, 32))
solar_uncertainty = 3 + np.linspace(0, 5, 32)

# Wind: moderate growth with higher seasonal variation
wind_base = 35 + np.linspace(0, 30, 32) + 12 * np.sin(np.linspace(0, 8 * np.pi, 32) + np.pi / 2)
wind_uncertainty = 5 + np.linspace(0, 6, 32)

# Hydro: stable with seasonal peaks
hydro_base = 50 + 15 * np.sin(np.linspace(0, 8 * np.pi, 32) - np.pi / 4)
hydro_uncertainty = 4 + 2 * np.abs(np.sin(np.linspace(0, 8 * np.pi, 32)))

# Natural Gas: declining trend
gas_base = 80 - np.linspace(0, 25, 32) + 5 * np.random.randn(32)
gas_uncertainty = 6 + np.linspace(0, 4, 32)

# Create stacked values (cumulative)
solar_stack = solar_base
wind_stack = solar_base + wind_base
hydro_stack = wind_stack + hydro_base
gas_stack = hydro_stack + gas_base

# Confidence bands (stacked appropriately)
# Solar bands
solar_lower = solar_base - solar_uncertainty
solar_upper = solar_base + solar_uncertainty

# Wind bands (stacked on solar)
wind_lower = solar_stack + (wind_base - wind_uncertainty)
wind_upper = solar_stack + (wind_base + wind_uncertainty)

# Hydro bands (stacked on wind)
hydro_lower = wind_stack + (hydro_base - hydro_uncertainty)
hydro_upper = wind_stack + (hydro_base + hydro_uncertainty)

# Gas bands (stacked on hydro)
gas_lower = hydro_stack + (gas_base - gas_uncertainty)
gas_upper = hydro_stack + (gas_base + gas_uncertainty)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot stacked areas from bottom to top
# Solar (bottom layer)
ax.fill_between(quarters, 0, solar_stack, color=OKABE_ITO[0], alpha=0.8, label="Solar")
ax.fill_between(quarters, solar_lower, solar_upper, color=OKABE_ITO[0], alpha=0.2, linewidth=0)

# Wind (second layer)
ax.fill_between(quarters, solar_stack, wind_stack, color=OKABE_ITO[1], alpha=0.8, label="Wind")
ax.fill_between(quarters, wind_lower, wind_upper, color=OKABE_ITO[1], alpha=0.2, linewidth=0)

# Hydro (third layer)
ax.fill_between(quarters, wind_stack, hydro_stack, color=OKABE_ITO[2], alpha=0.8, label="Hydro")
ax.fill_between(quarters, hydro_lower, hydro_upper, color=OKABE_ITO[2], alpha=0.2, linewidth=0)

# Natural Gas (top layer)
ax.fill_between(quarters, hydro_stack, gas_stack, color=OKABE_ITO[3], alpha=0.8, label="Natural Gas")
ax.fill_between(quarters, gas_lower, gas_upper, color=OKABE_ITO[3], alpha=0.2, linewidth=0)

# Add center lines for clarity
ax.plot(quarters, solar_stack, color=OKABE_ITO[0], linewidth=2, alpha=0.9)
ax.plot(quarters, wind_stack, color=OKABE_ITO[1], linewidth=2, alpha=0.9)
ax.plot(quarters, hydro_stack, color=OKABE_ITO[2], linewidth=2, alpha=0.9)
ax.plot(quarters, gas_stack, color=OKABE_ITO[3], linewidth=2, alpha=0.9)

# Styling
ax.set_xlabel("Quarter", fontsize=20, color=INK)
ax.set_ylabel("Energy Consumption (TWh)", fontsize=20, color=INK)
ax.set_title("area-stacked-confidence · Python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid on both axes (subtle)
ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Format x-axis dates
fig.autofmt_xdate(rotation=45)

# Legend with confidence band note
legend = ax.legend(
    loc="upper left", fontsize=16, framealpha=0.95, title="Energy Source (shaded: 90% CI bands)", title_fontsize=16
)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_frame().set_linewidth(1)
for text in legend.get_texts():
    text.set_color(INK_SOFT)
legend.get_title().set_color(INK)

# Set y-axis to start at 0
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
