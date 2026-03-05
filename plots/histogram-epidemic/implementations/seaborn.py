"""pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-05
"""

import matplotlib.dates as mdates
import matplotlib.lines as mlines
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
suspect_counts = np.maximum(0, confirmed_counts * 0.15 + np.random.normal(0, 2, 120)).astype(int)

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
sns.set_theme(style="ticks", font_scale=1.0, rc={"font.family": "sans-serif"})
sns.set_context("talk", rc={"axes.titlesize": 24, "axes.labelsize": 20, "xtick.labelsize": 16, "ytick.labelsize": 16})
palette = {"Confirmed": "#306998", "Probable": "#E8A838", "Suspect": "#9467BD"}

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
    linewidth=0.4,
    legend=True,
    ax=ax,
)

# Highlight peak period with subtle background shading
peak_start = pd.Timestamp("2024-03-01")
peak_end = pd.Timestamp("2024-03-18")
ax.axvspan(peak_start, peak_end, alpha=0.06, color="#C04040", zorder=0)
ax.text(
    peak_start + (peak_end - peak_start) / 2,
    ax.get_ylim()[1] * 0.85,
    "Peak Period",
    fontsize=16,
    ha="center",
    va="center",
    color="#C04040",
    fontstyle="italic",
    fontweight="semibold",
    alpha=0.9,
)

# Cumulative line on secondary axis
ax2 = ax.twinx()
ax2.plot(dates_range, cumulative, color="#C04040", linewidth=2.8, alpha=0.85, zorder=3)
ax2.set_ylabel("Cumulative Cases", fontsize=20, color="#C04040", labelpad=12)
ax2.tick_params(axis="y", labelsize=16, colors="#C04040")

# Intervention annotations with bolder styling
intervention_dates = [
    (pd.Timestamp("2024-02-20"), "Travel\nRestrictions"),
    (pd.Timestamp("2024-03-25"), "Vaccination\nCampaign"),
]
for date, label in intervention_dates:
    ax.axvline(date, color="#444444", linewidth=1.8, linestyle="--", alpha=0.8, zorder=5)
    ax.annotate(
        label,
        xy=(date, ax.get_ylim()[1] * 0.95),
        fontsize=14,
        fontweight="semibold",
        ha="center",
        va="top",
        color="#333333",
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": "#F8F8F8",
            "edgecolor": "#888888",
            "linewidth": 1.2,
            "alpha": 0.92,
        },
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

# Extend seaborn-generated legend with cumulative line entry
legend = ax.get_legend()
handles, labels = legend.legend_handles[:], [t.get_text() for t in legend.get_texts()]
legend.remove()
handles.append(mlines.Line2D([], [], color="#C04040", linewidth=2.5, alpha=0.85))
labels.append("Cumulative Cases")
ax.legend(
    handles=handles, labels=labels, fontsize=14, loc="upper left", framealpha=0.92, edgecolor="#CCCCCC", fancybox=True
)

# Save
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
