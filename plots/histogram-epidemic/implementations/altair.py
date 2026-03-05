""" pyplots.ai
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

# Simulate a point-source outbreak with propagated secondary wave
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
        "case_type": (["Confirmed"] * 120 + ["Probable"] * 120 + ["Suspect"] * 120),
    }
)

# Intervention events
events = pd.DataFrame(
    {
        "date": pd.to_datetime(["2024-02-10", "2024-03-01", "2024-03-20"]),
        "event": ["Source identified", "Containment measures", "Vaccination campaign"],
    }
)

# Plot - stacked bar chart
type_order = ["Confirmed", "Probable", "Suspect"]
color_scale = alt.Scale(domain=type_order, range=["#306998", "#5B9BD5", "#A8D0E6"])

bars = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("onset_date:T", title="Date of Symptom Onset", axis=alt.Axis(format="%b %d")),
        y=alt.Y("case_count:Q", title="New Cases", stack="zero"),
        color=alt.Color("case_type:N", scale=color_scale, sort=type_order, title="Classification"),
        order=alt.Order("case_type_order:Q"),
        tooltip=["onset_date:T", "case_type:N", "case_count:Q"],
    )
    .transform_calculate(case_type_order="indexof(['Confirmed','Probable','Suspect'], datum.case_type)")
)

# Intervention vertical rules
rules = alt.Chart(events).mark_rule(strokeDash=[4, 4], strokeWidth=1.5, color="#555555").encode(x="date:T")

events["y_pos"] = [88, 88, 88]

rule_labels = (
    alt.Chart(events)
    .mark_text(align="left", dx=5, dy=0, fontSize=14, fontWeight="bold", color="#444444", angle=270)
    .encode(x="date:T", y="y_pos:Q", text="event:N")
)

# Combine with dual axis
chart = (
    alt.layer(bars, rules, rule_labels)
    .resolve_scale(y="shared")
    .properties(
        width=1600, height=900, title=alt.Title("histogram-epidemic · altair · pyplots.ai", fontSize=28, anchor="start")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.2)
    .configure_legend(titleFontSize=18, labelFontSize=16, symbolSize=200, orient="top-right")
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
