""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-04
"""

import altair as alt
import pandas as pd


# Data - Employee engagement survey (10 questions, 5-point Likert scale)
data = pd.DataFrame(
    {
        "question": [
            "I feel valued at work",
            "My manager supports my growth",
            "I have the tools I need",
            "Work-life balance is respected",
            "Communication is transparent",
            "I see career advancement opportunities",
            "The company culture is inclusive",
            "My compensation is fair",
            "I would recommend this workplace",
            "I feel motivated daily",
        ],
        "Strongly Disagree": [3, 5, 2, 8, 12, 15, 4, 18, 6, 10],
        "Disagree": [7, 10, 5, 15, 18, 22, 8, 25, 10, 16],
        "Neutral": [12, 15, 10, 14, 20, 18, 12, 15, 14, 18],
        "Agree": [45, 38, 48, 35, 30, 28, 42, 28, 40, 32],
        "Strongly Agree": [33, 32, 35, 28, 20, 17, 34, 14, 30, 24],
    }
)

# Sort by net agreement (agree + strongly agree - disagree - strongly disagree)
data["net_agreement"] = data["Agree"] + data["Strongly Agree"] - data["Disagree"] - data["Strongly Disagree"]
data = data.sort_values("net_agreement").reset_index(drop=True)
question_order = data["question"].tolist()

# Build diverging segments centered on neutral midpoint
categories = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
colors = ["#D95F02", "#FDB863", "#B0B0B0", "#92C5DE", "#306998"]

rows = []
for _, row in data.iterrows():
    half_neutral = row["Neutral"] / 2
    positions = {
        "Strongly Disagree": (
            -(row["Strongly Disagree"] + row["Disagree"] + half_neutral),
            -(row["Disagree"] + half_neutral),
        ),
        "Disagree": (-(row["Disagree"] + half_neutral), -half_neutral),
        "Neutral": (-half_neutral, half_neutral),
        "Agree": (half_neutral, half_neutral + row["Agree"]),
        "Strongly Agree": (half_neutral + row["Agree"], half_neutral + row["Agree"] + row["Strongly Agree"]),
    }
    for cat in categories:
        x_start, x_end = positions[cat]
        val = row[cat]
        rows.append(
            {
                "question": row["question"],
                "x_start": x_start,
                "x_end": x_end,
                "category": cat,
                "value": val,
                "x_mid": (x_start + x_end) / 2,
                "label": f"{int(val)}%",
            }
        )

segments_df = pd.DataFrame(rows)

# Bars
bars = (
    alt.Chart(segments_df)
    .mark_bar(stroke="white", strokeWidth=0.8)
    .encode(
        x=alt.X("x_start:Q", title="Percentage (%)", axis=alt.Axis(titleFontSize=22, labelFontSize=18)),
        x2="x_end:Q",
        y=alt.Y("question:N", title=None, sort=question_order, axis=alt.Axis(labelFontSize=16, labelLimit=350)),
        color=alt.Color(
            "category:N",
            scale=alt.Scale(domain=categories, range=colors),
            legend=alt.Legend(title=None, labelFontSize=18, symbolSize=400, orient="bottom", direction="horizontal"),
        ),
        tooltip=[
            alt.Tooltip("question:N", title="Question"),
            alt.Tooltip("category:N", title="Response"),
            alt.Tooltip("value:Q", title="%", format=".0f"),
        ],
    )
)

# Labels (white text on dark backgrounds: Strongly Disagree, Strongly Agree)
dark_bg = segments_df[
    (segments_df["value"] >= 10) & segments_df["category"].isin(["Strongly Disagree", "Strongly Agree"])
]
labels_white = (
    alt.Chart(dark_bg)
    .mark_text(fontSize=14, fontWeight="bold", color="white")
    .encode(x="x_mid:Q", y=alt.Y("question:N", sort=question_order), text="label:N")
)

# Labels (dark text on light backgrounds: Disagree, Neutral, Agree)
light_bg = segments_df[(segments_df["value"] >= 10) & segments_df["category"].isin(["Disagree", "Neutral", "Agree"])]
labels_dark = (
    alt.Chart(light_bg)
    .mark_text(fontSize=14, fontWeight="bold", color="#333333")
    .encode(x="x_mid:Q", y=alt.Y("question:N", sort=question_order), text="label:N")
)

# Zero baseline
zero_line = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#333333", strokeWidth=1.5).encode(x="x:Q")

# Combine and style
chart = (
    (bars + labels_white + labels_dark + zero_line)
    .properties(
        width=1400,
        height=800,
        title=alt.Title("bar-diverging-likert · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
    .configure_axisX(gridOpacity=0.15)
    .configure_axisY(grid=False)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
