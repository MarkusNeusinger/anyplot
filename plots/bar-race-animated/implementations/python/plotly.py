""" pyplots.ai
bar-race-animated: Animated Bar Chart Race
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
import plotly.express as px


# Data: Global streaming platform subscribers (millions) over 5 years
np.random.seed(42)

platforms = [
    "StreamFlix",
    "ViewMax",
    "WatchHub",
    "PlayStream",
    "CinemaCloud",
    "MediaFlow",
    "ScreenTime",
    "FlixNow",
    "StreamZone",
    "OnDemandTV",
]
years = list(range(2019, 2025))

# Generate realistic subscriber growth data with varying trajectories
data = []
base_values = {
    "StreamFlix": 150,
    "ViewMax": 120,
    "WatchHub": 80,
    "PlayStream": 60,
    "CinemaCloud": 50,
    "MediaFlow": 40,
    "ScreenTime": 35,
    "FlixNow": 25,
    "StreamZone": 20,
    "OnDemandTV": 15,
}

growth_rates = {
    "StreamFlix": 1.15,
    "ViewMax": 1.25,
    "WatchHub": 1.35,
    "PlayStream": 1.20,
    "CinemaCloud": 1.10,
    "MediaFlow": 1.30,
    "ScreenTime": 1.40,
    "FlixNow": 1.45,
    "StreamZone": 1.25,
    "OnDemandTV": 1.50,
}

for platform in platforms:
    value = base_values[platform]
    for year in years:
        noise = np.random.uniform(0.9, 1.1)
        data.append({"Platform": platform, "Year": year, "Subscribers": round(value * noise, 1)})
        value = value * growth_rates[platform]

df = pd.DataFrame(data)

# Sort and add rank for each year
df["Rank"] = df.groupby("Year")["Subscribers"].rank(method="first", ascending=False)
df = df.sort_values(["Year", "Subscribers"], ascending=[True, False])

# Color palette - consistent per platform (using Python colors first, then colorblind-safe)
colors = ["#306998", "#FFD43B", "#E24A33", "#348ABD", "#988ED5", "#777777", "#FBC15E", "#8EBA42", "#FFB5B8", "#56B4E9"]
color_map = dict(zip(platforms, colors, strict=False))

# Create animated bar chart
fig = px.bar(
    df,
    x="Subscribers",
    y="Platform",
    color="Platform",
    color_discrete_map=color_map,
    animation_frame="Year",
    orientation="h",
    text="Subscribers",
    category_orders={
        "Platform": df[df["Year"] == 2024].sort_values("Subscribers", ascending=True)["Platform"].tolist()
    },
)

# Update layout for 4800x2700 px canvas
fig.update_layout(
    title={
        "text": "bar-race-animated · plotly · pyplots.ai", "font": {"size": 32, "color": "#333333"}, "x": 0.5, "xanchor": "center"
    },
    xaxis={
        "title": {"text": "Subscribers (Millions)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "range": [0, df["Subscribers"].max() * 1.15],
        "gridcolor": "rgba(128,128,128,0.2)",
        "gridwidth": 1,
    },
    yaxis={"title": {"text": "", "font": {"size": 24}}, "tickfont": {"size": 20}, "categoryorder": "total ascending"},
    template="plotly_white",
    showlegend=False,
    margin={"l": 200, "r": 100, "t": 120, "b": 100},
    plot_bgcolor="white",
    paper_bgcolor="white",
)

# Update traces for better visibility
fig.update_traces(
    texttemplate="%{text:.0f}M",
    textposition="outside",
    textfont={"size": 18, "color": "#333333"},
    marker={"line": {"width": 1, "color": "white"}},
)

# Update animation settings
fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 800
fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 400

# Update slider styling
fig.layout.sliders[0].font = {"size": 18}
fig.layout.sliders[0].currentvalue = {"font": {"size": 24}, "prefix": "Year: ", "visible": True, "xanchor": "center"}

# Save as PNG (static frame showing final year)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML (interactive with animation)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
