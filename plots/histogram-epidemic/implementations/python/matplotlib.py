""" pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-05
"""

import matplotlib.dates as mdates
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)
dates = pd.date_range("2024-01-15", periods=90, freq="D")

confirmed_base = np.concatenate(
    [
        np.random.poisson(3, 10),
        np.random.poisson(12, 10),
        np.random.poisson(35, 10),
        np.random.poisson(55, 10),
        np.random.poisson(15, 10),
        np.random.poisson(8, 10),
        np.random.poisson(30, 10),
        np.random.poisson(50, 10),
        np.random.poisson(18, 10),
    ]
)
probable = np.maximum(0, (confirmed_base * np.random.uniform(0.1, 0.3, 90)).astype(int))
suspect = np.maximum(0, (confirmed_base * np.random.uniform(0.05, 0.15, 90)).astype(int))
confirmed = confirmed_base - probable - suspect
confirmed = np.maximum(0, confirmed)

df = pd.DataFrame({"date": dates, "Confirmed": confirmed, "Probable": probable, "Suspect": suspect})

cumulative = (df["Confirmed"] + df["Probable"] + df["Suspect"]).cumsum()

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

bar_width = 0.8
ax.bar(
    df["date"], df["Confirmed"], width=bar_width, label="Confirmed", color="#306998", edgecolor="white", linewidth=0.6
)
ax.bar(
    df["date"],
    df["Probable"],
    width=bar_width,
    bottom=df["Confirmed"],
    label="Probable",
    color="#E8A838",
    edgecolor="white",
    linewidth=0.6,
)
ax.bar(
    df["date"],
    df["Suspect"],
    width=bar_width,
    bottom=df["Confirmed"] + df["Probable"],
    label="Suspect",
    color="#5BAA8A",
    edgecolor="white",
    linewidth=0.6,
)

# Cumulative line on secondary axis
ax2 = ax.twinx()
ax2.plot(df["date"], cumulative, color="#C44E52", linewidth=2.5, alpha=0.85, label="Cumulative cases")
ax2.fill_between(df["date"], cumulative, alpha=0.08, color="#C44E52")
ax2.set_ylabel("Cumulative Cases", fontsize=20, color="#C44E52")
ax2.tick_params(axis="y", labelsize=16, colors="#C44E52")
ax2.spines["top"].set_visible(False)

# Intervention lines
lockdown_date = pd.Timestamp("2024-02-10")
vaccine_date = pd.Timestamp("2024-03-15")
ax.axvline(lockdown_date, color="#555555", linestyle="--", linewidth=1.5, alpha=0.7)
ax.axvline(vaccine_date, color="#555555", linestyle="--", linewidth=1.5, alpha=0.7)
text_effect = [pe.withStroke(linewidth=3, foreground="white")]
ax.text(
    lockdown_date,
    ax.get_ylim()[1] * 0.95,
    " Lockdown",
    fontsize=14,
    color="#555555",
    va="top",
    ha="left",
    path_effects=text_effect,
)
ax.text(
    vaccine_date,
    ax.get_ylim()[1] * 0.95,
    " Vaccination\n campaign",
    fontsize=14,
    color="#555555",
    va="top",
    ha="left",
    path_effects=text_effect,
)

# Style
ax.set_xlabel("Date of Symptom Onset", fontsize=20)
ax.set_ylabel("Daily New Cases", fontsize=20)
ax.set_title("histogram-epidemic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_axisbelow(True)

# Combined legend
lines_ax, labels_ax = ax.get_legend_handles_labels()
lines_ax2, labels_ax2 = ax2.get_legend_handles_labels()
ax.legend(lines_ax + lines_ax2, labels_ax + labels_ax2, fontsize=16, loc="upper left", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
