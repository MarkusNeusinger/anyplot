""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: altair 6.0.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Alpine hiking trail ~120 km with realistic terrain
np.random.seed(42)
num_points = 480
distance = np.linspace(0, 120, num_points)

# Build realistic elevation profile with multiple peaks and valleys
elevation = 800 + np.zeros(num_points)
# Broad terrain shape using sine components
elevation += 600 * np.sin(distance * np.pi / 60) ** 2
elevation += 300 * np.sin(distance * np.pi / 30 + 1.2) ** 2
elevation += 200 * np.sin(distance * np.pi / 15 + 0.5)
# Add ruggedness
elevation += np.cumsum(np.random.randn(num_points) * 3)
elevation += np.random.randn(num_points) * 15
# Smooth slightly
kernel = np.ones(5) / 5
elevation = np.convolve(elevation, kernel, mode="same")
elevation = np.clip(elevation, 600, 2800)

df = pd.DataFrame({"distance": distance, "elevation": elevation})

# Landmarks along the trail
landmarks = pd.DataFrame(
    {
        "name": [
            "Grindelwald\n(Start)",
            "Bachsee\nLake",
            "Faulhorn\nSummit",
            "Schynige\nPlatte",
            "Kleine\nScheidegg",
            "Männlichen\nPass",
            "Wengen\n(End)",
        ],
        "distance": [0.0, 18.0, 35.0, 55.0, 75.0, 95.0, 120.0],
    }
)
# Get elevation at each landmark by interpolation
landmarks["elevation"] = np.interp(landmarks["distance"], distance, elevation)

# Area chart - terrain silhouette with gradient fill
area = (
    alt.Chart(df)
    .mark_area(
        line={"color": "#306998", "strokeWidth": 2.5},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(48, 105, 152, 0.08)", offset=0),
                alt.GradientStop(color="rgba(48, 105, 152, 0.50)", offset=1),
            ],
            x1=1,
            x2=1,
            y1=1,
            y2=0,
        ),
    )
    .encode(
        x=alt.X("distance:Q", title="Distance (km)", scale=alt.Scale(domain=[0, 125])),
        y=alt.Y("elevation:Q", title="Elevation (m)", scale=alt.Scale(domain=[400, 3000])),
        tooltip=[
            alt.Tooltip("distance:Q", title="Distance", format=".1f"),
            alt.Tooltip("elevation:Q", title="Elevation", format=".0f"),
        ],
    )
)

# Landmark vertical rules
landmark_rules = (
    alt.Chart(landmarks)
    .mark_rule(color="#8B4513", strokeWidth=1.2, strokeDash=[6, 4], opacity=0.6)
    .encode(x="distance:Q")
)

# Landmark points on the profile line
landmark_points = (
    alt.Chart(landmarks)
    .mark_circle(size=100, color="#8B4513", stroke="white", strokeWidth=1.5)
    .encode(x="distance:Q", y="elevation:Q")
)

# Landmark text labels above points
landmark_labels = (
    alt.Chart(landmarks)
    .mark_text(align="center", dy=-22, fontSize=13, fontWeight="bold", color="#4a3520", lineBreak="\n")
    .encode(x="distance:Q", y="elevation:Q", text="name:N")
)

# Elevation labels at landmarks (show elevation value)
elevation_labels = (
    alt.Chart(landmarks)
    .mark_text(align="center", dy=-60, fontSize=11, color="#666666")
    .encode(x="distance:Q", y="elevation:Q", text=alt.Text("elevation:Q", format=".0f"))
)

# Compose layered chart
chart = (
    alt.layer(area, landmark_rules, landmark_points, landmark_labels, elevation_labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Bernese Oberland Trail · area-elevation-profile · altair · pyplots.ai",
            fontSize=28,
            subtitle="120 km hiking transect from Grindelwald to Wengen  ·  Vertical exaggeration ~10×",
            subtitleFontSize=16,
            subtitleColor="#777777",
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15, grid=True)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
