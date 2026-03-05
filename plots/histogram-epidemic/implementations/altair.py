"""pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: altair 6.0.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-05
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

# Cumulative case count
daily_total = pd.DataFrame({"onset_date": dates, "daily_total": total_cases})
daily_total["cumulative"] = daily_total["daily_total"].cumsum()
max_daily = int(total_cases.max()) + 15

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
    .mark_bar(stroke="#ffffff", strokeWidth=0.5)
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

# Cumulative line overlay with independent right y-axis
cumulative_line = (
    alt.Chart(daily_total)
    .mark_line(strokeWidth=2.5, interpolate="monotone", color="#D55E00")
    .encode(
        x="onset_date:T",
        y=alt.Y(
            "cumulative:Q",
            title="Cumulative Cases",
            axis=alt.Axis(
                titleColor="#D55E00", labelColor="#D55E00", format=",.0f", titleFontSize=22, labelFontSize=18
            ),
        ),
        tooltip=[
            alt.Tooltip("onset_date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("cumulative:Q", title="Cumulative Cases", format=","),
        ],
    )
)

# Intervention vertical rules
rules = alt.Chart(events).mark_rule(strokeDash=[6, 4], strokeWidth=1.5, color="#888888").encode(x="date:T")

rule_labels = (
    alt.Chart(events)
    .mark_text(align="left", dx=6, fontSize=18, fontWeight="bold", fontStyle="italic", color="#555555", angle=270)
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
    .mark_text(fontSize=18, fontWeight="bold", color="#D55E00", dy=-16)
    .encode(x="onset_date:T", y="peak_val:Q", text="label:N")
)

# Combine bar layers (share left y-axis)
bar_layer = alt.layer(bars, rules, rule_labels, peak_label)

# Combine with cumulative line using independent y-axis resolution
chart = (
    alt.layer(bar_layer, cumulative_line)
    .resolve_scale(y="independent")
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "histogram-epidemic · altair · pyplots.ai",
            fontSize=28,
            anchor="start",
            subtitle="Daily new cases by classification with cumulative total",
            subtitleFontSize=18,
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
