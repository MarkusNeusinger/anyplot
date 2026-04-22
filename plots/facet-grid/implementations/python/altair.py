""" pyplots.ai
facet-grid: Faceted Grid Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


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
            # Base yield varies by soil type
            base_yield = {"Sandy": 3.5, "Clay": 4.0, "Loam": 5.0}[soil]
            # Season affects yield
            season_mult = {"Spring": 0.9, "Summer": 1.1, "Fall": 1.0}[season]
            # Crop type affects yield and water needs
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

# Create faceted chart with scatter plots - facet by soil and season, color by crop
chart = (
    alt.Chart(df)
    .mark_circle(size=100, opacity=0.7)
    .encode(
        x=alt.X("Water Usage (mm):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Yield (tons/ha):Q", scale=alt.Scale(zero=False)),
        color=alt.Color("Crop:N", scale=alt.Scale(domain=crop_types, range=["#306998", "#FFD43B", "#4CAF50"])),
        tooltip=["Yield (tons/ha)", "Water Usage (mm)", "Soil Type", "Season", "Crop"],
    )
    .properties(width=320, height=260)
    .facet(
        column=alt.Column(
            "Season:N", header=alt.Header(titleFontSize=20, labelFontSize=16), sort=["Spring", "Summer", "Fall"]
        ),
        row=alt.Row(
            "Soil Type:N", header=alt.Header(titleFontSize=20, labelFontSize=16), sort=["Sandy", "Clay", "Loam"]
        ),
    )
    .configure_axis(labelFontSize=14, titleFontSize=16)
    .configure_legend(titleFontSize=18, labelFontSize=16, symbolSize=180)
    .configure_title(fontSize=24)
    .properties(title="facet-grid · altair · pyplots.ai")
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
