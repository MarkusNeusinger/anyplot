""" anyplot.ai
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

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1 - bluish green for main series
EVENT_COLOR = "#954477"  # Position 7 - yellow for annotations

# Configure seaborn with theme tokens
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

# Data - Simulating monthly product sales with marketing events
np.random.seed(42)

# Create 365 days of sales data
dates = pd.date_range("2024-01-01", periods=365, freq="D")
# Base trend with seasonality and noise
trend = np.linspace(100, 180, 365)
seasonality = 15 * np.sin(np.linspace(0, 4 * np.pi, 365))
noise = np.random.normal(0, 8, 365)
sales = trend + seasonality + noise

df = pd.DataFrame({"date": dates, "sales": sales})

# Events - Key marketing milestones
events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(["2024-02-14", "2024-05-01", "2024-07-15", "2024-09-20", "2024-11-25"]),
        "event_label": ["Valentine's Campaign", "Spring Sale", "Summer Launch", "Fall Promotion", "Black Friday"],
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Main line plot using seaborn
sns.lineplot(data=df, x="date", y="sales", ax=ax, linewidth=2.5, color=BRAND)

# Add event markers with alternating heights for readability
y_positions = [0.85, 0.75, 0.85, 0.75, 0.85]

for i, (_, event) in enumerate(events.iterrows()):
    # Vertical line at event date
    ax.axvline(x=event["event_date"], color=EVENT_COLOR, linestyle="--", linewidth=2, alpha=0.8)

    # Event label with background
    y_pos = ax.get_ylim()[0] + (ax.get_ylim()[1] - ax.get_ylim()[0]) * y_positions[i]
    ax.annotate(
        event["event_label"],
        xy=(event["event_date"], y_pos),
        fontsize=14,
        fontweight="bold",
        color=INK,
        ha="center",
        va="bottom",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": EVENT_COLOR, "edgecolor": "none", "alpha": 0.9},
        rotation=0,
    )

    # Small marker on the line at event date
    event_sales = df.loc[df["date"] == event["event_date"], "sales"]
    if not event_sales.empty:
        ax.scatter(
            event["event_date"], event_sales.values[0], color=EVENT_COLOR, s=150, zorder=5, edgecolor=INK, linewidth=2
        )

# Styling
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Daily Sales (Units)", fontsize=20, color=INK)
ax.set_title("line-annotated-events · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

# Subtle y-axis grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Add legend explaining event markers
legend_elements = [
    Line2D([0], [0], color=BRAND, lw=2.5, label="Daily Sales"),
    Line2D([0], [0], color=EVENT_COLOR, lw=2, linestyle="--", label="Event Marker"),
]
ax.legend(handles=legend_elements, loc="upper left", fontsize=16, frameon=True, fancybox=True)

# Format x-axis dates
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
