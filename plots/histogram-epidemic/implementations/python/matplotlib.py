""" anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-28
"""

import os

import matplotlib.dates as mdates
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per case classification in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
CUMULATIVE_COLOR = "#AE3030"  # matte red — total burden / severity semantic anchor

# Columns: set these to your table's column names
ONSET_DATE = "Date of Symptom Onset"  # role: onset_date
CASE_COUNT = "Daily New Cases"  # role: case_count
CASE_TYPE = "Case classification"  # role: case_type
EVENT = "Intervention"  # role: events

# Data: replace this block with your own table, for example df = pd.read_csv("cases.csv")
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
confirmed = np.maximum(0, confirmed_base - probable - suspect)
events = {pd.Timestamp("2024-02-10"): "Lockdown", pd.Timestamp("2024-03-15"): "Vaccination\ncampaign"}
df = pd.DataFrame(
    {
        ONSET_DATE: np.tile(dates, 3),
        CASE_TYPE: np.repeat(["Confirmed", "Probable", "Suspect"], len(dates)),
        CASE_COUNT: np.concatenate([confirmed, probable, suspect]),
    }
)
df[EVENT] = df[ONSET_DATE].map(events).where(df[CASE_TYPE] == "Confirmed")

# Plot: reads only df and the constants above
table = df.astype({CASE_COUNT: float}).pivot_table(
    index=ONSET_DATE, columns=CASE_TYPE, values=CASE_COUNT, aggfunc="sum", sort=False
)
case_types = df[CASE_TYPE].unique()
total_per_day = table.sum(axis=1)
cumulative = total_per_day.cumsum()
marked = df.dropna(subset=[EVENT])

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_prop_cycle(color=IMPRINT_PALETTE)

bar_width = 0.8
bottom = np.zeros(len(table))
for case_type in case_types:
    ax.bar(
        table.index, table[case_type], width=bar_width, bottom=bottom, label=case_type, edgecolor=PAGE_BG, linewidth=0.3
    )
    bottom = bottom + table[case_type].to_numpy()

# Cumulative line on secondary axis
ax2 = ax.twinx()
ax2.plot(table.index, cumulative, color=CUMULATIVE_COLOR, linewidth=2.0, alpha=0.85, label="Cumulative")
ax2.fill_between(table.index, cumulative, alpha=0.07, color=CUMULATIVE_COLOR)
ax2.set_ylabel("Cumulative Cases", fontsize=10, color=CUMULATIVE_COLOR)
ax2.tick_params(axis="y", labelsize=8, colors=CUMULATIVE_COLOR, labelcolor=CUMULATIVE_COLOR)
ax2.spines["top"].set_visible(False)
ax2.spines["left"].set_visible(False)
ax2.spines["bottom"].set_visible(False)
ax2.spines["right"].set_color(CUMULATIVE_COLOR)

# Intervention annotation lines
text_stroke = [pe.withStroke(linewidth=2, foreground=PAGE_BG)]
y_label_pos = total_per_day.max() * 0.93
for event_date, event_label in zip(marked[ONSET_DATE], marked[EVENT], strict=True):
    ax.axvline(event_date, color=INK_MUTED, linestyle="--", linewidth=1.0, alpha=0.8)
    ax.text(
        event_date,
        y_label_pos,
        " " + event_label.replace("\n", "\n "),
        fontsize=7,
        color=INK_SOFT,
        va="top",
        ha="left",
        path_effects=text_stroke,
    )

# Style
title = "histogram-epidemic · python · matplotlib · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * 67 / n)) if n > 67 else 12

ax.set_xlabel(ONSET_DATE, fontsize=10, color=INK)
ax.set_ylabel(CASE_COUNT, fontsize=10, color=INK)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)
ax.set_axisbelow(True)

# Combined legend from both axes
lines_bars, labels_bars = ax.get_legend_handles_labels()
lines_cum, labels_cum = ax2.get_legend_handles_labels()
leg = ax.legend(lines_bars + lines_cum, labels_bars + labels_cum, fontsize=8, loc="upper left", framealpha=0.9)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Save — bbox_inches must stay default (None) to preserve exact 3200×1800 canvas
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
