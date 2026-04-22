""" pyplots.ai
line-win-probability: Win Probability Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated NFL game: Eagles vs Cowboys
np.random.seed(42)

quarters = [0, 15, 30, 45, 60]
quarter_labels = ["Kickoff", "Q2", "Q3", "Q4", "Final"]

plays = np.linspace(0, 60, 200)
prob = np.full_like(plays, 0.5)
events = []

scoring_plays = [
    (5, -0.10, "FG Cowboys 0-3"),
    (12, 0.20, "TD Eagles 7-3"),
    (18, -0.18, "TD Cowboys 7-10"),
    (24, 0.15, "FG Eagles 10-10"),
    (31, 0.18, "TD Eagles 17-10"),
    (37, -0.22, "TD Cowboys 17-17"),
    (40, -0.12, "FG Cowboys 17-20"),
    (48, 0.28, "TD Eagles 24-20"),
    (53, 0.10, "FG Eagles 27-20"),
    (58, 0.08, "INT Eagles seal it"),
]

for i in range(1, len(plays)):
    drift = 0.0
    for event_time, shift, label in scoring_plays:
        if plays[i - 1] < event_time <= plays[i]:
            drift += shift
            events.append((event_time, label))
    noise = np.random.normal(0, 0.008)
    prob[i] = np.clip(prob[i - 1] + drift + noise, 0.01, 0.99)

prob[-1] = 1.0
prob[-2] = 0.98
prob[-3] = 0.95

df = pd.DataFrame({"minute": plays, "win_prob": prob})
df["win_pct"] = df["win_prob"] * 100
df["above_50"] = df["win_pct"].clip(lower=50)
df["below_50"] = df["win_pct"].clip(upper=50)

df_events = pd.DataFrame(events, columns=["minute", "label"])
df_events["win_pct"] = [np.interp(m, df["minute"], df["win_pct"]) for m in df_events["minute"]]

# Manual label y-offsets tuned per event to avoid overlap
# Positive = above point, negative = below point
label_nudges = [8, -12, -12, -10, 7, 10, -10, -14, 7, 7]
df_events["label_y"] = np.clip(df_events["win_pct"] + label_nudges, 5, 97)

# Split events into early/late for different label alignment
df_events_left = df_events[df_events["minute"] <= 50].copy()
df_events_right = df_events[df_events["minute"] > 50].copy()

df_quarters = pd.DataFrame({"minute": quarters, "label": quarter_labels})

# Plot
base = alt.Chart(df)

baseline = base.mark_rule(strokeDash=[6, 4], strokeWidth=2, color="#888888").encode(y=alt.datum(50))

area_home = base.mark_area(interpolate="monotone", opacity=0.4, color="#004C54").encode(
    x=alt.X("minute:Q", title="Game Time (minutes)", scale=alt.Scale(domain=[0, 60])),
    y=alt.Y("above_50:Q", title="Win Probability (%)", scale=alt.Scale(domain=[0, 100])),
    y2=alt.datum(50),
)

area_away = base.mark_area(interpolate="monotone", opacity=0.4, color="#7B2D26").encode(
    x="minute:Q", y=alt.Y("below_50:Q", scale=alt.Scale(domain=[0, 100])), y2=alt.datum(50)
)

# Use dark charcoal line instead of Python Blue to harmonize with team-colored fills
line = base.mark_line(interpolate="monotone", strokeWidth=3.5, color="#2D2D2D").encode(
    x="minute:Q",
    y=alt.Y("win_pct:Q"),
    tooltip=[
        alt.Tooltip("minute:Q", title="Minute", format=".1f"),
        alt.Tooltip("win_pct:Q", title="Win Prob %", format=".1f"),
    ],
)

# Interactive nearest-point selection for crosshair effect
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["minute"], empty=False)

# Invisible voronoi layer to capture mouse position
selectors = base.mark_point(size=1, opacity=0).encode(x="minute:Q").add_params(nearest)

# Crosshair vertical rule that follows cursor
crosshair_rule = base.mark_rule(color="#666666", strokeWidth=1, strokeDash=[3, 3]).encode(
    x="minute:Q", opacity=alt.condition(nearest, alt.value(0.7), alt.value(0))
)

# Highlight dot on line at nearest point
highlight_dot = base.mark_circle(size=180, color="#2D2D2D", stroke="white", strokeWidth=2).encode(
    x="minute:Q", y="win_pct:Q", opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)

# Event markers: use gold/amber for clear contrast against both team fills
event_points = (
    alt.Chart(df_events)
    .mark_circle(size=220, color="#F5A623", stroke="#2D2D2D", strokeWidth=2)
    .encode(
        x="minute:Q",
        y="win_pct:Q",
        tooltip=[alt.Tooltip("label:N", title="Event"), alt.Tooltip("minute:Q", title="Minute", format=".0f")],
    )
)

# Staggered event labels to prevent overlap - split into left/right aligned groups
event_labels_left = (
    alt.Chart(df_events_left)
    .mark_text(fontSize=15, fontWeight="bold", align="left", dx=12, color="#2D2D2D")
    .encode(x="minute:Q", y="label_y:Q", text="label:N")
)

event_labels_right = (
    alt.Chart(df_events_right)
    .mark_text(fontSize=15, fontWeight="bold", align="right", dx=-12, color="#2D2D2D")
    .encode(x="minute:Q", y="label_y:Q", text="label:N")
)

quarter_rules = (
    alt.Chart(df_quarters[1:-1]).mark_rule(strokeDash=[4, 3], strokeWidth=1.5, color="#aaaaaa").encode(x="minute:Q")
)

quarter_text = (
    alt.Chart(df_quarters)
    .mark_text(fontSize=16, fontWeight="bold", dy=-14, color="#666666")
    .encode(x="minute:Q", y=alt.datum(100), text="label:N")
)

chart = (
    (
        area_home
        + area_away
        + baseline
        + line
        + event_points
        + event_labels_left
        + event_labels_right
        + quarter_rules
        + quarter_text
        + selectors
        + crosshair_rule
        + highlight_dot
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Eagles vs Cowboys · line-win-probability · altair · pyplots.ai",
            fontSize=28,
            subtitle="Final Score: Eagles 27 - Cowboys 20",
            subtitleFontSize=20,
            subtitleColor="#555555",
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=False, domainColor="#cccccc")
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
