"""anyplot.ai
drawdown-basic: Drawdown Chart
Library: altair | Python 3.13
Quality: pending | Updated: 2026-05-23
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

DD_COLOR = "#B71D27"  # anyplot palette pos 3 — semantic: loss/drawdown
REC_COLOR = "#009E73"  # anyplot palette pos 1 — semantic: recovery/new high

# Data — simulated asset price over ~2 years with drawdowns and recoveries
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=500, freq="D")
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

price = 100 * np.cumprod(1 + returns)
running_max = np.maximum.accumulate(price)
drawdown = (price - running_max) / running_max * 100

df = pd.DataFrame({"date": dates, "drawdown": drawdown})

# Max drawdown stats
max_dd_idx = df["drawdown"].idxmin()
max_dd_date = df.loc[max_dd_idx, "date"]
max_dd_value = df.loc[max_dd_idx, "drawdown"]
max_drawdown_pct = abs(max_dd_value)

# Drawdown duration (peak → trough)
dd_start_candidates = df.loc[:max_dd_idx][df.loc[:max_dd_idx, "drawdown"] == 0]
dd_start_date = dd_start_candidates.iloc[-1]["date"] if not dd_start_candidates.empty else dates[0]
dd_duration_days = (max_dd_date - dd_start_date).days

# Recovery (trough → next new high)
post_max = df[df.index > max_dd_idx]
recovery_row = post_max[post_max["drawdown"] >= 0]
recovery_days = int((recovery_row.iloc[0]["date"] - max_dd_date).days) if not recovery_row.empty else None
recovery_str = f"{recovery_days}d" if recovery_days else "ongoing"

# Recovery points: first new high after any drawdown deeper than -5%
df["prev_dd"] = df["drawdown"].shift(1)
df["is_new_high"] = (df["drawdown"] >= 0) & (df["prev_dd"] < 0)
rec_indices = []
last_low = 0.0
for idx, row in df.iterrows():
    if row["drawdown"] < last_low:
        last_low = row["drawdown"]
    if row["is_new_high"] and last_low < -5:
        rec_indices.append(idx)
        last_low = 0.0

recovery_points = df.loc[rec_indices, ["date", "drawdown"]].copy().reset_index(drop=True)
recovery_points["series"] = "New High"

max_dd_df = pd.DataFrame(
    {"date": [max_dd_date], "drawdown": [max_dd_value], "label": [f"Max DD: {max_drawdown_pct:.1f}%"]}
)

title_str = "drawdown-basic · python · altair · anyplot.ai"
subtitle_str = f"Max Drawdown: {max_drawdown_pct:.1f}%  ·  Duration: {dd_duration_days}d  ·  Recovery: {recovery_str}"

# Plot layers
area = (
    alt.Chart(df)
    .mark_area(opacity=0.45, color=DD_COLOR)
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("drawdown:Q", title="Drawdown (%)", scale=alt.Scale(domain=[df["drawdown"].min() * 1.15, 5])),
    )
)

dd_line = alt.Chart(df).mark_line(color=DD_COLOR, strokeWidth=2).encode(x="date:T", y="drawdown:Q")

zero_rule = (
    alt.Chart(pd.DataFrame({"y": [0]}))
    .mark_rule(strokeDash=[5, 4], strokeWidth=1.5)
    .encode(y="y:Q", color=alt.value(INK_SOFT))
)

max_dd_point = (
    alt.Chart(max_dd_df)
    .mark_point(size=250, color="#9418DB", filled=True, stroke=INK, strokeWidth=1.5)
    .encode(x="date:T", y="drawdown:Q")
)

max_dd_label = (
    alt.Chart(max_dd_df)
    .mark_text(align="left", dx=12, dy=-8, fontSize=11, fontWeight="bold")
    .encode(x="date:T", y="drawdown:Q", text="label:N", color=alt.value(INK))
)

layers = [area, dd_line, zero_rule, max_dd_point, max_dd_label]

if len(recovery_points) > 0:
    recovery_markers = (
        alt.Chart(recovery_points)
        .mark_point(shape="triangle-up", filled=True, size=150, stroke=PAGE_BG, strokeWidth=1)
        .encode(
            x="date:T",
            y="drawdown:Q",
            color=alt.Color(
                "series:N", scale=alt.Scale(range=[REC_COLOR]), legend=alt.Legend(title="", orient="top-right")
            ),
            tooltip=[alt.Tooltip("date:T", title="New High", format="%Y-%m-%d")],
        )
    )
    layers.append(recovery_markers)

chart = (
    alt.layer(*layers)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            title_str,
            fontSize=16,
            color=INK,
            anchor="start",
            subtitle=subtitle_str,
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1, continuousWidth=620, continuousHeight=320)
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
    .configure_title(color=INK, fontSize=16, subtitleFontSize=11, subtitleColor=INK_SOFT)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
    )
)

# Save PNG and pad to exact canvas target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
