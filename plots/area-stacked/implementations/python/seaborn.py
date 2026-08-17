""" anyplot.ai
area-stacked: Stacked Area Chart
Library: seaborn 0.13.2 | Python 3.13.15
Quality: 86/100 | Updated: 2026-08-17
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data: monthly energy consumption by sector over two years, with seasonality
np.random.seed(42)
months = pd.date_range("2024-01", periods=24, freq="ME")

industrial_base = 48 + np.sin(np.linspace(0, 4 * np.pi, 24)) * 4
residential_base = 34 + np.sin(np.linspace(np.pi, 5 * np.pi, 24)) * 9
commercial_base = 26 + np.sin(np.linspace(0.6, 4.6 * np.pi, 24)) * 5
transport_base = 16 + np.sin(np.linspace(1.2, 5.2 * np.pi, 24)) * 3
agriculture_base = 9 + np.sin(np.linspace(1.8, 5.8 * np.pi, 24)) * 2

growth = np.linspace(1.0, 1.18, 24)
industrial = (industrial_base * growth + np.random.randn(24) * 1.5).clip(30)
residential = (residential_base * growth + np.random.randn(24) * 1.5).clip(15)
commercial = (commercial_base * growth + np.random.randn(24) * 1.2).clip(12)
transport = (transport_base * growth + np.random.randn(24) * 0.8).clip(8)
agriculture = (agriculture_base * growth + np.random.randn(24) * 0.5).clip(4)

sectors = ["Industrial", "Residential", "Commercial", "Transport", "Agriculture"]
series = [industrial, residential, commercial, transport, agriculture]

# Plot — see default-style-guide.md "Visual Sizing Defaults" for canvas + sizing
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.stackplot(months, *series, labels=sectors, colors=IMPRINT_PALETTE, alpha=0.92, edgecolor=PAGE_BG, linewidth=0.6)

# A crisp ink-colored line traces the cumulative total for emphasis
total = np.sum(series, axis=0)
ax.plot(months, total, color=INK, linewidth=1.2, alpha=0.6, linestyle=(0, (1, 1.5)))

ax.set_xlabel("Month", fontsize=12, color=INK)
ax.set_ylabel("Consumption (GWh)", fontsize=12, color=INK)
ax.set_title("area-stacked · python · seaborn · anyplot.ai", fontsize=13, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=10, colors=INK_SOFT)

ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=40, ha="right")

# Legend sits outside the stacked area (fully filled top-to-bottom, no clear
# gap to dock a legend inside) so it never occludes data.
legend = ax.legend(
    loc="upper left",
    bbox_to_anchor=(1.01, 1.0),
    fontsize=9,
    framealpha=0.95,
    title="Sector",
    title_fontsize=10,
    labelcolor=INK,
)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_title().set_color(INK)

# Subtle y-axis grid only, per style guide
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# L-shaped frame
sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.set_ylim(bottom=0)
ax.margins(x=0)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
