"""pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: altair 6.0.0 | Python 3.14.3
Quality: 71/100 | Created: 2026-03-05
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

dates = pd.date_range("2024-01-15", periods=120, freq="D")

days = np.arange(120)
wave1 = 80 * np.exp(-0.5 * ((days - 25) / 6) ** 2)
wave2 = 45 * np.exp(-0.5 * ((days - 55) / 8) ** 2)
wave3 = 25 * np.exp(-0.5 * ((days - 85) / 10) ** 2)
base_rate = wave1 + wave2 + wave3 + 2

confirmed_frac = np.clip(0.6 + 0.2 * np.sin(days / 15), 0.4, 0.85)
probable_frac = np.clip(0.25 - 0.05 * np.sin(days / 15), 0.1, 0.35)

total_cases = np.round(base_rate + np.random.poisson(2, 120)).astype(int)
confirmed = np.round(total_cases * confirmed_frac).astype(int)
probable = np.round(total_cases * probable_frac).astype(int)
suspect = np.clip(total_cases - confirmed - probable, 0, None).astype(int)

df = pd.DataFrame(
    {
        "onset_date": np.tile(dates, 3),
        "case_count": np.concatenate([confirmed, probable, suspect]),
        "case_type": ["Confirmed"] * 120 + ["Probable"] * 120 + ["Suspect"] * 120,
    }
)

# Cumulative case count (normalized to bar y-axis scale)
daily_total = pd.DataFrame({"onset_date": dates, "daily_total": total_cases})
daily_total["cumulative"] = daily_total["daily_total"].cumsum()
max_cumulative = int(daily_total["cumulative"].max())
max_daily = int(total_cases.max()) + 15
daily_total["cumulative_scaled"] = daily_total["cumulative"] / max_cumulative * max_daily

# Intervention events
events = pd.DataFrame(
    {
        "date": pd.to_datetime(["2024-02-10", "2024-03-01", "2024-03-20"]),
        "event": ["Source identified", "Containment measures", "Vaccination campaign"],
        "y_pos": [max_daily - 2, max_daily - 2, max_daily - 2],
    }
)

# Distinct colorblind-safe palette (dark blue, amber, sky blue)
type_order = ["Confirmed", "Probable", "Suspect"]
color_scale = alt.Scale(domain=type_order, range=["#306998", "#E69F00", "#56B4E9"])

bars = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X(
            "onset_date:T",
            title="Date of Symptom Onset",
            axis=alt.Axis(format="%b %d", labelAngle=-45, tickCount="week"),
        ),
        y=alt.Y("case_count:Q", title="New Cases", scale=alt.Scale(domain=[0, max_daily])),
        color=alt.Color("case_type:N", scale=color_scale, sort=type_order, title="Classification"),
        order=alt.Order("order:Q"),
        tooltip=[
            alt.Tooltip("onset_date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("case_type:N", title="Type"),
            alt.Tooltip("case_count:Q", title="Cases"),
        ],
    )
    .transform_calculate(order="{'Confirmed': 0, 'Probable': 1, 'Suspect': 2}[datum.case_type]")
)

# Cumulative line overlay (scaled to left y-axis range)
cumulative_line = (
    alt.Chart(daily_total)
    .mark_line(strokeWidth=2.5, interpolate="monotone", color="#D55E00")
    .encode(
        x="onset_date:T",
        y=alt.Y("cumulative_scaled:Q", scale=alt.Scale(domain=[0, max_daily])),
        tooltip=[
            alt.Tooltip("onset_date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("cumulative:Q", title="Cumulative Cases", format=","),
        ],
    )
)

# Right-axis tick labels for cumulative scale
cum_ticks = [0, 500, 1000, 1500, 2000, 2500, 3000, max_cumulative]
cum_tick_df = pd.DataFrame(
    {"label": [f"{int(v):,}" for v in cum_ticks], "y_val": [v / max_cumulative * max_daily for v in cum_ticks]}
)

right_axis_labels = (
    alt.Chart(cum_tick_df)
    .mark_text(align="left", dx=8, fontSize=16, color="#D55E00")
    .encode(x=alt.value(1600), y=alt.Y("y_val:Q", scale=alt.Scale(domain=[0, max_daily])), text="label:N")
)

right_axis_title = (
    alt.Chart(pd.DataFrame({"x": [0]}))
    .mark_text(align="center", fontSize=20, color="#D55E00", angle=270, fontWeight="bold")
    .encode(x=alt.value(1660), y=alt.value(450), text=alt.value("Cumulative Cases"))
)

# Intervention vertical rules
rules = alt.Chart(events).mark_rule(strokeDash=[6, 4], strokeWidth=1.5, color="#888888").encode(x="date:T")

rule_labels = (
    alt.Chart(events)
    .mark_text(align="left", dx=6, fontSize=13, fontWeight="bold", fontStyle="italic", color="#555555", angle=270)
    .encode(x="date:T", y="y_pos:Q", text="event:N")
)

# Peak annotation
peak_day = int(np.argmax(total_cases))
peak_data = pd.DataFrame(
    {
        "onset_date": [dates[peak_day]],
        "peak_val": [int(total_cases[peak_day])],
        "label": [f"Peak: {int(total_cases[peak_day])} cases"],
    }
)

peak_label = (
    alt.Chart(peak_data)
    .mark_text(fontSize=14, fontWeight="bold", color="#D55E00", dy=-14)
    .encode(x="onset_date:T", y="peak_val:Q", text="label:N")
)

# Combine all layers
chart = (
    alt.layer(bars, cumulative_line, right_axis_labels, right_axis_title, rules, rule_labels, peak_label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "histogram-epidemic · altair · pyplots.ai",
            fontSize=28,
            anchor="start",
            subtitle="Daily new cases by classification with cumulative total",
            subtitleFontSize=16,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15, domainColor="#cccccc", tickColor="#cccccc")
    .configure_legend(
        titleFontSize=18,
        labelFontSize=16,
        symbolSize=200,
        orient="top-right",
        fillColor="#ffffffee",
        strokeColor="#eeeeee",
        padding=10,
        cornerRadius=4,
    )
    .configure_view(strokeWidth=0)
    .configure_title(anchor="start")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
