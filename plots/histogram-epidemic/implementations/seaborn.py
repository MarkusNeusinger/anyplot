"""pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 68/100 | Created: 2026-03-05
"""

import matplotlib.dates as mdates
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

dates_range = pd.date_range("2024-01-15", periods=120, freq="D")

confirmed_base = np.concatenate(
    [
        np.linspace(2, 35, 30),
        np.linspace(35, 80, 15),
        np.linspace(80, 120, 10),
        np.linspace(120, 60, 20),
        np.linspace(60, 25, 15),
        np.linspace(25, 45, 10),
        np.linspace(45, 15, 20),
    ]
)
confirmed_counts = np.maximum(0, confirmed_base + np.random.normal(0, 8, 120)).astype(int)
probable_counts = np.maximum(0, confirmed_counts * 0.25 + np.random.normal(0, 3, 120)).astype(int)
suspect_counts = np.maximum(0, confirmed_counts * 0.12 + np.random.normal(0, 2, 120)).astype(int)

# Build long-form DataFrame with one row per case for sns.histplot
rows = []
for i, date in enumerate(dates_range):
    rows.extend([(date, "Confirmed")] * confirmed_counts[i])
    rows.extend([(date, "Probable")] * probable_counts[i])
    rows.extend([(date, "Suspect")] * suspect_counts[i])
cases_df = pd.DataFrame(rows, columns=["onset_date", "case_type"])

# Cumulative data
daily_totals = confirmed_counts + probable_counts + suspect_counts
cumulative = np.cumsum(daily_totals)

# Plot
sns.set_theme(style="ticks", font_scale=1.0)
palette = {"Confirmed": "#306998", "Probable": "#E8A838", "Suspect": "#5BA05B"}

fig, ax = plt.subplots(figsize=(16, 9))

sns.histplot(
    data=cases_df,
    x="onset_date",
    hue="case_type",
    hue_order=["Confirmed", "Probable", "Suspect"],
    multiple="stack",
    palette=palette,
    bins=120,
    edgecolor="white",
    linewidth=0.3,
    legend=False,
    ax=ax,
)

# Cumulative line on secondary axis
ax2 = ax.twinx()
ax2.plot(dates_range, cumulative, color="#C04040", linewidth=2.5, alpha=0.85)
ax2.set_ylabel("Cumulative Cases", fontsize=20, color="#C04040")
ax2.tick_params(axis="y", labelsize=16, colors="#C04040")

# Intervention annotations
intervention_dates = [
    (pd.Timestamp("2024-02-20"), "Travel\nRestrictions"),
    (pd.Timestamp("2024-03-25"), "Vaccination\nCampaign"),
]
for date, label in intervention_dates:
    ax.axvline(date, color="#555555", linewidth=1.5, linestyle="--", alpha=0.7, zorder=5)
    ax.text(
        date,
        ax.get_ylim()[1] * 0.92,
        label,
        fontsize=13,
        ha="center",
        va="top",
        color="#555555",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#CCCCCC", "alpha": 0.85},
    )

# Style
ax.set_xlabel("Date of Symptom Onset", fontsize=20)
ax.set_ylabel("New Cases", fontsize=20)
ax.set_title("histogram-epidemic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

sns.despine(ax=ax)
sns.despine(ax=ax2, left=True)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_axisbelow(True)

# Build legend manually to combine bar categories with cumulative line
legend_handles = [
    mpatches.Patch(facecolor=palette["Confirmed"], edgecolor="white", label="Confirmed"),
    mpatches.Patch(facecolor=palette["Probable"], edgecolor="white", label="Probable"),
    mpatches.Patch(facecolor=palette["Suspect"], edgecolor="white", label="Suspect"),
    mlines.Line2D([], [], color="#C04040", linewidth=2.5, alpha=0.85, label="Cumulative Cases"),
]
ax.legend(handles=legend_handles, fontsize=14, loc="upper left", framealpha=0.9)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
