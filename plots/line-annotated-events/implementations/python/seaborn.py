"""anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
BRAND = "#009E73"  # position 1: the main series
EVENT_COLOR = "#954477"  # position 7: event markers and labels

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

# Constants
LABEL_HEIGHTS = (0.90, 0.80)  # alternating label heights, as axes fractions

# Columns
DATE = "Date"  # role: date
SALES = "Daily Sales (Units)"  # role: value
EVENT_DATE = "Event Date"  # role: event_date
EVENT_LABEL = "Event"  # role: event_label

# Data
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=365, freq="D")
trend = np.linspace(100, 180, 365)
seasonality = 15 * np.sin(np.linspace(0, 4 * np.pi, 365))
noise = np.random.normal(0, 8, 365)
df = pd.DataFrame({DATE: dates, SALES: trend + seasonality + noise})
event_names = {
    "2024-02-14": "Valentine's Campaign",
    "2024-05-01": "Spring Sale",
    "2024-07-15": "Summer Launch",
    "2024-09-20": "Fall Promotion",
    "2024-11-25": "Black Friday",
}
df[EVENT_LABEL] = df[DATE].dt.strftime("%Y-%m-%d").map(event_names)
df[EVENT_DATE] = df[DATE].where(df[EVENT_LABEL].notna())

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

sns.lineplot(data=df, x=DATE, y=SALES, ax=ax, linewidth=1.8, color=BRAND)

events = df.dropna(subset=[EVENT_LABEL])

for i, (event_date, label, sales) in enumerate(
    zip(events[EVENT_DATE], events[EVENT_LABEL], events[SALES], strict=True)
):
    ax.axvline(x=event_date, color=EVENT_COLOR, linestyle="--", linewidth=1.2, alpha=0.85)
    ax.annotate(
        label,
        xy=(event_date, LABEL_HEIGHTS[i % len(LABEL_HEIGHTS)]),
        xycoords=("data", "axes fraction"),
        xytext=(4, 0),
        textcoords="offset points",
        fontsize=8,
        fontweight="bold",
        color="#FFFFFF",
        ha="left",
        va="center",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": EVENT_COLOR, "edgecolor": "none"},
    )
    ax.scatter(event_date, sales, color=EVENT_COLOR, s=45, zorder=5, edgecolor=INK, linewidth=1)

ax.set_ylim(df[SALES].min() - 10, df[SALES].max() + 20)
ax.set_xlabel(DATE, fontsize=10)
ax.set_ylabel(SALES, fontsize=10)
ax.set_title("line-annotated-events · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium")
ax.tick_params(axis="both", labelsize=8)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

legend_elements = [
    Line2D([0], [0], color=BRAND, lw=1.8, label="Daily sales"),
    Line2D([0], [0], color=EVENT_COLOR, lw=1.2, linestyle="--", label="Event marker"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=8, frameon=True, fancybox=True)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
