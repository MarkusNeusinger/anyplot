"""anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
"""
# ruff: noqa: F405

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
INK_GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

ALPHA_95 = 0.24 if THEME == "light" else 0.35
ALPHA_80 = 0.38 if THEME == "light" else 0.55

# Constants
DATE = "Date"  # role: date
ACTUAL = "Historical"  # role: actual
FORECAST = "Forecast"  # role: forecast
LOWER_80 = "Lower 80%"  # role: lower_80
UPPER_80 = "Upper 80%"  # role: upper_80
LOWER_95 = "Lower 95%"  # role: lower_95
UPPER_95 = "Upper 95%"  # role: upper_95
VALUE_LABEL = "Energy Demand (MWh)"
VALUE, SERIES, BAND, LOW, HIGH = "value", "series", "band", "low", "high"  # long-form helper columns

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
# Monthly energy demand: 36 months history + 12 month forecast
np.random.seed(42)
dates_hist = pd.date_range("2023-01-01", periods=36, freq="MS")
trend = np.linspace(420, 510, 36)
seasonal = 40 * np.sin(np.linspace(0, 6 * np.pi, 36))
noise = np.random.normal(0, 12, 36)
actual = trend + seasonal + noise

dates_forecast = pd.date_range("2026-01-01", periods=12, freq="MS")
trend_fc = np.linspace(510, 545, 12)
seasonal_fc = 40 * np.sin(np.linspace(6 * np.pi, 8 * np.pi, 12))
forecast = trend_fc + seasonal_fc
uncertainty_80 = np.linspace(18, 45, 12)
uncertainty_95 = np.linspace(28, 68, 12)

df = pd.concat(
    [
        pd.DataFrame({DATE: dates_hist, ACTUAL: actual}),
        pd.DataFrame(
            {
                DATE: dates_forecast,
                FORECAST: forecast,
                LOWER_80: forecast - uncertainty_80,
                UPPER_80: forecast + uncertainty_80,
                LOWER_95: forecast - uncertainty_95,
                UPPER_95: forecast + uncertainty_95,
            }
        ),
    ],
    ignore_index=True,
)

# Plot
fc = df[df[FORECAST].notna()]
hist = df[df[ACTUAL].notna()]
forecast_start = fc[DATE].min()

# Long-form frames so every series and confidence level gets its own legend entry
hist_line = pd.DataFrame({DATE: hist[DATE], VALUE: hist[ACTUAL], SERIES: ACTUAL})
fc_line = pd.DataFrame({DATE: fc[DATE], VALUE: fc[FORECAST], SERIES: FORECAST})
band_95 = pd.DataFrame({DATE: fc[DATE], LOW: fc[LOWER_95], HIGH: fc[UPPER_95], BAND: "95% CI"})
band_80 = pd.DataFrame({DATE: fc[DATE], LOW: fc[LOWER_80], HIGH: fc[UPPER_80], BAND: "80% CI"})

plot = (
    ggplot()
    # 95% CI (outer, lighter) then 80% CI (inner, darker)
    + geom_ribbon(aes(x=DATE, ymin=LOW, ymax=HIGH, fill=BAND, alpha=BAND), data=band_95, size=0)
    + geom_ribbon(aes(x=DATE, ymin=LOW, ymax=HIGH, fill=BAND, alpha=BAND), data=band_80, size=0)
    # Historical solid line, tooltips show value on hover in HTML
    + geom_line(
        aes(x=DATE, y=VALUE, color=SERIES),
        data=hist_line,
        size=1.2,
        linetype="solid",
        tooltips=layer_tooltips().line(f"@{{{VALUE}}}{{.0f}} MWh").line(f"@{{{DATE}}}"),
    )
    # Forecast dashed line
    + geom_line(
        aes(x=DATE, y=VALUE, color=SERIES),
        data=fc_line,
        size=1.2,
        linetype="dashed",
        tooltips=layer_tooltips().line(f"Forecast: @{{{VALUE}}}{{.0f}} MWh").line(f"@{{{DATE}}}"),
    )
    + scale_color_manual(values={ACTUAL: IMPRINT_PALETTE[0], FORECAST: IMPRINT_PALETTE[1]}, name="")
    + scale_fill_manual(values={"80% CI": IMPRINT_PALETTE[1], "95% CI": IMPRINT_PALETTE[1]}, name="")
    + scale_alpha_manual(values={"80% CI": ALPHA_80, "95% CI": ALPHA_95}, name="")
    + labs(x=DATE, y=VALUE_LABEL, title="timeseries-forecast-uncertainty · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + theme_classic()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=INK_GRID, size=0.5),
        axis_title=element_text(color=INK, size=12),
        axis_text=element_text(color=INK_SOFT, size=10),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(color=INK, size=16),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=10),
        legend_title=element_blank(),
        legend_position="bottom",
    )
)

# Vertical marker at forecast boundary (datetime axis is in milliseconds)
if pd.notna(forecast_start):
    plot += geom_vline(xintercept=forecast_start.timestamp() * 1000, color=INK_MUTED, size=0.6, linetype="dotted")

# Save PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
