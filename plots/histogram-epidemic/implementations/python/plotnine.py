"""anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-02
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

# Data — two-wave epidemic model (point-source → propagated transmission)
np.random.seed(42)

start_date = pd.Timestamp("2024-01-15")
dates = pd.date_range(start_date, periods=90, freq="D")
days = np.arange(90)

confirmed_rate = (
    45 * np.exp(-0.5 * ((days - 18) / 5) ** 2) + 25 * np.exp(-0.5 * ((days - 55) / 10) ** 2) + np.random.poisson(2, 90)
)
probable_rate = (
    15 * np.exp(-0.5 * ((days - 20) / 6) ** 2) + 10 * np.exp(-0.5 * ((days - 57) / 11) ** 2) + np.random.poisson(1, 90)
)
suspect_rate = (
    8 * np.exp(-0.5 * ((days - 22) / 7) ** 2) + 5 * np.exp(-0.5 * ((days - 60) / 12) ** 2) + np.random.poisson(1, 90)
)

confirmed = np.maximum(confirmed_rate.astype(int), 0)
probable = np.maximum(probable_rate.astype(int), 0)
suspect = np.maximum(suspect_rate.astype(int), 0)

df = pd.DataFrame(
    {
        "onset_date": np.tile(dates, 3),
        "case_count": np.concatenate([confirmed, probable, suspect]),
        "case_type": ["Confirmed"] * 90 + ["Probable"] * 90 + ["Suspect"] * 90,
    }
)
df["case_type"] = pd.Categorical(df["case_type"], categories=["Suspect", "Probable", "Confirmed"], ordered=True)

daily_totals = df.groupby("onset_date")["case_count"].sum().reset_index()
daily_totals["cumulative"] = daily_totals["case_count"].cumsum()
max_daily = daily_totals["case_count"].max()
max_cumulative = int(daily_totals["cumulative"].max())
daily_totals["cumulative_scaled"] = daily_totals["cumulative"] / max_cumulative * max_daily

lockdown_date = pd.Timestamp("2024-02-10")
vaccination_date = pd.Timestamp("2024-03-01")
interventions = pd.DataFrame(
    {"date": [lockdown_date, vaccination_date], "label": ["Lockdown", "Vaccination\ncampaign"]}
)

wave1_idx = daily_totals.loc[daily_totals["onset_date"] < "2024-03-01", "case_count"].idxmax()
wave2_idx = daily_totals.loc[daily_totals["onset_date"] >= "2024-03-01", "case_count"].idxmax()
wave1_date = daily_totals.loc[wave1_idx, "onset_date"]
wave1_peak = daily_totals.loc[wave1_idx, "case_count"]
wave2_date = daily_totals.loc[wave2_idx, "onset_date"]
wave2_peak = daily_totals.loc[wave2_idx, "case_count"]

cumul_label = f"Cumulative: {max_cumulative:,} cases →"

# Plot
title = "histogram-epidemic · python · plotnine · anyplot.ai"

plot = (
    ggplot(df, aes(x="onset_date", y="case_count"))
    + geom_col(aes(fill="case_type"), width=1.0)
    + geom_line(
        data=daily_totals,
        mapping=aes(x="onset_date", y="cumulative_scaled"),
        color=IMPRINT_PALETTE[3],
        size=1.5,
        alpha=0.9,
    )
    + geom_vline(
        data=interventions, mapping=aes(xintercept="date"), linetype="dashed", color=INK_SOFT, size=0.5, alpha=0.8
    )
    + geom_text(
        data=interventions,
        mapping=aes(x="date", label="label"),
        y=max_daily * 0.88,
        ha="left",
        nudge_x=1.5,
        size=4,
        color=INK_MUTED,
        fontstyle="italic",
    )
    + annotate(
        "text",
        x=dates[-1],
        y=daily_totals["cumulative_scaled"].iloc[-1] * 1.03,
        label=cumul_label,
        ha="right",
        va="bottom",
        size=3.5,
        color=IMPRINT_PALETTE[3],
        fontstyle="italic",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=wave1_date,
        y=wave1_peak + 3,
        label=f"Wave 1 peak\n{wave1_peak} cases/day",
        ha="center",
        va="bottom",
        size=3.5,
        color=INK,
        fontweight="bold",
    )
    + annotate(
        "text",
        x=wave2_date,
        y=wave2_peak + 3,
        label=f"Wave 2 peak\n{wave2_peak} cases/day",
        ha="center",
        va="bottom",
        size=3.5,
        color=INK,
        fontweight="bold",
    )
    + scale_fill_manual(
        values={"Confirmed": IMPRINT_PALETTE[0], "Probable": IMPRINT_PALETTE[1], "Suspect": IMPRINT_PALETTE[2]}
    )
    + scale_x_date(date_breaks="2 weeks", date_labels="%b %d")
    + scale_y_continuous(expand=(0, 0, 0.12, 0))
    + labs(x="Date of Symptom Onset", y="Number of New Cases (per day)", fill="Case Classification", title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(rotation=45, ha="right", color=INK_SOFT),
        plot_title=element_text(size=13, color=INK, fontweight="bold"),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_position="top",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
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
