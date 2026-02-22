"""pyplots.ai
bump-basic: Basic Bump Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: /100 | Updated: 2026-02-22
"""

import altair as alt
import pandas as pd


# Data - Sports league standings over 6 matchweeks (no random data)
teams = ["Arsenal", "Chelsea", "Liverpool", "Man City", "Man United", "Tottenham"]
weeks = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]
ranks = [
    # Arsenal: Starts 3rd, rises to 1st, stays competitive
    3,
    2,
    1,
    1,
    2,
    1,
    # Chelsea: Mid-table consistency
    4,
    4,
    3,
    4,
    3,
    3,
    # Liverpool: Starts 1st, drops mid-season, recovers
    1,
    1,
    2,
    3,
    1,
    2,
    # Man City: Slow start, climbs steadily
    5,
    5,
    4,
    2,
    4,
    4,
    # Man United: Volatile rankings
    2,
    3,
    5,
    5,
    5,
    5,
    # Tottenham: Bottom position throughout
    6,
    6,
    6,
    6,
    6,
    6,
]

df = pd.DataFrame({"Team": [t for t in teams for _ in weeks], "Week": weeks * len(teams), "Rank": ranks})

# Colorblind-safe palette (Python Blue first)
colors = ["#306998", "#FFD43B", "#E15759", "#59A14F", "#B07AA1", "#76B7B2"]

# Interactive highlight — distinctive Altair feature
highlight = alt.selection_point(fields=["Team"], on="pointerover")

# Shared encodings
x = alt.X("Week:O", title="Match Week", axis=alt.Axis(labelFontSize=18, titleFontSize=22))
y = alt.Y(
    "Rank:Q",
    title="League Position",
    scale=alt.Scale(domain=[1, 6], reverse=True),
    axis=alt.Axis(labelFontSize=18, titleFontSize=22, tickMinStep=1, values=[1, 2, 3, 4, 5, 6]),
)
color = alt.Color(
    "Team:N",
    title="Team",
    scale=alt.Scale(domain=teams, range=colors),
    legend=alt.Legend(labelFontSize=16, titleFontSize=18, symbolSize=200),
)

# Lines — dim non-highlighted teams on hover
lines = (
    alt.Chart(df)
    .mark_line(strokeWidth=4)
    .encode(x=x, y=y, color=color, opacity=alt.condition(highlight, alt.value(1), alt.value(0.3)))
    .add_params(highlight)
)

# Points at each period for clarity
points = (
    alt.Chart(df)
    .mark_point(size=250, filled=True)
    .encode(
        x=alt.X("Week:O"),
        y=alt.Y("Rank:Q", scale=alt.Scale(domain=[1, 6], reverse=True)),
        color=alt.Color("Team:N", scale=alt.Scale(domain=teams, range=colors)),
        opacity=alt.condition(highlight, alt.value(1), alt.value(0.3)),
        tooltip=["Team:N", "Week:O", "Rank:Q"],
    )
)

# Combine layers and configure
chart = (
    (lines + points)
    .properties(width=1600, height=900, title=alt.Title("bump-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(grid=True, gridOpacity=0.2, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG (1600 × 900 × 3 = 4800 × 2700)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version (hover highlights team)
chart.save("plot.html")
