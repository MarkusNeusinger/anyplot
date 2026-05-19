""" anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: altair 6.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-19
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73) + accessible extensions for 10 entities
COLORS = [
    "#009E73",  # Okabe-Ito pos 1 — brand green, always first
    "#D55E00",  # Okabe-Ito pos 2 — vermillion
    "#0072B2",  # Okabe-Ito pos 3 — blue
    "#CC79A7",  # Okabe-Ito pos 4 — reddish purple
    "#E69F00",  # Okabe-Ito pos 5 — orange
    "#56B4E9",  # Okabe-Ito pos 6 — sky blue
    "#F0E442",  # Okabe-Ito pos 7 — yellow
    "#332288",  # accessible extension — deep indigo
    "#117733",  # accessible extension — deep green
    "#882255",  # accessible extension — deep crimson
]

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

data = []
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
df_key["Rank"] = df_key.groupby("Year")["Subscribers"].rank(ascending=True, method="first").astype(int)

# Bar chart layer
bar_chart = (
    alt.Chart(df_key)
    .mark_bar(cornerRadiusEnd=6, height=45)
    .encode(
        x=alt.X(
            "Subscribers:Q",
            title="Subscribers (millions)",
            axis=alt.Axis(labelFontSize=16, titleFontSize=20, grid=True, gridOpacity=0.25),
        ),
        y=alt.Y("Rank:O", title=None, axis=None, sort="descending"),
        color=alt.Color(
            "Platform:N",
            scale=alt.Scale(domain=platforms, range=COLORS),
            legend=alt.Legend(
                title="Platform", labelFontSize=16, titleFontSize=18, symbolSize=160, padding=14, cornerRadius=4
            ),
        ),
        tooltip=[
            alt.Tooltip("Platform:N", title="Platform"),
            alt.Tooltip("Subscribers:Q", format=".1f", title="Subscribers (M)"),
            alt.Tooltip("Year:O", title="Year"),
        ],
    )
)

# Platform name labels outside bars
text_labels = (
    alt.Chart(df_key)
    .mark_text(align="left", dx=8, fontSize=14, fontWeight="bold")
    .encode(
        x=alt.X("Subscribers:Q"),
        y=alt.Y("Rank:O", sort="descending"),
        text=alt.Text("Platform:N"),
        color=alt.value(INK),
    )
)

# Value labels inside bars
value_labels = (
    alt.Chart(df_key)
    .mark_text(align="right", dx=-8, fontSize=16, fontWeight="normal")
    .encode(
        x=alt.X("Subscribers:Q"),
        y=alt.Y("Rank:O", sort="descending"),
        text=alt.Text("Subscribers:Q", format=".0f"),
        color=alt.value("white"),
    )
)

# Combine layers and facet by year
combined = (bar_chart + text_labels + value_labels).properties(width=340, height=750)

chart = (
    combined.facet(
        column=alt.Column("Year:O", header=alt.Header(labelFontSize=26, title=None, labelPadding=15, labelColor=INK)),
        spacing=20,
    )
    .properties(
        title=alt.Title(
            "bar-race-animated · python · altair · anyplot.ai",
            fontSize=34,
            anchor="middle",
            subtitle="Streaming Platform Subscribers Over Time (millions)",
            subtitleFontSize=22,
            dy=-10,
        ),
        background=PAGE_BG,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK_SOFT,
        gridOpacity=0.20,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK, subtitleColor=INK_SOFT)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .resolve_scale(x="independent")
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
