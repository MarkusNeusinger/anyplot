""" pyplots.ai
drawdown-basic: Drawdown Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated asset price over 2 years with drawdowns and recoveries
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=500, freq="D")

# Base returns with positive drift
returns = np.random.normal(0.001, 0.01, 500)

# Create distinct market phases with drawdowns and full recoveries
# Phase 1: Initial rally then correction
returns[0:30] = np.random.normal(0.002, 0.008, 30)  # Rally
returns[30:50] = np.random.normal(-0.012, 0.012, 20)  # Correction ~20%
returns[50:90] = np.random.normal(0.008, 0.008, 40)  # Strong recovery to new highs

# Phase 2: Second correction and recovery
returns[100:130] = np.random.normal(-0.015, 0.015, 30)  # Deeper correction ~30%
returns[130:200] = np.random.normal(0.006, 0.009, 70)  # Recovery to new highs

# Phase 3: Major drawdown (the max)
returns[220:270] = np.random.normal(-0.01, 0.012, 50)  # Extended decline ~35%
returns[270:350] = np.random.normal(0.005, 0.008, 80)  # Gradual recovery to new highs

# Phase 4: Late correction
returns[380:410] = np.random.normal(-0.008, 0.01, 30)  # Moderate correction ~15%
returns[410:480] = np.random.normal(0.004, 0.007, 70)  # Final recovery

price = 100 * np.cumprod(1 + returns)

# Calculate drawdown
running_max = np.maximum.accumulate(price)
drawdown = (price - running_max) / running_max * 100

# Create DataFrame
df = pd.DataFrame({"date": dates, "price": price, "drawdown": drawdown, "running_max": running_max})

# Find maximum drawdown point
max_dd_idx = df["drawdown"].idxmin()
max_dd_date = df.loc[max_dd_idx, "date"]
max_dd_value = df.loc[max_dd_idx, "drawdown"]
max_drawdown_pct = abs(max_dd_value)

# Find recovery points (new highs after drawdowns)
df["prev_drawdown"] = df["drawdown"].shift(1)
df["is_recovery"] = (df["drawdown"] == 0) & (df["prev_drawdown"] < -2)
recovery_points = df[df["is_recovery"]].copy()

# Drawdown area chart (filled below zero)
area = (
    alt.Chart(df)
    .mark_area(opacity=0.6, color="#D32F2F")
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y", labelFontSize=16, titleFontSize=20)),
        y=alt.Y(
            "drawdown:Q",
            title="Drawdown (%)",
            scale=alt.Scale(domain=[df["drawdown"].min() * 1.15, 5]),
            axis=alt.Axis(labelFontSize=16, titleFontSize=20),
        ),
    )
)

# Drawdown line for clearer edge
line = alt.Chart(df).mark_line(color="#B71C1C", strokeWidth=2).encode(x="date:T", y="drawdown:Q")

# Zero baseline
zero_line = (
    alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#333333", strokeWidth=2, strokeDash=[4, 4]).encode(y="y:Q")
)

# Maximum drawdown point marker
max_dd_df = pd.DataFrame(
    {"date": [max_dd_date], "drawdown": [max_dd_value], "label": [f"Max DD: {max_drawdown_pct:.1f}%"]}
)

max_dd_point = (
    alt.Chart(max_dd_df)
    .mark_point(size=300, color="#FFD43B", filled=True, strokeWidth=2, stroke="#333333")
    .encode(x="date:T", y="drawdown:Q", tooltip=["label:N"])
)

max_dd_label = (
    alt.Chart(max_dd_df)
    .mark_text(align="left", dx=15, dy=-10, fontSize=18, fontWeight="bold", color="#333333")
    .encode(x="date:T", y="drawdown:Q", text="label:N")
)

# Recovery points markers (new highs after drawdowns)
recovery_markers = (
    alt.Chart(recovery_points)
    .mark_point(size=200, color="#306998", shape="triangle-up", filled=True)
    .encode(x="date:T", y="drawdown:Q", tooltip=[alt.Tooltip("date:T", title="Recovery Date", format="%Y-%m-%d")])
)

# Combine all layers
chart = (
    alt.layer(area, line, zero_line, max_dd_point, max_dd_label, recovery_markers)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("drawdown-basic · altair · pyplots.ai", fontSize=28, anchor="middle", color="#333333"),
    )
    .configure_axis(labelFontSize=16, titleFontSize=20, gridColor="#E0E0E0", gridOpacity=0.5)
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
