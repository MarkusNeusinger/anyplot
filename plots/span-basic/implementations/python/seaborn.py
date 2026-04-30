"""anyplot.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-04-30
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

BRAND = "#009E73"  # Okabe-Ito position 1 — always first series
SPAN_RECESSION = "#D55E00"  # Okabe-Ito position 2
SPAN_TARGET = "#0072B2"  # Okabe-Ito position 3

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

# Data - Monthly sales revenue with recession period and target threshold
np.random.seed(42)
months = pd.date_range(start="2006-01", periods=60, freq="ME")
base_trend = np.linspace(100, 150, 60)
recession_effect = np.where((months >= "2008-01") & (months <= "2009-12"), -30 * np.sin(np.linspace(0, np.pi, 60)), 0)
sales = base_trend + recession_effect + np.random.randn(60) * 8
df = pd.DataFrame({"Month": months, "Sales": sales})

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Vertical span — recession period (2008–2009)
ax.axvspan(
    pd.Timestamp("2008-01-01"),
    pd.Timestamp("2009-12-31"),
    alpha=0.25,
    color=SPAN_RECESSION,
    label="Recession (2008–2009)",
)

# Horizontal span — target sales zone (120–140)
ax.axhspan(120, 140, alpha=0.20, color=SPAN_TARGET, label="Target Zone (120–140)")

# Line plot
sns.lineplot(data=df, x="Month", y="Sales", ax=ax, linewidth=3, color=BRAND)

# Style
ax.set_title("span-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xlabel("Month", fontsize=20, color=INK)
ax.set_ylabel("Sales (thousands $)", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.legend(fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
