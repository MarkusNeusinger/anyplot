""" anyplot.ai
horizon-basic: Horizon Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 78/100 | Updated: 2026-05-07
"""

import os

import altair as alt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: Generate server metrics over 24 hours for multiple servers
np.random.seed(42)

n_points = 96
hours = pd.date_range("2024-01-15 00:00", periods=n_points, freq="15min")

data_list = []
servers = ["Web Server 1", "Web Server 2", "Database", "Cache", "API Gateway", "Worker"]

for server in servers:
    t = np.linspace(0, 2 * np.pi, n_points)
    if server == "Database":
        base = 40 + 30 * np.sin(t - np.pi / 2) + np.random.randn(n_points) * 8
    elif server == "Cache":
        base = 25 + np.random.randn(n_points) * 5
        base[40:45] += 40
    elif server == "Worker":
        base = 20 + 50 * (np.sin(t * 3) > 0.7) + np.random.randn(n_points) * 6
    else:
        base = 30 + 25 * np.sin(t - np.pi / 3) + np.random.randn(n_points) * 10

    values = base - base.mean()

    for hour, val in zip(hours, values, strict=True):
        data_list.append({"date": hour, "value": val, "series": server})

df = pd.DataFrame(data_list)

# Horizon chart parameters
n_bands = 3
band_height = df["value"].abs().max() / n_bands

# Create band data with human-readable labels
band_data = []
intensity_labels = {0: "Low", 1: "Medium", 2: "High"}

for _, row in df.iterrows():
    val = row["value"]
    for band in range(n_bands):
        band_min = band * band_height
        if val >= 0:
            band_val = max(0, min(val - band_min, band_height))
            band_data.append(
                {
                    "date": row["date"],
                    "series": row["series"],
                    "band": band,
                    "value": band_val,
                    "direction": "positive",
                    "label": f"Positive {intensity_labels[band]}",
                }
            )
        else:
            abs_val = abs(val)
            band_val = max(0, min(abs_val - band_min, band_height))
            band_data.append(
                {
                    "date": row["date"],
                    "series": row["series"],
                    "band": band,
                    "value": band_val,
                    "direction": "negative",
                    "label": f"Negative {intensity_labels[band]}",
                }
            )

band_df = pd.DataFrame(band_data)

# Colorblind-safe diverging colors using BrBG-inspired palette
# Positive: shades of blue-green, Negative: shades of brown/red
positive_colors = ["#d4e9f0", "#5ba3c0", "#1d6a8e"]
negative_colors = ["#f0d4a8", "#d4944f", "#8b5a2b"]

band_df["color_label"] = band_df["label"]

color_scale = alt.Scale(
    domain=["Positive Low", "Positive Medium", "Positive High", "Negative Low", "Negative Medium", "Negative High"],
    range=positive_colors + negative_colors,
)

# Create the horizon chart
chart = (
    alt.Chart(band_df)
    .mark_area()
    .encode(
        x=alt.X("date:T", title="Time", axis=alt.Axis(format="%H:%M", labelFontSize=18, titleFontSize=22)),
        y=alt.Y("value:Q", title=None, axis=None, scale=alt.Scale(domain=[0, band_height])),
        color=alt.Color(
            "color_label:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Intensity",
                orient="right",
                titleFontSize=18,
                labelFontSize=16,
                symbolSize=200,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                labelColor=INK_SOFT,
                titleColor=INK,
            ),
        ),
        tooltip=["date:T", "series:N", "value:Q"],
        order=alt.Order("band:O"),
    )
    .properties(width=1400, height=80)
    .facet(
        row=alt.Row(
            "series:N",
            title=None,
            header=alt.Header(labelFontSize=16, labelAngle=0, labelAlign="left", labelPadding=10),
        )
    )
    .properties(
        title=alt.Title("horizon-basic · altair · anyplot.ai", fontSize=28, anchor="start", offset=20, color=INK)
    )
    .configure_facet(spacing=5)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
