"""anyplot.ai
drawdown-basic: Drawdown Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-23
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

DD_COLOR = "#AE3030"  # Imprint palette pos 3 — semantic: loss/drawdown
REC_COLOR = "#009E73"  # Imprint palette pos 1 — semantic: recovery/new high

# Constants
DATE = "date"  # role: date
PRICE = "price"  # role: price
DRAWDOWN = "Drawdown (%)"  # derived below the Data block
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
DATE_F, PRICE_F, DD_F = (c.translate(ESCAPE) for c in (DATE, PRICE, DRAWDOWN))

# Data: simulated asset price over ~2 years with drawdowns and recoveries
np.random.seed(42)
returns = np.random.normal(0.001, 0.01, 500)

returns[0:30] = np.random.normal(0.002, 0.008, 30)  # initial rally
returns[30:50] = np.random.normal(-0.012, 0.012, 20)  # correction ~20%
returns[50:90] = np.random.normal(0.008, 0.008, 40)  # recovery to new highs
returns[100:130] = np.random.normal(-0.015, 0.015, 30)  # deeper correction ~30%
returns[130:200] = np.random.normal(0.006, 0.009, 70)  # recovery to new highs
returns[220:270] = np.random.normal(-0.01, 0.012, 50)  # extended decline ~35%
returns[270:350] = np.random.normal(0.005, 0.008, 80)  # gradual recovery
returns[380:410] = np.random.normal(-0.008, 0.01, 30)  # late correction ~15%
returns[410:480] = np.random.normal(0.004, 0.007, 70)  # final recovery

df = pd.DataFrame({DATE: pd.date_range("2022-01-01", periods=500, freq="D"), PRICE: 100 * np.cumprod(1 + returns)})

# Plot
dd = df[[DATE]].copy()
dd[DRAWDOWN] = (df[PRICE] / df[PRICE].cummax() - 1) * 100

# Max drawdown stats
max_dd_idx = dd[DRAWDOWN].idxmin()
max_dd_date = dd.loc[max_dd_idx, DATE]
max_dd_value = dd.loc[max_dd_idx, DRAWDOWN]
max_drawdown_pct = abs(max_dd_value)

# Drawdown duration (peak → trough)
at_peak = dd.loc[:max_dd_idx][dd.loc[:max_dd_idx, DRAWDOWN] == 0]
dd_start_date = at_peak.iloc[-1][DATE] if not at_peak.empty else dd[DATE].iloc[0]
dd_duration_days = (max_dd_date - dd_start_date).days

# Recovery (trough → next new high)
after_trough = dd[dd.index > max_dd_idx]
recovered = after_trough[after_trough[DRAWDOWN] >= 0]
recovery_days = int((recovered.iloc[0][DATE] - max_dd_date).days) if not recovered.empty else None
recovery_str = f"{recovery_days}d" if recovery_days else "ongoing"

# Recovery points: first new high after any drawdown deeper than -5%
is_new_high = (dd[DRAWDOWN] >= 0) & (dd[DRAWDOWN].shift(1) < 0)
rec_indices = []
last_low = 0.0
for idx in dd.index:
    last_low = min(last_low, dd.at[idx, DRAWDOWN])
    if is_new_high[idx] and last_low < -5:
        rec_indices.append(idx)
        last_low = 0.0

recovery_points = dd.loc[rec_indices, [DATE, DRAWDOWN]].reset_index(drop=True)
recovery_points["series"] = "New High"

max_dd_df = pd.DataFrame({DATE: [max_dd_date], DRAWDOWN: [max_dd_value], "label": [f"Max DD: {max_drawdown_pct:.1f}%"]})

title_str = "drawdown-basic · python · altair · anyplot.ai"
subtitle_str = f"Max Drawdown: {max_drawdown_pct:.1f}%  ·  Duration: {dd_duration_days}d  ·  Recovery: {recovery_str}"

# Plot layers
area = (
    alt.Chart(dd)
    .mark_area(opacity=0.45, color=DD_COLOR)
    .encode(
        x=alt.X(DATE_F, type="temporal", title="Date", axis=alt.Axis(format="%b %Y")),
        y=alt.Y(
            DD_F,
            type="quantitative",
            title=DRAWDOWN,
            scale=alt.Scale(domain=[dd[DRAWDOWN].min() * 1.15, -dd[DRAWDOWN].min() * 0.12]),
        ),
    )
)

dd_line = (
    alt.Chart(dd)
    .mark_line(color=DD_COLOR, strokeWidth=2)
    .encode(x=alt.X(DATE_F, type="temporal"), y=alt.Y(DD_F, type="quantitative"))
)

zero_rule = (
    alt.Chart(pd.DataFrame({"y": [0]}))
    .mark_rule(strokeDash=[5, 4], strokeWidth=1.5)
    .encode(y="y:Q", color=alt.value(INK_SOFT))
)

max_dd_point = (
    alt.Chart(max_dd_df)
    .mark_point(size=250, color="#C475FD", filled=True, stroke=INK, strokeWidth=1.5)
    .encode(x=alt.X(DATE_F, type="temporal"), y=alt.Y(DD_F, type="quantitative"))
)

max_dd_label = (
    alt.Chart(max_dd_df)
    .mark_text(align="left", dx=12, dy=-8, fontSize=11, fontWeight="bold")
    .encode(
        x=alt.X(DATE_F, type="temporal"),
        y=alt.Y(DD_F, type="quantitative"),
        text=alt.Text("label", type="nominal"),
        color=alt.value(INK),
    )
)

layers = [area, dd_line, zero_rule, max_dd_point, max_dd_label]

if len(recovery_points) > 0:
    recovery_markers = (
        alt.Chart(recovery_points)
        .mark_point(shape="triangle-up", filled=True, size=150, stroke=PAGE_BG, strokeWidth=1)
        .encode(
            x=alt.X(DATE_F, type="temporal"),
            y=alt.Y(DD_F, type="quantitative"),
            color=alt.Color(
                "series",
                type="nominal",
                scale=alt.Scale(range=[REC_COLOR]),
                legend=alt.Legend(title="", orient="top-right"),
            ),
            tooltip=[alt.Tooltip(DATE_F, type="temporal", title="New High", format="%Y-%m-%d")],
        )
    )
    layers.append(recovery_markers)

chart = (
    alt.layer(*layers)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(
            title_str,
            fontSize=16,
            color=INK,
            anchor="start",
            subtitle=subtitle_str,
            subtitleFontSize=12,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_axisX(grid=False)
    .configure_title(color=INK, fontSize=16, subtitleFontSize=12, subtitleColor=INK_SOFT)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
    )
)

# Save PNG at the exact canvas target, then HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
