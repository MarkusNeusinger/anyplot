""" pyplots.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data: quarterly energy consumption by source with measurement uncertainty
np.random.seed(42)

# Time axis: 8 years of quarterly data (32 quarters)
quarters = pd.date_range(start="2016-01-01", periods=32, freq="QE")

# Base consumption patterns for each energy source (in TWh)
# Solar: growing trend with seasonal variation
solar_base = 20 + np.linspace(0, 40, 32) + 8 * np.sin(np.linspace(0, 8 * np.pi, 32))
solar_uncertainty = 3 + np.linspace(0, 5, 32)  # Uncertainty grows with forecast horizon

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

# Colors for each series
colors = {
    "solar": "#FFD43B",  # Python Yellow
    "wind": "#306998",  # Python Blue
    "hydro": "#4ECDC4",  # Teal
    "gas": "#FF6B6B",  # Coral
}

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot stacked areas from bottom to top
# Solar (bottom layer)
ax.fill_between(quarters, 0, solar_stack, color=colors["solar"], alpha=0.8, label="Solar")
ax.fill_between(quarters, solar_lower, solar_upper, color=colors["solar"], alpha=0.25, linewidth=0)

# Wind (second layer)
ax.fill_between(quarters, solar_stack, wind_stack, color=colors["wind"], alpha=0.8, label="Wind")
ax.fill_between(quarters, wind_lower, wind_upper, color=colors["wind"], alpha=0.25, linewidth=0)

# Hydro (third layer)
ax.fill_between(quarters, wind_stack, hydro_stack, color=colors["hydro"], alpha=0.8, label="Hydro")
ax.fill_between(quarters, hydro_lower, hydro_upper, color=colors["hydro"], alpha=0.25, linewidth=0)

# Natural Gas (top layer)
ax.fill_between(quarters, hydro_stack, gas_stack, color=colors["gas"], alpha=0.8, label="Natural Gas")
ax.fill_between(quarters, gas_lower, gas_upper, color=colors["gas"], alpha=0.25, linewidth=0)

# Add center lines for clarity
ax.plot(quarters, solar_stack, color=colors["solar"], linewidth=2, alpha=0.9)
ax.plot(quarters, wind_stack, color=colors["wind"], linewidth=2, alpha=0.9)
ax.plot(quarters, hydro_stack, color=colors["hydro"], linewidth=2, alpha=0.9)
ax.plot(quarters, gas_stack, color=colors["gas"], linewidth=2, alpha=0.9)

# Styling
ax.set_xlabel("Quarter", fontsize=20)
ax.set_ylabel("Energy Consumption (TWh)", fontsize=20)
ax.set_title("area-stacked-confidence · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Format x-axis dates
fig.autofmt_xdate(rotation=45)

# Legend with confidence band note
handles, labels = ax.get_legend_handles_labels()
ax.legend(
    handles,
    labels,
    loc="upper left",
    fontsize=16,
    framealpha=0.9,
    title="Energy Source (with 90% CI bands)",
    title_fontsize=14,
)

# Set y-axis to start at 0
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
