"""anyplot.ai
line-basic: Basic Line Plot
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-10-23
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
BRAND = "#009E73"
ACCENT = "#C475FD"

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
    },
)

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
TEMPERATURE = "Temperature (°C)"  # role: y

# Data: monthly temperatures over five years; seaborn draws the mean and a 95 % interval
np.random.seed(42)
months = np.tile(np.arange(1, 13), 5)
seasonal = 15 + 12 * np.sin((months - 4) * np.pi / 6)
df = pd.DataFrame({MONTH: months, TEMPERATURE: seasonal + np.random.randn(months.size) * 2.5})

# Plot: reads only df and the constants above
means = df.groupby(MONTH, sort=True)[TEMPERATURE].mean()
peak = means.idxmax()

fig, ax = plt.subplots(figsize=(16, 9), dpi=200, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
sns.lineplot(
    data=df,
    x=MONTH,
    y=TEMPERATURE,
    ax=ax,
    linewidth=3,
    color=BRAND,
    marker="o",
    markersize=12,
    errorbar=("ci", 95),
    err_kws={"alpha": 0.20},
    label="Mean with 95 % interval",
)
ax.scatter(
    [peak], [means[peak]], color=ACCENT, s=300, zorder=5, edgecolors=PAGE_BG, linewidth=2.5, label=f"Peak: {peak}"
)

# Style
ax.set_title("line-basic · python · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.spines[["top", "right"]].set_visible(False)
legend = ax.legend(fontsize=16, framealpha=1.0)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
plt.savefig(f"plot-{THEME}.png", dpi=200, facecolor=PAGE_BG)
