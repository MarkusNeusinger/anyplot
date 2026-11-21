"""anyplot.ai
box-horizontal: Horizontal Box Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1, single-series plot

# Columns: set these to your table's column names
SERVICE = "Service Type"  # role: categories
RESPONSE_TIME = "Response Time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
samples = {
    "Authentication Service": np.random.normal(150, 30, 80),  # tight distribution
    "Database Query": np.concatenate([np.random.normal(200, 40, 70), [450, 480, 520]]),  # with outliers
    "File Upload": np.random.normal(500, 100, 90),  # wider spread
    "Payment Processing": np.random.exponential(180, 85) + 100,  # skewed right
    "Email Notification": np.random.normal(80, 15, 75),  # fast and tight
    "Image Processing": np.random.uniform(300, 800, 60),  # wide uniform spread
}
df = pd.DataFrame(
    {
        SERVICE: np.repeat(list(samples), [len(v) for v in samples.values()]),
        RESPONSE_TIME: np.concatenate(list(samples.values())),
    }
)

# Plot: reads only df and the constants above
groups = [(name, rows[RESPONSE_TIME].dropna().to_numpy()) for name, rows in df.groupby(SERVICE, sort=False)]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.boxplot(
    [values for _, values in groups],
    orientation="horizontal",
    tick_labels=[name for name, _ in groups],
    patch_artist=True,
    widths=0.6,
    flierprops={"marker": "o", "markersize": 4, "markerfacecolor": BRAND, "markeredgecolor": BRAND},
    medianprops={"color": INK, "linewidth": 1.5},
    whiskerprops={"color": INK_SOFT, "linewidth": 1.2},
    capprops={"color": INK_SOFT, "linewidth": 1.2},
    boxprops={"facecolor": BRAND, "edgecolor": BRAND, "linewidth": 1.2, "alpha": 0.7},
)

# Style
ax.set_xlabel(RESPONSE_TIME, fontsize=10, color=INK)
ax.set_ylabel(SERVICE, fontsize=10, color=INK)
ax.set_title("box-horizontal · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)

fig.subplots_adjust(left=0.22, right=0.97, top=0.92, bottom=0.13)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
