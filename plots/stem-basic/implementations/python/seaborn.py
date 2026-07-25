"""anyplot.ai
stem-basic: Basic Stem Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Imprint palette position 1

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

# Data - Discrete signal samples (damped sinusoidal impulse response)
np.random.seed(42)
n_samples = 30
x = np.arange(n_samples)
y = np.exp(-0.1 * x) * np.sin(0.5 * x) * 2.5
envelope = np.exp(-0.1 * x) * 2.5

df = pd.DataFrame({"Sample Index": x, "Amplitude": y, "Magnitude": np.abs(y)})
peak_idx = df["Magnitude"].idxmax()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Decay envelope - traces the impulse-response narrative behind the samples
sns.lineplot(x=x, y=envelope, ax=ax, color=INK_SOFT, linewidth=1.2, linestyle="--", alpha=0.4, zorder=1)
sns.lineplot(x=x, y=-envelope, ax=ax, color=INK_SOFT, linewidth=1.2, linestyle="--", alpha=0.4, zorder=1)

# Stems (thin vertical lines from baseline y=0 to data values)
ax.vlines(x=df["Sample Index"], ymin=0, ymax=df["Amplitude"], color=BRAND, linewidth=1.5, alpha=0.8, zorder=2)

# Markers sized by amplitude magnitude (seaborn statistical size mapping) - plain
# dots with no background-colored edge, a deliberate departure from the
# matplotlib/plotly treatment of this spec.
sns.scatterplot(
    data=df,
    x="Sample Index",
    y="Amplitude",
    size="Magnitude",
    sizes=(30, 140),
    color=BRAND,
    edgecolor="none",
    legend=False,
    ax=ax,
    zorder=3,
)

# Baseline at y=0
ax.axhline(y=0, color=INK_SOFT, linewidth=0.75, alpha=0.5, zorder=1)

# Annotate the peak sample to guide the viewer through the decay narrative
ax.annotate(
    "Peak amplitude",
    xy=(df["Sample Index"][peak_idx], df["Amplitude"][peak_idx]),
    xytext=(df["Sample Index"][peak_idx] + 3, df["Amplitude"][peak_idx] + 0.3),
    fontsize=8,
    color=INK_SOFT,
    arrowprops={"arrowstyle": "-", "color": INK_SOFT, "alpha": 0.6, "linewidth": 0.75},
)

ax.set_xlabel("Sample Index (n)", fontsize=10)
ax.set_ylabel("Amplitude", fontsize=10)
ax.set_title("stem-basic · seaborn · anyplot.ai", fontsize=12)
ax.tick_params(axis="both", labelsize=8)

ax.yaxis.grid(True, linestyle="-", linewidth=0.4, alpha=0.15)
ax.set_axisbelow(True)

sns.despine(ax=ax)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
