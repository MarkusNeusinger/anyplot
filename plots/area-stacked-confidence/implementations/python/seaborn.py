""" pyplots.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Quarterly energy consumption by source with measurement uncertainty
np.random.seed(42)

quarters = pd.date_range("2020-01-01", periods=24, freq="QE")
n = len(quarters)

# Base values for each energy source (in TWh)
solar_base = np.linspace(50, 150, n) + np.random.randn(n) * 8
wind_base = np.linspace(80, 180, n) + np.random.randn(n) * 10
hydro_base = np.linspace(100, 120, n) + np.random.randn(n) * 5

# Uncertainty grows over time (wider bands for projections)
solar_uncertainty = np.linspace(10, 25, n)
wind_uncertainty = np.linspace(12, 30, n)
hydro_uncertainty = np.linspace(8, 15, n)

# Create cumulative stacks for central values (bottom to top: Solar, Wind, Hydro)
solar_cumsum = solar_base
wind_cumsum = solar_base + wind_base
hydro_cumsum = solar_base + wind_base + hydro_base

# Confidence bands for each layer (stacked properly)
# Solar band (bottom layer)
solar_lower = solar_base - solar_uncertainty
solar_upper = solar_base + solar_uncertainty

# Wind band (cumulative from solar)
wind_lower_cumsum = solar_cumsum + (wind_base - wind_uncertainty)
wind_upper_cumsum = solar_cumsum + (wind_base + wind_uncertainty)

# Hydro band (cumulative from wind)
hydro_lower_cumsum = wind_cumsum + (hydro_base - hydro_uncertainty)
hydro_upper_cumsum = wind_cumsum + (hydro_base + hydro_uncertainty)

# Create plot
sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(figsize=(16, 9))

# Colors - Python Blue for primary, with variations
colors = {"solar": "#306998", "wind": "#FFD43B", "hydro": "#4A90A4"}

# Plot from top to bottom for proper layering (back to front)
# Hydro confidence band (top layer, drawn first to be in background)
ax.fill_between(quarters, hydro_lower_cumsum, hydro_upper_cumsum, color=colors["hydro"], alpha=0.25, linewidth=0)

# Hydro main area
ax.fill_between(quarters, wind_cumsum, hydro_cumsum, color=colors["hydro"], alpha=0.8, label="Hydro")

# Wind confidence band
ax.fill_between(quarters, wind_lower_cumsum, wind_upper_cumsum, color=colors["wind"], alpha=0.25, linewidth=0)

# Wind main area
ax.fill_between(quarters, solar_cumsum, wind_cumsum, color=colors["wind"], alpha=0.8, label="Wind")

# Solar confidence band
ax.fill_between(quarters, solar_lower, solar_upper, color=colors["solar"], alpha=0.25, linewidth=0)

# Solar main area (bottom layer)
ax.fill_between(quarters, 0, solar_cumsum, color=colors["solar"], alpha=0.8, label="Solar")

# Add lines for central values to show boundaries
ax.plot(quarters, solar_cumsum, color=colors["solar"], linewidth=2, alpha=0.9)
ax.plot(quarters, wind_cumsum, color=colors["wind"], linewidth=2, alpha=0.9)
ax.plot(quarters, hydro_cumsum, color=colors["hydro"], linewidth=2, alpha=0.9)

# Styling
ax.set_xlabel("Quarter", fontsize=20)
ax.set_ylabel("Energy Consumption (TWh)", fontsize=20)
ax.set_title("area-stacked-confidence \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)

# Legend - reverse order so bottom layer is first in legend
handles, labels = ax.get_legend_handles_labels()
legend = ax.legend(
    handles[::-1],
    labels[::-1],
    loc="upper left",
    fontsize=16,
    title="Energy Source\n(bands show 90% CI)",
    title_fontsize=14,
    framealpha=0.9,
)

# Grid
ax.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Format x-axis dates
fig.autofmt_xdate(rotation=45)

# Set y-axis to start at 0
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
