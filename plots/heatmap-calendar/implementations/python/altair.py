""" pyplots.ai
heatmap-calendar: Basic Calendar Heatmap
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - create one year of daily activity data (GitHub-style contribution graph)
np.random.seed(42)

# Generate dates for one year
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Generate realistic activity values (commits/contributions)
# More activity on weekdays, less on weekends, with some variation
values = []
for date in dates:
    weekday = date.weekday()
    # Base activity: higher on weekdays
    if weekday < 5:  # Weekday
        base = np.random.choice([0, 2, 5, 8, 12], p=[0.2, 0.25, 0.3, 0.15, 0.1])
    else:  # Weekend
        base = np.random.choice([0, 1, 3, 5], p=[0.5, 0.25, 0.15, 0.1])
    # Add some noise
    value = max(0, base + np.random.randint(-1, 2))
    values.append(value)

# Create DataFrame
df = pd.DataFrame({"date": dates, "value": values})

# Extract calendar components
df["week"] = df["date"].dt.isocalendar().week
df["year"] = df["date"].dt.year
df["weekday"] = df["date"].dt.weekday  # 0=Monday, 6=Sunday
df["month"] = df["date"].dt.month
df["month_name"] = df["date"].dt.strftime("%b")

# Create week number that's continuous across the year
df["week_of_year"] = (df["date"] - start_date).dt.days // 7

# Map weekday numbers to names (for y-axis)
weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
df["weekday_name"] = df["weekday"].map(lambda x: weekday_names[x])

# Create month labels for x-axis (first week of each month)
month_labels = df.groupby("month").agg({"week_of_year": "min", "month_name": "first"}).reset_index()
# Assign to top row (Monday) for positioning
month_labels["weekday_name"] = "Mon"

# Plot - calendar heatmap
heatmap = (
    alt.Chart(df)
    .mark_rect(cornerRadius=3)
    .encode(
        x=alt.X("week_of_year:O", title="", axis=alt.Axis(labels=False, ticks=False, domain=False)),
        y=alt.Y(
            "weekday_name:O",
            title="",
            sort=weekday_names,
            axis=alt.Axis(labelFontSize=18, titleFontSize=20, domain=False, ticks=False),
        ),
        color=alt.Color(
            "value:Q",
            scale=alt.Scale(scheme="greens", domain=[0, 15]),
            legend=alt.Legend(
                title="Contributions", titleFontSize=18, labelFontSize=16, orient="bottom", direction="horizontal"
            ),
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("value:Q", title="Contributions"),
            alt.Tooltip("weekday_name:N", title="Day"),
        ],
    )
)

# Create month labels as a text layer at the top
month_text = (
    alt.Chart(month_labels)
    .mark_text(fontSize=20, align="left", baseline="bottom", dy=-10, fontWeight="bold")
    .encode(x=alt.X("week_of_year:O"), y=alt.Y("weekday_name:O", sort=weekday_names), text="month_name:N")
)

# Combine heatmap and month labels
# Target: ~4800x2700 px (16:9) with scale_factor=3.0
chart = (
    alt.layer(heatmap, month_text)
    .properties(
        width=1500,
        height=800,
        title=alt.Title(
            "Daily Contributions 2024 · heatmap-calendar · altair · pyplots.ai", fontSize=28, anchor="start", offset=20
        ),
    )
    .configure_axis(grid=False)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
