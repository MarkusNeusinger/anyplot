""" pyplots.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_text,
    geom_point,
    geom_polygon,
    geom_segment,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Surface wind observations from a grid of weather stations
np.random.seed(42)

# Create a grid of observation points (6x5 grid = 30 stations)
x_coords = np.linspace(0, 10, 6)
y_coords = np.linspace(0, 8, 5)
xx, yy = np.meshgrid(x_coords, y_coords)
x = xx.flatten()
y = yy.flatten()

# Generate wind components (u: east-west, v: north-south) in knots
u = np.random.uniform(-30, 30, len(x))
v = np.random.uniform(-25, 25, len(x))

# Force calm conditions (< 2.5 knots) for feature coverage
u[0] = 0.5
v[0] = 0.3
u[5] = 1.0
v[5] = -0.8

# Force high winds with pennants (50+ knots)
u[15] = 45
v[15] = 35
u[20] = 55
v[20] = 10

# Calculate wind speed and direction
wind_speed = np.sqrt(u**2 + v**2)
# Direction FROM which wind blows (meteorological convention)
wind_direction_rad = np.arctan2(-u, -v)

# Build wind barb components: staffs, barb flags, pennants, calm circles
staff_records = []
barb_records = []
pennant_records = []
calm_records = []

scale = 0.06  # Scale factor for staff length

for i in range(len(x)):
    speed = wind_speed[i]

    if speed < 2.5:
        # Calm winds - open circle
        calm_records.append({"x": x[i], "y": y[i], "speed": speed})
    else:
        # Calculate staff direction (pointing INTO the wind, from which it blows)
        dir_rad = wind_direction_rad[i]
        ux = -np.sin(dir_rad)
        uy = -np.cos(dir_rad)

        # Staff length proportional to speed but capped for readability
        staff_len = min(speed * scale, 2.5)

        # Staff endpoint
        x2 = x[i] + ux * staff_len
        y2 = y[i] + uy * staff_len
        staff_records.append({"x": x[i], "y": y[i], "xend": x2, "yend": y2, "speed": speed})

        # Perpendicular vector for barb flags (left side in Northern Hemisphere)
        px = -uy
        py = ux

        # Add barbs and pennants based on speed
        remaining_speed = speed
        barb_pos = 0.85  # Start position along staff (fraction from base)
        barb_idx = 0

        # Pennants (50 knots each) - represented as filled triangular flags
        pennant_id = 0
        while remaining_speed >= 50 and barb_idx < 3:
            pos_factor = barb_pos - barb_idx * 0.15
            bx = x[i] + ux * staff_len * pos_factor
            by = y[i] + uy * staff_len * pos_factor

            # Create triangle vertices for pennant (filled triangle per meteorological standard)
            tri_base = 0.25
            tri_height = 0.35
            # Tip of triangle (along perpendicular)
            tip_x = bx + px * tri_height
            tip_y = by + py * tri_height
            # Base along staff direction
            base1_x = bx - ux * tri_base / 2
            base1_y = by - uy * tri_base / 2
            base2_x = bx + ux * tri_base / 2
            base2_y = by + uy * tri_base / 2

            # Store pennant vertices for filled polygon (3 vertices per triangle)
            group_id = f"{i}_{pennant_id}"
            pennant_records.append({"x": base1_x, "y": base1_y, "group": group_id, "order": 1})
            pennant_records.append({"x": tip_x, "y": tip_y, "group": group_id, "order": 2})
            pennant_records.append({"x": base2_x, "y": base2_y, "group": group_id, "order": 3})

            remaining_speed -= 50
            barb_idx += 1
            pennant_id += 1

        # Full barbs (10 knots each)
        while remaining_speed >= 10 and barb_idx < 8:
            pos_factor = barb_pos - barb_idx * 0.12
            bx = x[i] + ux * staff_len * pos_factor
            by = y[i] + uy * staff_len * pos_factor

            # Full barb - longer line
            barb_len = 0.40
            barb_records.append(
                {"x": bx, "y": by, "xend": bx + px * barb_len, "yend": by + py * barb_len, "type": "full"}
            )
            remaining_speed -= 10
            barb_idx += 1

        # Half barb (5 knots)
        if remaining_speed >= 5:
            pos_factor = barb_pos - barb_idx * 0.12
            bx = x[i] + ux * staff_len * pos_factor
            by = y[i] + uy * staff_len * pos_factor

            # Half barb - shorter line
            barb_len = 0.22
            barb_records.append(
                {"x": bx, "y": by, "xend": bx + px * barb_len, "yend": by + py * barb_len, "type": "half"}
            )

# Create DataFrames
staff_df = pd.DataFrame(staff_records) if staff_records else pd.DataFrame(columns=["x", "y", "xend", "yend", "speed"])
barb_df = pd.DataFrame(barb_records) if barb_records else pd.DataFrame(columns=["x", "y", "xend", "yend", "type"])
pennant_df = pd.DataFrame(pennant_records) if pennant_records else pd.DataFrame(columns=["x", "y", "group", "order"])
calm_df = pd.DataFrame(calm_records) if calm_records else pd.DataFrame(columns=["x", "y", "speed"])

# Base plot with staffs
plot = (
    ggplot()
    # Layer 1: Staffs (main wind barb lines)
    + geom_segment(data=staff_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#306998", size=1.5)
    # Layer 2: Station points at base of barbs
    + geom_point(data=staff_df, mapping=aes(x="x", y="y"), color="#306998", size=3)
)

# Layer 3: Barb flags (full and half barbs)
if len(barb_df) > 0:
    plot = plot + geom_segment(
        data=barb_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#306998", size=1.5
    )

# Layer 4: Pennants (filled triangular flags for 50 knots - meteorological standard)
if len(pennant_df) > 0:
    plot = plot + geom_polygon(
        data=pennant_df, mapping=aes(x="x", y="y", group="group"), fill="#306998", color="#306998", size=0.5
    )

# Layer 5: Calm wind indicators (open circles)
if len(calm_df) > 0:
    plot = plot + geom_point(data=calm_df, mapping=aes(x="x", y="y"), color="#306998", fill="white", size=6, stroke=1.5)

# Add legend annotation (positioned in lower right to avoid data overlap)
legend_text = "Wind Barb Key:\n○  Calm (< 2.5 kt)\n╲  Half barb = 5 kt\n╲╲ Full barb = 10 kt\n▲  Pennant = 50 kt"

plot = (
    plot
    + annotate(
        "label",
        x=11.5,
        y=-0.5,
        label=legend_text,
        size=11,
        ha="right",
        va="bottom",
        fill="white",
        alpha=0.9,
        label_padding=0.4,
        color="#306998",
    )
    + scale_x_continuous(limits=(-1, 13))
    + scale_y_continuous(limits=(-1.5, 9))
    + labs(x="Longitude (°E)", y="Latitude (°N)", title="windbarb-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", alpha=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
