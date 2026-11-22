""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-22
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
    geom_line,
    geom_ribbon,
    geom_vline,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_linetype_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column names, written the way the axis and legend should read
DATE = "Week"  # role: date
ACTUAL = "Observed"  # role: actual
FORECAST = "Forecast"  # role: forecast
LOWER_80 = "Lower 80%"  # role: lower_80
UPPER_80 = "Upper 80%"  # role: upper_80
LOWER_95 = "Lower 95%"  # role: lower_95
UPPER_95 = "Upper 95%"  # role: upper_95
VISITS_LABEL = "Website visits (thousand per week)"

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
# Weekly website traffic: 2 years of history with a step change at a campaign launch,
# then a damped-growth forecast for the next 16 weeks.
rng = np.random.default_rng(7)
n_hist, n_fc = 104, 16
weeks = pd.date_range("2023-01-02", periods=n_hist + n_fc, freq="W-MON")
t = np.arange(n_hist)
level = 42 + 0.12 * t + 24 * (t >= 62)
season = 4 * np.sin(2 * np.pi * (t - 8) / 52)
observed = level + season + rng.normal(0, 2.2, n_hist)

horizon = np.arange(0, n_fc + 1)
damped_growth = 0.9 * 6 * (1 - 0.88**horizon)
seasonal_shift = 4 * (np.sin(2 * np.pi * (n_hist - 1 + horizon - 8) / 52) - np.sin(2 * np.pi * (n_hist - 1 - 8) / 52))
fc = observed[-1] + damped_growth + seasonal_shift
spread = 2.4 * np.sqrt(horizon)

df = pd.DataFrame(
    {
        DATE: weeks[n_hist - 1 :].union(weeks[:n_hist]),
        ACTUAL: np.r_[observed, np.full(n_fc, np.nan)],
        FORECAST: np.r_[np.full(n_hist - 1, np.nan), fc],
        LOWER_80: np.r_[np.full(n_hist - 1, np.nan), fc - 1.28 * spread],
        UPPER_80: np.r_[np.full(n_hist - 1, np.nan), fc + 1.28 * spread],
        LOWER_95: np.r_[np.full(n_hist - 1, np.nan), fc - 1.96 * spread],
        UPPER_95: np.r_[np.full(n_hist - 1, np.nan), fc + 1.96 * spread],
    }
)

# Plot
SERIES, VALUE, LEVEL, LOW, HIGH = "Series", "Value", "Interval", "Low", "High"
LEVEL_95, LEVEL_80 = "95% interval", "80% interval"

lines = df.melt(id_vars=DATE, value_vars=[ACTUAL, FORECAST], var_name=SERIES, value_name=VALUE).dropna()
bands_in = df.dropna(subset=[FORECAST])
bands = pd.concat(
    [
        pd.DataFrame({DATE: bands_in[DATE], LOW: bands_in[LOWER_95], HIGH: bands_in[UPPER_95], LEVEL: LEVEL_95}),
        pd.DataFrame({DATE: bands_in[DATE], LOW: bands_in[LOWER_80], HIGH: bands_in[UPPER_80], LEVEL: LEVEL_80}),
    ]
)
series_order = [ACTUAL, FORECAST]
forecast_start = df.loc[df[ACTUAL].notna(), DATE].max()
label_x = forecast_start + pd.Timedelta(weeks=1)
label_y = df[UPPER_95].max()

plot = (
    ggplot()
    + geom_ribbon(data=bands[bands[LEVEL] == LEVEL_95], mapping=aes(x=DATE, ymin=LOW, ymax=HIGH, fill=LEVEL))
    + geom_ribbon(data=bands[bands[LEVEL] == LEVEL_80], mapping=aes(x=DATE, ymin=LOW, ymax=HIGH, fill=LEVEL))
    + geom_vline(xintercept=forecast_start, linetype="dashed", color=INK_SOFT, size=0.8)
    + annotate("text", x=label_x, y=label_y, label="Forecast →", color=INK_MUTED, size=7, ha="left")
    + geom_line(data=lines, mapping=aes(x=DATE, y=VALUE, color=SERIES, linetype=SERIES), size=1.5)
    + scale_color_manual(values=IMPRINT_PALETTE[:2], limits=series_order)
    + scale_linetype_manual(values=["solid", "dashed"], limits=series_order)
    + scale_fill_manual(values=[IMPRINT_PALETTE[2] + "70", IMPRINT_PALETTE[2] + "33"], limits=[LEVEL_80, LEVEL_95])
    + guides(
        color=guide_legend(title="", order=1),
        linetype=guide_legend(title="", order=1),
        fill=guide_legend(title="Confidence band", order=2),
    )
    + labs(
        x=DATE,
        y=VISITS_LABEL,
        title="timeseries-forecast-uncertainty · python · plotnine · anyplot.ai",
        subtitle="Weekly traffic after the campaign step change; bands widen with forecast horizon",
    )
    + scale_x_datetime(date_breaks="6 months", date_labels="%b %Y")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.1),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(angle=45, ha="right"),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=12, color=INK, weight="medium"),
        plot_subtitle=element_text(size=9, color=INK_MUTED),
        legend_position="top",
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
