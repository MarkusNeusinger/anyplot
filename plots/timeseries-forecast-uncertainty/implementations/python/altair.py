""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: altair 6.3.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 1 for the history, position 2 for the forecast
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Band opacities: the purple reads heavier on the dark surface, so the fills are lighter there
BAND_80_OPACITY = 0.30 if THEME == "light" else 0.20
BAND_95_OPACITY = 0.15 if THEME == "light" else 0.10
LEGEND_LABELS = ["Historical Data", "Forecast", "80% CI", "95% CI"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
SALES = "Sales (thousands USD)"  # role: actual
FORECAST = "Forecast (thousands USD)"  # role: forecast
LOWER_80 = "Lower 80% bound"  # role: lower_80
UPPER_80 = "Upper 80% bound"  # role: upper_80
LOWER_95 = "Lower 95% bound"  # role: lower_95
UPPER_95 = "Upper 95% bound"  # role: upper_95

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
# Monthly sales: 36 months of history, then a 12-month forecast with widening bounds
np.random.seed(42)
history_dates = pd.date_range("2021-01-01", periods=36, freq="MS")
history = np.linspace(100, 180, 36) + 15 * np.sin(np.linspace(0, 6 * np.pi, 36)) + np.random.normal(0, 8, 36)
future_dates = pd.date_range("2024-01-01", periods=12, freq="MS")
future = np.linspace(180, 210, 12) + 15 * np.sin(np.linspace(6 * np.pi, 8 * np.pi, 12))
spread = np.linspace(5, 20, 12)
df = pd.DataFrame(
    {
        DATE: history_dates.append(future_dates),
        SALES: np.concatenate([history, np.full(12, np.nan)]),
        FORECAST: np.concatenate([np.full(36, np.nan), future]),
        LOWER_80: np.concatenate([np.full(36, np.nan), future - 1.28 * spread]),
        UPPER_80: np.concatenate([np.full(36, np.nan), future + 1.28 * spread]),
        LOWER_95: np.concatenate([np.full(36, np.nan), future - 1.96 * spread]),
        UPPER_95: np.concatenate([np.full(36, np.nan), future + 1.96 * spread]),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
field = {name: name.translate(ESCAPE) for name in df.columns}

observed = df[df[SALES].notna()]
projected = df[df[FORECAST].notna()]
forecast_start = projected[DATE].min()

bounds = df.drop(columns=[DATE]).to_numpy(dtype=float)
y_low, y_high = np.nanmin(bounds), np.nanmax(bounds)
pad = (y_high - y_low) * 0.1
y_scale = alt.Scale(domain=[y_low - pad, y_high + pad * 1.5])
x_axis = alt.Axis(title=DATE, format="%Y", tickCount="year")


def band(lower, upper, opacity):
    return (
        alt.Chart(projected)
        .mark_area(opacity=opacity)
        .encode(
            x=alt.X(field[DATE], type="temporal", axis=x_axis),
            y=alt.Y(field[lower], type="quantitative", scale=y_scale),
            y2=alt.Y2(field[upper]),
            color=alt.value(IMPRINT_PALETTE[1]),
        )
    )


# Widest band first so the narrower one sits on top
band_95 = band(LOWER_95, UPPER_95, BAND_95_OPACITY)
band_80 = band(LOWER_80, UPPER_80, BAND_80_OPACITY)

# Historical line (solid); invisible overlay points enable HTML tooltips
historical_line = (
    alt.Chart(observed)
    .mark_line(strokeWidth=3, point=alt.OverlayMarkDef(size=50, opacity=0))
    .encode(
        x=alt.X(field[DATE], type="temporal", axis=x_axis),
        y=alt.Y(field[SALES], type="quantitative", title=SALES, scale=y_scale),
        color=alt.value(IMPRINT_PALETTE[0]),
        tooltip=[
            alt.Tooltip(field[DATE], type="temporal", title=DATE, format="%b %Y"),
            alt.Tooltip(field[SALES], type="quantitative", title=SALES, format=".1f"),
        ],
    )
)

# Forecast line (dashed); the tooltip surfaces the 80% bounds
forecast_line = (
    alt.Chart(projected)
    .mark_line(strokeWidth=3, strokeDash=[8, 4], point=alt.OverlayMarkDef(size=50, opacity=0))
    .encode(
        x=alt.X(field[DATE], type="temporal", axis=x_axis),
        y=alt.Y(field[FORECAST], type="quantitative", scale=y_scale),
        color=alt.value(IMPRINT_PALETTE[1]),
        tooltip=[
            alt.Tooltip(field[DATE], type="temporal", title=DATE, format="%b %Y"),
            alt.Tooltip(field[FORECAST], type="quantitative", title=FORECAST, format=".1f"),
            alt.Tooltip(field[LOWER_80], type="quantitative", title=LOWER_80, format=".1f"),
            alt.Tooltip(field[UPPER_80], type="quantitative", title=UPPER_80, format=".1f"),
        ],
    )
)

# Vertical rule at the first forecast date
vertical_rule = (
    alt.Chart(pd.DataFrame({DATE: [forecast_start]}))
    .mark_rule(strokeWidth=2, strokeDash=[6, 3], color=INK_SOFT)
    .encode(x=alt.X(field[DATE], type="temporal"))
)

# Annotation at the top of the forecast region
annotation_df = pd.DataFrame(
    {DATE: [forecast_start + pd.DateOffset(months=1)], "y": [y_high + pad], "label": ["Forecast period →"]}
)
forecast_annotation = (
    alt.Chart(annotation_df)
    .mark_text(align="left", fontSize=12, fontStyle="italic")
    .encode(
        x=alt.X(field[DATE], type="temporal"), y=alt.Y("y:Q", scale=y_scale), text="label:N", color=alt.value(INK_MUTED)
    )
)

# Legend via invisible size-0 points: fixed-color layers have no legend of their own
legend_df = pd.DataFrame({DATE: [forecast_start] * len(LEGEND_LABELS), "type": LEGEND_LABELS})
legend_chart = (
    alt.Chart(legend_df)
    .mark_point(size=0)
    .encode(
        x=alt.X(field[DATE], type="temporal"),
        color=alt.Color(
            "type:N",
            scale=alt.Scale(
                domain=LEGEND_LABELS,
                range=[
                    IMPRINT_PALETTE[0],
                    IMPRINT_PALETTE[1],
                    "rgba(196, 117, 253, 0.60)",
                    "rgba(196, 117, 253, 0.25)",
                ],
            ),
            legend=alt.Legend(title="Series", orient="right", titleFontSize=12, labelFontSize=10),
        ),
    )
)

chart = (
    alt.layer(band_95, band_80, historical_line, forecast_line, vertical_rule, forecast_annotation, legend_chart)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "timeseries-forecast-uncertainty · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            color=INK,
            subtitle="Monthly Sales with 80% and 95% Confidence Intervals",
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        labelColor=INK_SOFT,
        titleColor=INK,
        domain=False,
        tickSize=0,
        gridColor=INK,
        gridOpacity=0.10,
    )
    .configure_axisX(grid=False)
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(
        titleFontSize=12,
        labelFontSize=10,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the PNG up to the canonical 3200 x 1800 canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
if img.size != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
