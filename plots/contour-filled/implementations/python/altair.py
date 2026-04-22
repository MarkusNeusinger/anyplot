"""pyplots.ai
contour-filled: Filled Contour Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 86/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Marching squares contour extraction (pure numpy implementation)
def find_contours(Z, level, x_coords, y_coords):
    """Extract contour lines using marching squares algorithm."""
    rows, cols = Z.shape
    segments = []

    # Marching squares lookup table for edge intersections
    for i in range(rows - 1):
        for j in range(cols - 1):
            # Get cell corner values
            z00, z01, z10, z11 = Z[i, j], Z[i, j + 1], Z[i + 1, j], Z[i + 1, j + 1]
            cell = [z00, z01, z10, z11]

            # Compute case index based on which corners are above level
            case = sum([1 << k for k, v in enumerate(cell) if v >= level])

            if case in (0, 15):  # All above or all below
                continue

            # Cell coordinates
            x0, x1 = x_coords[j], x_coords[j + 1]
            y0, y1 = y_coords[i], y_coords[i + 1]

            # Interpolate edge crossings
            def interp(v1, v2, c1, c2):
                if abs(v2 - v1) < 1e-10:
                    return (c1 + c2) / 2
                t = (level - v1) / (v2 - v1)
                return c1 + t * (c2 - c1)

            edges = {
                "top": (interp(z00, z01, x0, x1), y0),
                "bottom": (interp(z10, z11, x0, x1), y1),
                "left": (x0, interp(z00, z10, y0, y1)),
                "right": (x1, interp(z01, z11, y0, y1)),
            }

            # Map case to line segments
            cases = {
                1: [("left", "top")],
                2: [("top", "right")],
                3: [("left", "right")],
                4: [("bottom", "left")],
                5: [("top", "bottom")],
                6: [("top", "left"), ("bottom", "right")]
                if (z00 + z11) / 2 >= level
                else [("top", "right"), ("bottom", "left")],
                7: [("bottom", "right")],
                8: [("right", "bottom")],
                9: [("left", "bottom"), ("right", "top")]
                if (z00 + z11) / 2 >= level
                else [("left", "top"), ("right", "bottom")],
                10: [("top", "bottom")],
                11: [("left", "bottom")],
                12: [("left", "right")],
                13: [("top", "right")],
                14: [("left", "top")],
            }

            for e1, e2 in cases.get(case, []):
                segments.append((edges[e1], edges[e2]))

    return segments


# Data - Gaussian peaks on a 2D grid (80x80 for smooth contours)
np.random.seed(42)
n_points = 80
x = np.linspace(-3, 3, n_points)
y = np.linspace(-3, 3, n_points)
X, Y = np.meshgrid(x, y)

# Create interesting surface with two Gaussian peaks and a valley
Z = (
    1.5 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2) / 0.8)  # Peak at (1, 1)
    + 1.2 * np.exp(-((X + 1) ** 2 + (Y + 0.5) ** 2) / 1.0)  # Peak at (-1, -0.5)
    - 0.6 * np.exp(-((X) ** 2 + (Y - 1.5) ** 2) / 0.6)  # Valley at (0, 1.5)
    + 0.2 * np.sin(X * 2) * np.cos(Y * 2)  # Subtle ripples
)

# Create discrete contour levels (12 levels for smoother gradient)
n_levels = 12
z_min, z_max = Z.min(), Z.max()
levels = np.linspace(z_min, z_max, n_levels + 1)

# Bin z-values into discrete levels for filled contour appearance
Z_binned = np.digitize(Z, levels) - 1
Z_binned = np.clip(Z_binned, 0, n_levels - 1)
# Map back to level center values for color mapping
level_centers = (levels[:-1] + levels[1:]) / 2
Z_discrete = level_centers[Z_binned]

# Calculate step size for proper rectangle sizing
step = x[1] - x[0]
half_step = step / 2

# Flatten grid data for Altair with explicit rectangle bounds
df = pd.DataFrame(
    {
        "x": X.ravel() - half_step,
        "x2": X.ravel() + half_step,
        "y": Y.ravel() - half_step,
        "y2": Y.ravel() + half_step,
        "z": Z_discrete.ravel(),
    }
)

# Create filled contour using mark_rect with discrete color bands
filled_contour = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X(
            "x:Q",
            title="X Coordinate",
            scale=alt.Scale(domain=[-3.1, 3.1]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, tickCount=7),
        ),
        x2="x2:Q",
        y=alt.Y(
            "y:Q",
            title="Y Coordinate",
            scale=alt.Scale(domain=[-3.1, 3.1]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, tickCount=7),
        ),
        y2="y2:Q",
        color=alt.Color(
            "z:Q",
            title="Intensity",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(titleFontSize=20, labelFontSize=16, gradientLength=400, gradientThickness=25),
        ),
    )
)

# Extract contour lines using marching squares
contour_lines_data = []
contour_levels_subset = levels[2:-2:2]  # Select 5 evenly-spaced levels

for idx, level_val in enumerate(contour_levels_subset):
    segments = find_contours(Z, level_val, x, y)
    for seg_idx, (p1, p2) in enumerate(segments):
        contour_id = f"L{idx}_S{seg_idx}"
        contour_lines_data.append({"x": p1[0], "y": p1[1], "order": 0, "contour_id": contour_id})
        contour_lines_data.append({"x": p2[0], "y": p2[1], "order": 1, "contour_id": contour_id})

contour_df = pd.DataFrame(contour_lines_data)

# Create contour lines overlay using mark_line for proper isolines
contour_overlay = (
    alt.Chart(contour_df)
    .mark_line(strokeWidth=1.2, opacity=0.5)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-3.1, 3.1])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-3.1, 3.1])),
        order="order:O",
        detail="contour_id:N",
        color=alt.value("#333333"),
    )
)

# Combine layers
chart = (
    alt.layer(filled_contour, contour_overlay)
    .properties(
        width=1400,
        height=800,
        title=alt.Title(text="contour-filled · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
)

# Save PNG (4800 × 2700 px with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML
chart.save("plot.html")
