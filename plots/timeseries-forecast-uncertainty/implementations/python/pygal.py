""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: pygal 3.1.3 | Python 3.14.10
Quality: 88/100 | Updated: 2026-11-08
"""

import os
import sys


# noqa: E402 - sys.path must be modified before imports to avoid module shadowing
sys.path[:] = [p for p in sys.path if p not in ("", ".", os.path.dirname(__file__))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

BRAND = "#009E73"  # historical observations
FORECAST_COLOR = "#C475FD"  # forecast line; its bands are translucent tints of the same lavender
BAND_95 = "rgba(196, 117, 253, 0.20)" if THEME == "light" else "rgba(196, 117, 253, 0.22)"
BAND_80 = "rgba(196, 117, 253, 0.45)" if THEME == "light" else "rgba(196, 117, 253, 0.42)"

# Constants
TICK_COUNT = 7  # about this many date ticks along the x axis

# Columns: set these to your table's column names
DATE = "Month"  # role: date
ACTUAL = "Monthly sales ($)"  # role: actual
FORECAST = "Forecast"  # role: forecast
LOWER_80 = "Lower 80%"  # role: lower_80
UPPER_80 = "Upper 80%"  # role: upper_80
LOWER_95 = "Lower 95%"  # role: lower_95
UPPER_95 = "Upper 95%"  # role: upper_95

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
np.random.seed(42)
months = 42
split_idx = 36

t = np.arange(split_idx)
actual = 1000 + 50 * t + 100 * np.sin(2 * np.pi * t / 12) + np.random.normal(0, 30, split_idx)

t_forecast = np.arange(split_idx, months)
forecast_values = actual[-1] + 30 * (t_forecast - split_idx) + 50 * np.sin(2 * np.pi * t_forecast / 12)

history_gap = np.full(split_idx, np.nan)
forecast_gap = np.full(months - split_idx, np.nan)
df = pd.DataFrame(
    {
        DATE: pd.date_range("2022-01-01", periods=months, freq="MS"),
        ACTUAL: np.concatenate([actual, forecast_gap]),
        FORECAST: np.concatenate([history_gap, forecast_values]),
        LOWER_80: np.concatenate([history_gap, forecast_values - 100]),
        UPPER_80: np.concatenate([history_gap, forecast_values + 100]),
        LOWER_95: np.concatenate([history_gap, forecast_values - 150]),
        UPPER_95: np.concatenate([history_gap, forecast_values + 150]),
    }
)

# Plot: rows numbered from 1 (no tick at 0, so pygal draws its left spine at the edge)
df = df.sort_values(DATE).reset_index(drop=True)
df["x"] = np.arange(1, len(df) + 1, dtype=float)
hist = df[df[ACTUAL].notna()]
fc = df[df[FORECAST].notna() & df[ACTUAL].isna()]
bands = fc.dropna(subset=[LOWER_80, UPPER_80, LOWER_95, UPPER_95])
origin = (float(hist["x"].iloc[-1]), float(hist[ACTUAL].iloc[-1]))  # forecast and bands start at the last observation

# Bands as polygons between their bounds (upper bound forward, lower bound back), starting at the origin:
# the 80% band, and the two strips of the 95% band outside it, so each colour has exactly one region
fc_x = [origin[0], *bands["x"]]
band_80 = list(zip(fc_x, [origin[1], *bands[UPPER_80]], strict=True)) + list(
    zip(fc_x[::-1], [*bands[LOWER_80][::-1], origin[1]], strict=True)
)
band_95_upper = list(zip(fc_x, [origin[1], *bands[UPPER_95]], strict=True)) + list(
    zip(fc_x[::-1], [*bands[UPPER_80][::-1], origin[1]], strict=True)
)
band_95_lower = list(zip(fc_x, [origin[1], *bands[LOWER_80]], strict=True)) + list(
    zip(fc_x[::-1], [*bands[LOWER_95][::-1], origin[1]], strict=True)
)

# A 1-2-5 tick step giving about ten y ticks across the data and both 95% bounds
data_lo = np.nanmin([df[ACTUAL].min(), df[LOWER_95].min()])
data_hi = np.nanmax([df[ACTUAL].max(), df[UPPER_95].max()])
raw_step = (data_hi - data_lo) / 10
magnitude = 10 ** np.floor(np.log10(raw_step))
STEP = magnitude * next(m for m in (1, 2, 5, 10) if m * magnitude >= raw_step)
y_lo = np.floor(data_lo / STEP) * STEP
y_hi = np.ceil(data_hi / STEP) * STEP + STEP / 2
# The forecast-start line and its caption are drawn only when the table holds a forecast period
forecast_start = float(fc["x"].iloc[0]) if len(fc) else None
marker = [(forecast_start, y_lo), (forecast_start, y_hi)] if len(fc) else []
caption = [{"value": (forecast_start + 0.15, y_hi - STEP / 4), "label": "Forecast →"}] if len(fc) else []
tick_every = max(1, round(len(df) / TICK_COUNT))

LABEL_FS = 40
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(INK, BAND_95, BAND_95, BAND_80, INK_SOFT, BRAND, FORECAST_COLOR),
    value_colors=(INK,) * 7,
    opacity=1,
    opacity_hover=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=5,
    guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_color=RULE,
    major_guide_stroke_dasharray="none",
    title_font_size=60,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=42,
    # pygal prints a point's label value_font_size px right of it and 4/3 of that below it;
    # at 0.26 x the label size the text sits vertically centred on its point
    value_font_size=round(0.26 * LABEL_FS),
    value_label_font_size=LABEL_FS,
    tooltip_font_size=34,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="timeseries-forecast-uncertainty · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title=ACTUAL,
    show_x_guides=False,
    show_y_guides=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,  # one row; pygal counts the untitled series too when it reserves legend rows
    legend_box_size=36,
    truncate_legend=-1,
    xrange=(float(df["x"].iloc[0]), float(df["x"].iloc[-1]) + 0.5),
    range=(float(y_lo), float(y_hi)),
    print_labels=True,
    print_values=False,
    margin=40,
    spacing=24,
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.serie-1 .line, .serie-2 .line, .serie-3 .line { stroke-width: 0 !important; }",
        "inline:.serie-4 .line { stroke-width: 3px !important; }",
        "inline:.text-overlay text.label { font-weight: bold; }",
        "inline:.plot_title { font-weight: bold; }",
        # pygal sets legend text only 5 px right of its swatch; push it clear of the box
        "inline:.legends .legend text { transform: translate(14px, 0px); }",
        # The dashed series get dashed outline swatches instead of solid squares
        "inline:#activate-serie-4 rect, #activate-serie-6 rect "
        "{ fill: none !important; stroke-width: 5px; stroke-dasharray: 9, 5; }",
        f"inline:#activate-serie-4 rect {{ stroke: {INK_SOFT} !important; }}",
        f"inline:#activate-serie-6 rect {{ stroke: {FORECAST_COLOR} !important; }}",
    ),
)
chart.x_labels = [
    {"value": int(row["x"]), "label": row[DATE].strftime("%b %y")} for _, row in df.iloc[::tick_every].iterrows()
]

# Label first and bands next, so the lines are drawn on top of the fills
chart.add(None, caption, stroke=False, dots_size=0)
chart.add("95% interval", band_95_upper, fill=True, show_dots=False)
chart.add(None, band_95_lower, fill=True, show_dots=False)
chart.add("80% interval", band_80, fill=True, show_dots=False)
chart.add("Forecast start", marker, show_dots=False, stroke_style={"dasharray": "14, 10"})
chart.add(
    "Observed history",
    list(zip(hist["x"], hist[ACTUAL], strict=True)),
    dots_size=5,
    formatter=lambda p: f"${p[1]:,.0f}",
)
chart.add(
    FORECAST,
    [origin, *zip(fc["x"], fc[FORECAST], strict=True)],
    dots_size=5,
    stroke_style={"dasharray": "22, 12"},
    formatter=lambda p: f"${p[1]:,.0f}",
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
