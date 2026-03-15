"""pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: altair 6.0.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-15
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
elevation += 1000 * np.sin(distance * np.pi / 60) ** 2
elevation += 500 * np.sin(distance * np.pi / 30 + 1.2) ** 2
elevation += 250 * np.sin(distance * np.pi / 15 + 0.5)
elevation += np.cumsum(np.random.randn(num_points) * 3)
elevation += np.random.randn(num_points) * 15
kernel = np.ones(5) / 5
elevation = np.convolve(elevation, kernel, mode="same")
elevation = np.clip(elevation, 600, 2800)

df = pd.DataFrame({"distance": distance, "elevation": elevation})

# Landmarks along the trail with type for visual differentiation
landmarks = pd.DataFrame(
    {
        "name": [
            "Grindelwald (Start)",
            "Bachsee Lake",
            "Faulhorn Summit",
            "Schynige Platte",
            "Kleine Scheidegg",
            "Männlichen Summit",
            "Wengen (End)",
        ],
        "distance": [0.0, 18.0, 35.0, 55.0, 75.0, 95.0, 120.0],
        "type": ["town", "lake", "summit", "plateau", "pass", "summit", "town"],
    }
)
landmarks["elevation"] = np.interp(landmarks["distance"], distance, elevation)
# Combined label: name + elevation on two lines
landmarks["label"] = landmarks.apply(lambda r: f"{r['name']}\n{r['elevation']:.0f} m", axis=1)

# Tighter axis domains to eliminate wasted canvas space
y_min = int(np.floor(elevation.min() / 100) * 100)

# Area chart - terrain silhouette with gradient fill
area = (
    alt.Chart(df)
    .mark_area(
        line={"color": "#306998", "strokeWidth": 2.5},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color="rgba(48, 105, 152, 0.05)", offset=0),
                alt.GradientStop(color="rgba(48, 105, 152, 0.22)", offset=0.3),
                alt.GradientStop(color="rgba(48, 105, 152, 0.55)", offset=1),
            ],
            x1=1,
            x2=1,
            y1=1,
            y2=0,
        ),
    )
    .encode(
        x=alt.X("distance:Q", title="Distance (km)", scale=alt.Scale(domain=[0, 120])),
        y=alt.Y("elevation:Q", title="Elevation (m)", scale=alt.Scale(domain=[y_min, 2800])),
        tooltip=[
            alt.Tooltip("distance:Q", title="Distance (km)", format=".1f"),
            alt.Tooltip("elevation:Q", title="Elevation (m)", format=".0f"),
        ],
    )
)

# Landmark vertical rules with color by type
landmark_rules = (
    alt.Chart(landmarks)
    .mark_rule(strokeWidth=1, strokeDash=[5, 4], opacity=0.4)
    .encode(x="distance:Q", color=alt.condition(alt.datum.type == "summit", alt.value("#A0522D"), alt.value("#8B7355")))
)

# Landmark points with shape encoding by type
landmark_points = (
    alt.Chart(landmarks)
    .mark_point(size=120, filled=True, stroke="white", strokeWidth=1.5)
    .encode(
        x="distance:Q",
        y="elevation:Q",
        shape=alt.Shape(
            "type:N",
            legend=None,
            scale=alt.Scale(
                domain=["summit", "lake", "pass", "plateau", "town"],
                range=["triangle-up", "diamond", "cross", "square", "circle"],
            ),
        ),
        color=alt.Color(
            "type:N",
            legend=None,
            scale=alt.Scale(
                domain=["summit", "lake", "pass", "plateau", "town"],
                range=["#A0522D", "#4682B4", "#8B7355", "#6B8E23", "#555555"],
            ),
        ),
    )
)

# Combined label layers (name + elevation) - 3 layers by alignment instead of 6
lm_start = landmarks[landmarks["distance"] == 0.0]
lm_end = landmarks[landmarks["distance"] == 120.0]
lm_mid = landmarks[(landmarks["distance"] > 0) & (landmarks["distance"] < 120)]

label_start = (
    alt.Chart(lm_start)
    .mark_text(
        align="left", dx=10, dy=-30, fontSize=14, fontWeight="bold", color="#3A3A3A", lineBreak="\n", lineHeight=18
    )
    .encode(x="distance:Q", y="elevation:Q", text="label:N")
)
label_end = (
    alt.Chart(lm_end)
    .mark_text(
        align="right", dx=-10, dy=-30, fontSize=14, fontWeight="bold", color="#3A3A3A", lineBreak="\n", lineHeight=18
    )
    .encode(x="distance:Q", y="elevation:Q", text="label:N")
)
label_mid = (
    alt.Chart(lm_mid)
    .mark_text(align="center", dy=-30, fontSize=14, fontWeight="bold", lineBreak="\n", lineHeight=18)
    .encode(
        x="distance:Q",
        y="elevation:Q",
        text="label:N",
        color=alt.Color(
            "type:N",
            legend=None,
            scale=alt.Scale(
                domain=["summit", "lake", "pass", "plateau", "town"],
                range=["#6B3A1F", "#2E5E7E", "#5C4E3C", "#4A6317", "#3A3A3A"],
            ),
        ),
    )
)

# Compose layered chart
chart = (
    alt.layer(area, landmark_rules, landmark_points, label_start, label_mid, label_end)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Bernese Oberland Trail · area-elevation-profile · altair · pyplots.ai",
            fontSize=28,
            subtitle="120 km hiking transect from Grindelwald to Wengen  ·  Vertical exaggeration ~10×",
            subtitleFontSize=16,
            subtitleColor="#777777",
            anchor="start",
            offset=12,
        ),
    )
    .configure_axis(
        labelFontSize=18, titleFontSize=22, gridOpacity=0.12, grid=True, domainColor="#999999", tickColor="#999999"
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
