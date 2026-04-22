""" pyplots.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Wind direction frequency data
np.random.seed(42)
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
angles = [0, 45, 90, 135, 180, 225, 270, 315]  # degrees from north

# Simulate realistic wind frequency with prevailing westerlies
base_freq = [12, 8, 10, 6, 9, 18, 22, 16]  # Higher for W, SW, NW
frequencies = [f + np.random.randint(-2, 3) for f in base_freq]

# Create DataFrame with angle in radians for Altair
df = pd.DataFrame({"direction": directions, "angle": angles, "frequency": frequencies})

# Calculate start and end angles for each bar (in radians)
# Altair uses radians, and we need to center each bar on its direction
bar_width = 40  # degrees
df["theta_start"] = np.radians(df["angle"] - bar_width / 2)
df["theta_end"] = np.radians(df["angle"] + bar_width / 2)

# Create the polar bar chart using mark_arc
base = alt.Chart(df)

# Bars radiating from center using arc marks
bars = base.mark_arc(stroke="white", strokeWidth=2).encode(
    theta=alt.Theta("theta_start:Q", scale=alt.Scale(domain=[0, 2 * np.pi])),
    theta2="theta_end:Q",
    radius=alt.Radius("frequency:Q", scale=alt.Scale(type="linear", zero=True, rangeMin=0)),
    color=alt.Color(
        "frequency:Q",
        scale=alt.Scale(scheme="blues"),
        legend=alt.Legend(title="Frequency (days)", titleFontSize=18, labelFontSize=16, orient="right"),
    ),
    tooltip=[alt.Tooltip("direction:N", title="Direction"), alt.Tooltip("frequency:Q", title="Frequency (days)")],
)

# Add direction labels around the perimeter
max_freq = max(frequencies) * 1.25
label_df = pd.DataFrame({"direction": directions, "angle_rad": np.radians(angles), "radius": [max_freq] * 8})

# Calculate x, y positions for labels
label_df["x"] = label_df["radius"] * np.sin(label_df["angle_rad"])
label_df["y"] = label_df["radius"] * np.cos(label_df["angle_rad"])

labels = (
    alt.Chart(label_df)
    .mark_text(fontSize=20, fontWeight="bold", color="#306998")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), text="direction:N")
)

# Combine bars and labels
chart = (
    alt.layer(bars, labels)
    .properties(
        width=900,
        height=900,
        title=alt.Title(text="polar-bar · altair · pyplots.ai", fontSize=28, anchor="middle", color="#333333"),
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save outputs
chart.save("plot.png", scale_factor=4.5)
chart.save("plot.html")
