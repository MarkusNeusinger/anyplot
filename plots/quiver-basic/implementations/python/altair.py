""" pyplots.ai
quiver-basic: Basic Quiver Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Create a 15x15 grid with circular rotation pattern (u = -y, v = x)
np.random.seed(42)
grid_size = 15
x_range = np.linspace(-2, 2, grid_size)
y_range = np.linspace(-2, 2, grid_size)
X, Y = np.meshgrid(x_range, y_range)
x_flat = X.flatten()
y_flat = Y.flatten()

# Circular rotation field: u = -y, v = x
U = -y_flat
V = x_flat

# Calculate magnitude for color encoding
magnitude = np.sqrt(U**2 + V**2)

# Normalize vectors for consistent arrow length, then scale
scale = 0.12
mag_safe = np.where(magnitude > 0, magnitude, 1)
U_norm = np.where(magnitude > 0, U / mag_safe * scale, 0)
V_norm = np.where(magnitude > 0, V / mag_safe * scale, 0)

# Create dataframe with arrow start and end points
df = pd.DataFrame({"x": x_flat, "y": y_flat, "x2": x_flat + U_norm, "y2": y_flat + V_norm, "magnitude": magnitude})

# Create arrowhead geometry (small triangle at the end of each arrow)
arrow_head_size = 0.04
angle = np.arctan2(V_norm, U_norm)

# Left and right points of arrowhead
df_heads = pd.DataFrame(
    {
        "x": df["x2"],
        "y": df["y2"],
        "x_left": df["x2"] - arrow_head_size * np.cos(angle - 0.4),
        "y_left": df["y2"] - arrow_head_size * np.sin(angle - 0.4),
        "x_right": df["x2"] - arrow_head_size * np.cos(angle + 0.4),
        "y_right": df["y2"] - arrow_head_size * np.sin(angle + 0.4),
        "magnitude": magnitude,
    }
)

# Build arrow data for line marks (shaft + two head lines per arrow)
arrow_data = []
for i in range(len(df)):
    mag = df.iloc[i]["magnitude"]
    # Arrow shaft
    arrow_data.append(
        {
            "x": df.iloc[i]["x"],
            "y": df.iloc[i]["y"],
            "x2": df.iloc[i]["x2"],
            "y2": df.iloc[i]["y2"],
            "magnitude": mag,
            "arrow_id": i,
        }
    )
    # Left head line
    arrow_data.append(
        {
            "x": df_heads.iloc[i]["x"],
            "y": df_heads.iloc[i]["y"],
            "x2": df_heads.iloc[i]["x_left"],
            "y2": df_heads.iloc[i]["y_left"],
            "magnitude": mag,
            "arrow_id": i,
        }
    )
    # Right head line
    arrow_data.append(
        {
            "x": df_heads.iloc[i]["x"],
            "y": df_heads.iloc[i]["y"],
            "x2": df_heads.iloc[i]["x_right"],
            "y2": df_heads.iloc[i]["y_right"],
            "magnitude": mag,
            "arrow_id": i,
        }
    )

arrow_df = pd.DataFrame(arrow_data)

# Create the chart using rule marks for arrows with magnitude-based coloring
chart = (
    alt.Chart(arrow_df)
    .mark_rule(strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", title="X Position", scale=alt.Scale(domain=[-2.5, 2.5])),
        y=alt.Y("y:Q", title="Y Position", scale=alt.Scale(domain=[-2.5, 2.5])),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color(
            "magnitude:Q",
            scale=alt.Scale(scheme="viridis"),
            title="Magnitude",
            legend=alt.Legend(titleFontSize=18, labelFontSize=16),
        ),
    )
    .properties(
        width=1600, height=900, title=alt.Title("quiver-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
