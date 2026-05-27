""" anyplot.ai
facet-grid: Faceted Grid Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-13
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

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Crop yield across different soil types and seasons
np.random.seed(42)

soil_types = ["Sandy", "Clay", "Loam"]
seasons = ["Spring", "Summer", "Fall"]
crop_types = ["Wheat", "Corn", "Soybean"]
n_per_group = 20

data = []
for soil in soil_types:
    for season in seasons:
        for crop in crop_types:
            base_yield = {"Sandy": 3.5, "Clay": 4.0, "Loam": 5.0}[soil]
            season_mult = {"Spring": 0.9, "Summer": 1.1, "Fall": 1.0}[season]
            crop_base = {"Wheat": 3.8, "Corn": 4.5, "Soybean": 3.2}[crop]

            yield_val = np.random.normal(base_yield * season_mult + crop_base, 0.8, n_per_group)
            water = np.random.normal(50 + crop_base * 5, 8, n_per_group)

            for y, w in zip(yield_val, water, strict=True):
                data.append(
                    {
                        "Yield (tons/ha)": max(0.5, y),
                        "Water Usage (mm)": max(20, w),
                        "Soil Type": soil,
                        "Season": season,
                        "Crop": crop,
                    }
                )

df = pd.DataFrame(data)

# Create faceted chart with scatter plots
chart = (
    alt.Chart(df)
    .mark_circle(size=150, opacity=0.7)
    .encode(
        x=alt.X("Water Usage (mm):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Yield (tons/ha):Q", scale=alt.Scale(zero=False)),
        color=alt.Color("Crop:N", scale=alt.Scale(domain=crop_types, range=IMPRINT[:3])),
        tooltip=["Yield (tons/ha)", "Water Usage (mm)", "Soil Type", "Season", "Crop"],
    )
    .properties(width=320, height=260)
    .facet(
        column=alt.Column(
            "Season:N", header=alt.Header(titleFontSize=22, labelFontSize=18), sort=["Spring", "Summer", "Fall"]
        ),
        row=alt.Row(
            "Soil Type:N", header=alt.Header(titleFontSize=22, labelFontSize=18), sort=["Sandy", "Clay", "Loam"]
        ),
    )
    .configure_axis(
        labelFontSize=16,
        titleFontSize=20,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_legend(
        titleFontSize=18,
        labelFontSize=16,
        symbolSize=180,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(fontSize=28, color=INK)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .properties(title="facet-grid · altair · anyplot.ai", background=PAGE_BG)
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
