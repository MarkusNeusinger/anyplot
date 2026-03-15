"""pyplots.ai
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
elevation = 900 + np.zeros(num_points)
# Broad terrain shape - two major peaks matching real Bernese Oberland terrain
elevation += 1000 * np.sin(distance * np.pi / 60) ** 2
elevation += 500 * np.sin(distance * np.pi / 30 + 1.2) ** 2
elevation += 250 * np.sin(distance * np.pi / 15 + 0.5)
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
        y=alt.Y("elevation:Q", title="Elevation (m)", scale=alt.Scale(domain=[400, 2800])),
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

# Split landmarks into edge and middle groups for alignment
lm_start = landmarks[landmarks["distance"] == 0.0]
lm_end = landmarks[landmarks["distance"] == 120.0]
lm_mid = landmarks[(landmarks["distance"] > 0.0) & (landmarks["distance"] < 120.0)]

# Landmark text labels - left-aligned for start, right-aligned for end, centered for middle
landmark_labels_start = (
    alt.Chart(lm_start)
    .mark_text(align="left", dx=8, dy=-24, fontSize=14, fontWeight="bold", color="#4a3520", lineBreak="\n")
    .encode(x="distance:Q", y="elevation:Q", text="name:N")
)
landmark_labels_end = (
    alt.Chart(lm_end)
    .mark_text(align="right", dx=-8, dy=-24, fontSize=14, fontWeight="bold", color="#4a3520", lineBreak="\n")
    .encode(x="distance:Q", y="elevation:Q", text="name:N")
)
landmark_labels_mid = (
    alt.Chart(lm_mid)
    .mark_text(align="center", dy=-24, fontSize=14, fontWeight="bold", color="#4a3520", lineBreak="\n")
    .encode(x="distance:Q", y="elevation:Q", text="name:N")
)

# Elevation value labels - matching alignment
elev_labels_start = (
    alt.Chart(lm_start)
    .mark_text(align="left", dx=8, dy=-65, fontSize=13, color="#555555", fontWeight=600)
    .encode(x="distance:Q", y="elevation:Q", text=alt.Text("elevation:Q", format=".0f"))
)
elev_labels_end = (
    alt.Chart(lm_end)
    .mark_text(align="right", dx=-8, dy=-65, fontSize=13, color="#555555", fontWeight=600)
    .encode(x="distance:Q", y="elevation:Q", text=alt.Text("elevation:Q", format=".0f"))
)
elev_labels_mid = (
    alt.Chart(lm_mid)
    .mark_text(align="center", dy=-65, fontSize=13, color="#555555", fontWeight=600)
    .encode(x="distance:Q", y="elevation:Q", text=alt.Text("elevation:Q", format=".0f"))
)

# Compose layered chart
chart = (
    alt.layer(
        area,
        landmark_rules,
        landmark_points,
        landmark_labels_start,
        landmark_labels_mid,
        landmark_labels_end,
        elev_labels_start,
        elev_labels_mid,
        elev_labels_end,
    )
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
