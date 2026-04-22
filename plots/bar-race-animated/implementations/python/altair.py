""" pyplots.ai
bar-race-animated: Animated Bar Chart Race
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Simulated streaming platform subscribers (millions) over time
np.random.seed(42)

platforms = [
    "StreamFlix",
    "ViewMax",
    "PlayNow",
    "WatchHub",
    "MediaGo",
    "CineCloud",
    "ShowTime",
    "PrimeView",
    "FlixBox",
    "CloudTV",
]
years = list(range(2015, 2025))

# Generate evolving subscriber counts with different growth trajectories
data = []
base_values = {
    "StreamFlix": 40,
    "ViewMax": 35,
    "PlayNow": 30,
    "WatchHub": 25,
    "MediaGo": 20,
    "CineCloud": 15,
    "ShowTime": 10,
    "PrimeView": 5,
    "FlixBox": 8,
    "CloudTV": 12,
}
growth_rates = {
    "StreamFlix": 1.15,
    "ViewMax": 1.12,
    "PlayNow": 1.25,
    "WatchHub": 1.08,
    "MediaGo": 1.20,
    "CineCloud": 1.10,
    "ShowTime": 1.05,
    "PrimeView": 1.30,
    "FlixBox": 1.18,
    "CloudTV": 1.06,
}

for platform in platforms:
    value = base_values[platform]
    for year in years:
        noise = np.random.uniform(0.9, 1.1)
        data.append({"Platform": platform, "Year": year, "Subscribers": round(value * noise, 1)})
        value *= growth_rates[platform]

df = pd.DataFrame(data)

# Select key years for small multiples
key_years = [2015, 2018, 2021, 2024]
df_key = df[df["Year"].isin(key_years)].copy()

# Add rank for each year (used for sorting within each facet)
df_key["Rank"] = df_key.groupby("Year")["Subscribers"].rank(ascending=True, method="first").astype(int)

# Color palette with Python Blue and Yellow first
colors = ["#306998", "#FFD43B", "#4A90D9", "#2ECC71", "#E74C3C", "#9B59B6", "#F39C12", "#1ABC9C", "#34495E", "#E67E22"]

# Create single bar chart that will be faceted
bar_chart = (
    alt.Chart(df_key)
    .mark_bar(cornerRadiusEnd=6, height=45)
    .encode(
        x=alt.X(
            "Subscribers:Q",
            title="Subscribers (millions)",
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, grid=True, gridOpacity=0.3),
        ),
        y=alt.Y("Rank:O", title=None, axis=None, sort="descending"),
        color=alt.Color("Platform:N", scale=alt.Scale(domain=platforms, range=colors), legend=None),
        tooltip=[
            alt.Tooltip("Platform:N", title="Platform"),
            alt.Tooltip("Subscribers:Q", format=".1f", title="Subscribers (M)"),
            alt.Tooltip("Year:O", title="Year"),
        ],
    )
)

# Add text labels on bars
text_labels = (
    alt.Chart(df_key)
    .mark_text(align="left", dx=8, fontSize=14, fontWeight="bold")
    .encode(
        x=alt.X("Subscribers:Q"),
        y=alt.Y("Rank:O", sort="descending"),
        text=alt.Text("Platform:N"),
        color=alt.value("#333333"),
    )
)

# Value labels at end of bars
value_labels = (
    alt.Chart(df_key)
    .mark_text(align="right", dx=-8, fontSize=13, fontWeight="normal")
    .encode(
        x=alt.X("Subscribers:Q"),
        y=alt.Y("Rank:O", sort="descending"),
        text=alt.Text("Subscribers:Q", format=".0f"),
        color=alt.value("white"),
    )
)

# Combine layers - target 4800x2700 at scale 3x = 1600x900 base
combined = (bar_chart + text_labels + value_labels).properties(width=340, height=750)

# Facet by year
chart = (
    combined.facet(
        column=alt.Column("Year:O", header=alt.Header(labelFontSize=26, title=None, labelPadding=15)), spacing=20
    )
    .configure_view(strokeWidth=0)
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .properties(
        title=alt.Title(
            "bar-race-animated · altair · pyplots.ai",
            fontSize=34,
            anchor="middle",
            subtitle="Streaming Platform Subscribers Over Time (millions)",
            subtitleFontSize=22,
            dy=-10,
        )
    )
    .resolve_scale(x="independent")
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
