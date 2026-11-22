"""anyplot.ai
pdp-basic: Partial Dependence Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TEMPERATURE = "Temperature (°C)"  # role: feature_values
HUMIDITY = "Humidity (%)"  # role: extra
WIND = "Wind speed (m/s)"  # role: extra
DEMAND = "Energy demand (GWh/day)"  # role: partial_dependence

# Data: replace this block with your own table, for example df = pd.read_csv("demand.csv")
rng = np.random.default_rng(42)
n_days = 600
temperature = rng.uniform(-8, 38, n_days)
humidity = rng.uniform(30, 95, n_days)
wind = rng.gamma(2.5, 2.0, n_days)
# U-shaped demand: heating below ~16 °C, air conditioning above it (more so when humid)
demand = 90 + 0.135 * (temperature - 16) ** 2 + 0.12 * humidity * (temperature > 24) + 0.8 * wind
df = pd.DataFrame({TEMPERATURE: temperature, HUMIDITY: humidity, WIND: wind, DEMAND: demand + rng.normal(0, 6, n_days)})

# Plot: reads only df and the constants above
features = [TEMPERATURE, HUMIDITY, WIND]
model = GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=42)
model.fit(df[features], df[DEMAND])

pdp = partial_dependence(model, df[features], features=[TEMPERATURE], kind="both", grid_resolution=80)
grid = pdp["grid_values"][0]
average = pdp["average"][0]
shift = average.mean()
average_centered = average - shift
ice_centered = pdp["individual"][0] - shift
band_lower, band_upper = np.percentile(ice_centered, [10, 90], axis=0)

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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# Band: spread of the individual curves (10th to 90th percentile), behind the average
ax.fill_between(
    grid, band_lower, band_upper, color=IMPRINT_PALETTE[0], alpha=0.22, linewidth=0, label="ICE spread (10th–90th pct.)"
)
sns.lineplot(x=grid, y=average_centered, ax=ax, color=IMPRINT_PALETTE[0], linewidth=2.5, label="Partial dependence")
ax.axhline(0, color=INK_SOFT, linestyle="--", linewidth=1.0, alpha=0.6)

# Rug of the observed temperatures
sns.rugplot(data=df, x=TEMPERATURE, ax=ax, color=INK_SOFT, height=0.04, alpha=0.5, linewidth=0.8)

# Style
ax.set_title("pdp-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.set_xlabel(TEMPERATURE, fontsize=10)
ax.set_ylabel("Partial dependence of demand (GWh/day, centered)", fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.6)
sns.despine(ax=ax)
ax.legend(fontsize=8, loc="upper center", frameon=True, fancybox=False)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
