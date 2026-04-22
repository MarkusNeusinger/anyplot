""" pyplots.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: altair 6.0.0 | Python 3.13.11
Quality: 68/100 | Created: 2026-01-11
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - synthetic wind observations from weather stations on a grid
np.random.seed(42)

# Create a grid of observation points (6x5 grid = 30 stations)
x_coords = np.linspace(0, 10, 6)
y_coords = np.linspace(0, 8, 5)
xx, yy = np.meshgrid(x_coords, y_coords)
x = xx.flatten()
y = yy.flatten()

# Generate wind components (u: east-west, v: north-south) in knots
# Include some calm conditions (< 2.5 knots) and high winds (>= 50 knots)
np.random.seed(42)
u = np.random.uniform(-30, 30, len(x))
v = np.random.uniform(-25, 25, len(x))

# Force a few calm conditions and high winds (pennants) for feature coverage
u[0] = 0.5
v[0] = 0.3  # Calm (~0.6 knots)
u[5] = 1.0
v[5] = -0.8  # Calm (~1.3 knots)
u[15] = 45
v[15] = 35  # High wind (~57 knots - 1 pennant)
u[20] = 55
v[20] = 10  # High wind (~56 knots - 1 pennant)

# Calculate wind speed and direction
wind_speed = np.sqrt(u**2 + v**2)
# Direction FROM which wind blows (meteorological convention)
wind_direction = np.degrees(np.arctan2(-u, -v))

# Create DataFrame
df = pd.DataFrame({"x": x, "y": y, "u": u, "v": v, "speed": wind_speed, "direction": wind_direction})

# Separate calm winds (< 2.5 knots) - shown as open circles
calm_df = df[df["speed"] < 2.5].copy()
barbed_df = df[df["speed"] >= 2.5].copy()

# Scale factor for arrow length
scale = 0.03

# Calculate staff endpoints for barbed winds
barbed_df = barbed_df.copy()
barbed_df["dx"] = -barbed_df["u"] * scale
barbed_df["dy"] = -barbed_df["v"] * scale
barbed_df["x2"] = barbed_df["x"] + barbed_df["dx"]
barbed_df["y2"] = barbed_df["y"] + barbed_df["dy"]

# Create barb and pennant data (KISS - inline processing)
barb_records = []
pennant_records = []

for _, row in barbed_df.iterrows():
    speed = row["speed"]
    direction_rad = np.radians(row["direction"])

    # Unit vector in wind direction (pointing INTO the wind)
    ux = -np.sin(direction_rad)
    uy = -np.cos(direction_rad)

    # Perpendicular vector for barb flags (left side in NH)
    px = -uy
    py = ux

    # Staff length for barb positioning
    staff_length = speed * scale

    # Add barbs based on speed
    remaining_speed = speed
    barb_position = 0.85
    barb_count = 0

    # Add pennants (50 knots each) - represented by triangle markers
    while remaining_speed >= 50 and barb_count < 3:
        pos_factor = barb_position - barb_count * 0.18
        bx = row["x"] + ux * staff_length * pos_factor
        by = row["y"] + uy * staff_length * pos_factor
        # Store pennant position and angle for triangle marker
        pennant_records.append(
            {
                "x": bx + px * 0.15,  # Offset slightly for visual centering
                "y": by + py * 0.15,
                "angle": row["direction"] + 90,  # Rotate to point perpendicular to staff
                "speed": speed,
            }
        )
        remaining_speed -= 50
        barb_count += 1

    # Add full barbs (10 knots each)
    while remaining_speed >= 10 and barb_count < 6:
        pos_factor = barb_position - barb_count * 0.12
        bx = row["x"] + ux * staff_length * pos_factor
        by = row["y"] + uy * staff_length * pos_factor
        barb_records.append({"x": bx, "y": by, "type": "full", "x2": bx + px * 0.35, "y2": by + py * 0.35})
        remaining_speed -= 10
        barb_count += 1

    # Add half barb (5 knots) if remaining
    if remaining_speed >= 5:
        pos_factor = barb_position - barb_count * 0.12
        bx = row["x"] + ux * staff_length * pos_factor
        by = row["y"] + uy * staff_length * pos_factor
        barb_records.append({"x": bx, "y": by, "type": "half", "x2": bx + px * 0.18, "y2": by + py * 0.18})

barb_df = pd.DataFrame(barb_records) if barb_records else pd.DataFrame(columns=["x", "y", "x2", "y2"])
pennant_df = pd.DataFrame(pennant_records) if pennant_records else pd.DataFrame(columns=["x", "y", "angle"])

# Layer 1: Staff (main line of wind barb) for barbed winds only
staff = (
    alt.Chart(barbed_df)
    .mark_rule(strokeWidth=2.5, color="#306998")
    .encode(
        x=alt.X("x:Q", title="Longitude (degrees E)", scale=alt.Scale(domain=[-1, 12])),
        y=alt.Y("y:Q", title="Latitude (degrees N)", scale=alt.Scale(domain=[-1, 9.5])),
        x2="x2:Q",
        y2="y2:Q",
        tooltip=[
            alt.Tooltip("x:Q", title="Longitude", format=".1f"),
            alt.Tooltip("y:Q", title="Latitude", format=".1f"),
            alt.Tooltip("speed:Q", title="Wind Speed (knots)", format=".1f"),
            alt.Tooltip("direction:Q", title="Direction (deg from N)", format=".0f"),
        ],
    )
)

# Layer 2: Station points for barbed winds (base of barb)
points = (
    alt.Chart(barbed_df)
    .mark_circle(size=80, color="#306998")
    .encode(x="x:Q", y="y:Q", tooltip=[alt.Tooltip("speed:Q", title="Speed (knots)", format=".1f")])
)

# Layer 3: Calm wind indicators (open circles for < 2.5 knots)
# Using larger size and thicker stroke for better visibility
calm_circles = (
    alt.Chart(calm_df)
    .mark_circle(size=400, stroke="#306998", strokeWidth=4, fill="white")
    .encode(
        x="x:Q",
        y="y:Q",
        tooltip=[
            alt.Tooltip("x:Q", title="Longitude", format=".1f"),
            alt.Tooltip("y:Q", title="Latitude", format=".1f"),
            alt.Tooltip("speed:Q", title="Wind Speed (knots)", format=".1f"),
        ],
    )
)

# Layer 4: Barb flags (speed indicators)
barbs = (
    (alt.Chart(barb_df).mark_rule(strokeWidth=2.5, color="#306998").encode(x="x:Q", y="y:Q", x2="x2:Q", y2="y2:Q"))
    if len(barb_df) > 0
    else alt.Chart(pd.DataFrame({"x": []})).mark_point()
)

# Layer 5: Pennant triangles (filled markers for 50 knots)
# Build pennants as small filled triangles using polygon-like mark_line
pennant_layer_list = []
if len(pennant_df) > 0:
    for _, prow in pennant_df.iterrows():
        # Create a filled triangle outline
        px, py = prow["x"], prow["y"]
        angle_rad = np.radians(prow["angle"])
        # Small triangle vertices (scaled to data coordinates)
        tri_size = 0.18
        v1_x = px + tri_size * np.cos(angle_rad)
        v1_y = py + tri_size * np.sin(angle_rad)
        v2_x = px + tri_size * np.cos(angle_rad + 2.09)  # 120 degrees
        v2_y = py + tri_size * np.sin(angle_rad + 2.09)
        v3_x = px + tri_size * np.cos(angle_rad - 2.09)
        v3_y = py + tri_size * np.sin(angle_rad - 2.09)
        tri_data = pd.DataFrame({"x": [v1_x, v2_x, v3_x, v1_x], "y": [v1_y, v2_y, v3_y, v1_y], "order": [0, 1, 2, 3]})
        # Draw triangle outline (filled appearance via thick stroke)
        pennant_layer_list.append(
            alt.Chart(tri_data).mark_line(strokeWidth=4, color="#306998").encode(x="x:Q", y="y:Q", order="order:O")
        )
        # Add center point to give filled appearance
        center_data = pd.DataFrame({"x": [px], "y": [py]})
        pennant_layer_list.append(
            alt.Chart(center_data)
            .mark_point(shape="triangle", size=200, color="#306998", filled=True)
            .encode(x="x:Q", y="y:Q")
        )
pennants = alt.layer(*pennant_layer_list) if pennant_layer_list else alt.Chart(pd.DataFrame({"x": []})).mark_point()

# Create legend as text annotations in the top-right area of the plot
# Using explicit data coordinates that are visible within the axis domain
legend_items = pd.DataFrame(
    {
        "x": [9.2, 9.2, 9.2, 9.2, 9.2],
        "y": [8.8, 8.2, 7.6, 7.0, 6.4],
        "label": [
            "Wind Barb Key:",
            "○ Calm (< 2.5 kt)",
            "— Half barb = 5 kt",
            "—— Full barb = 10 kt",
            "▲ Pennant = 50 kt",
        ],
    }
)

legend_text = (
    alt.Chart(legend_items)
    .mark_text(align="left", baseline="middle", fontSize=14, font="monospace", fontWeight="bold", color="#333333")
    .encode(x="x:Q", y="y:Q", text="label:N")
)

# Main wind barb chart with all layers including legend
chart = (
    alt.layer(staff, points, calm_circles, barbs, pennants, legend_text)
    .properties(width=1600, height=900, title=alt.Title("windbarb-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG only
chart.save("plot.png", scale_factor=3.0)
