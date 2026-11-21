"""anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Columns: set these to your table's column names
AMBIENT = "Ambient Value"  # role: x
OUTPUT = "Sensor Output"  # role: y
SENSOR = "Sensor Type"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("sensors.csv")
np.random.seed(42)
n_per_group = 50

# Temperature sensors
temp_x = np.random.normal(25, 4, n_per_group)
temp_y = np.random.normal(55, 10, n_per_group)

# Pressure sensors: higher variance
pressure_x = np.random.normal(1005, 5, n_per_group)
pressure_y = np.random.normal(65, 12, n_per_group)

# Humidity sensors
humidity_x = np.random.normal(28, 4.5, n_per_group)
humidity_y = np.random.normal(72, 11, n_per_group)

df = pd.DataFrame(
    {
        AMBIENT: np.concatenate([temp_x, pressure_x, humidity_x]),
        OUTPUT: np.concatenate([temp_y, pressure_y, humidity_y]),
        SENSOR: ["Temperature"] * n_per_group + ["Pressure"] * n_per_group + ["Humidity"] * n_per_group,
    }
)

# Plot
n_groups = df[SENSOR].nunique()
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.scatterplot(
    data=df,
    x=AMBIENT,
    y=OUTPUT,
    hue=SENSOR,
    palette=IMPRINT_PALETTE[:n_groups],
    s=60,
    alpha=0.7,
    edgecolor=PAGE_BG,
    linewidth=0.3,
    ax=ax,
)

# Style
ax.set_title("scatter-categorical · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(AMBIENT, fontsize=10)
ax.set_ylabel(OUTPUT, fontsize=10)
ax.tick_params(axis="both", labelsize=8)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.legend(title=SENSOR, fontsize=8, title_fontsize=9, loc="upper center")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
