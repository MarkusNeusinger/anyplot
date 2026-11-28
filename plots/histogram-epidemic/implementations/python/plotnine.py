"""anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-02
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_line,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_date,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — positions 1-3 for stacked case types; position 4 for cumulative line
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ONSET_DATE = "Date of Symptom Onset"  # role: onset_date
CASE_COUNT = "Number of New Cases (per day)"  # role: case_count
CASE_TYPE = "Case Classification"  # role: case_type
EVENT_DATE = "Intervention date"  # role: events
EVENT_LABEL = "Intervention"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("cases.csv")
# Event columns are filled only on the first rows (one row per intervention); the rest stay empty.
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-01-15", periods=n_days, freq="D")
days = np.arange(n_days)

confirmed = (
    45 * np.exp(-0.5 * ((days - 18) / 5) ** 2)
    + 25 * np.exp(-0.5 * ((days - 55) / 10) ** 2)
    + np.random.poisson(2, n_days)
).astype(int)
probable = (
    15 * np.exp(-0.5 * ((days - 20) / 6) ** 2)
    + 10 * np.exp(-0.5 * ((days - 57) / 11) ** 2)
    + np.random.poisson(1, n_days)
).astype(int)
suspect = (
    8 * np.exp(-0.5 * ((days - 22) / 7) ** 2)
    + 5 * np.exp(-0.5 * ((days - 60) / 12) ** 2)
    + np.random.poisson(1, n_days)
).astype(int)

df = pd.DataFrame(
    {
        ONSET_DATE: np.tile(dates, 3),
        CASE_COUNT: np.concatenate([confirmed, probable, suspect]),
        CASE_TYPE: np.repeat(["Confirmed", "Probable", "Suspect"], n_days),
        EVENT_DATE: pd.Series([pd.Timestamp("2024-02-10"), pd.Timestamp("2024-03-01")]).reindex(range(3 * n_days)),
        EVENT_LABEL: pd.Series(["Lockdown", "Vaccination\ncampaign"]).reindex(range(3 * n_days)),
    }
)

# Plot
# Stack order: first group in the data sits at the bottom of every bar
groups = df[CASE_TYPE].dropna().unique().tolist()
df[CASE_TYPE] = pd.Categorical(df[CASE_TYPE], categories=groups[::-1], ordered=True)

events = df[[EVENT_DATE, EVENT_LABEL]].dropna()
daily = df.groupby(ONSET_DATE, as_index=False)[CASE_COUNT].sum()
daily["cumulative"] = daily[CASE_COUNT].cumsum()
max_daily = daily[CASE_COUNT].max()
max_cumulative = int(daily["cumulative"].max())
# plotnine has no secondary axis: the cumulative line is rescaled onto the daily axis and labeled directly
daily["cumulative_scaled"] = daily["cumulative"] / max_cumulative * max_daily

# Waves are split at the middle of the observed period
wave_split = daily[ONSET_DATE].min() + (daily[ONSET_DATE].max() - daily[ONSET_DATE].min()) / 2
wave1 = daily[daily[ONSET_DATE] < wave_split]
wave2 = daily[daily[ONSET_DATE] >= wave_split]
wave1_peak = wave1.loc[wave1[CASE_COUNT].idxmax()]
wave2_peak = wave2.loc[wave2[CASE_COUNT].idxmax()]

cumul_label = f"Cumulative: {max_cumulative:,} cases →"

title = "histogram-epidemic · python · plotnine · anyplot.ai"

plot = (
    ggplot(df, aes(x=ONSET_DATE, y=CASE_COUNT))
    + geom_col(aes(fill=CASE_TYPE), width=1.0)
    + geom_line(
        data=daily, mapping=aes(x=ONSET_DATE, y="cumulative_scaled"), color=IMPRINT_PALETTE[3], size=1.5, alpha=0.9
    )
    + geom_vline(
        data=events, mapping=aes(xintercept=EVENT_DATE), linetype="dashed", color=INK_SOFT, size=0.5, alpha=0.8
    )
    + geom_text(
        data=events,
        mapping=aes(x=EVENT_DATE, label=EVENT_LABEL),
        y=max_daily * 0.88,
        ha="left",
        nudge_x=1.5,
        size=6,
        color=INK_MUTED,
        fontstyle="italic",
    )
    + annotate(
        "text",
        x=daily[ONSET_DATE].iloc[-1],
        y=daily["cumulative_scaled"].iloc[-1] * 1.03,
        label=cumul_label,
        ha="right",
        va="bottom",
        size=6,
        color=IMPRINT_PALETTE[3],
        fontstyle="italic",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=wave1_peak[ONSET_DATE],
        y=wave1_peak[CASE_COUNT] + 3,
        label=f"Wave 1 peak\n{wave1_peak[CASE_COUNT]} cases/day",
        ha="center",
        va="bottom",
        size=6,
        color=INK,
        fontweight="bold",
    )
    + annotate(
        "text",
        x=wave2_peak[ONSET_DATE],
        y=wave2_peak[CASE_COUNT] + 3,
        label=f"Wave 2 peak\n{wave2_peak[CASE_COUNT]} cases/day",
        ha="center",
        va="bottom",
        size=6,
        color=INK,
        fontweight="bold",
    )
    + scale_fill_manual(values=dict(zip(groups, IMPRINT_PALETTE, strict=False)), limits=groups)
    + scale_x_date(date_breaks="2 weeks", date_labels="%b %d")
    + scale_y_continuous(expand=(0, 0, 0.12, 0))
    + labs(title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(rotation=45, ha="right", color=INK_SOFT),
        plot_title=element_text(size=12, color=INK, fontweight="bold"),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_position="top",
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        panel_border=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_line_y=element_line(color=INK_SOFT, size=0.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
