""" pyplots.ai
contour-basic: Basic Contour Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - 2D Gaussian function on meshgrid
np.random.seed(42)
x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 80)
X, Y = np.meshgrid(x, y)

# Two overlapping Gaussian peaks for interesting contour patterns
Z = np.exp(-((X - 1) ** 2 + (Y - 1) ** 2)) + 0.8 * np.exp(-((X + 1) ** 2 + (Y + 0.5) ** 2))

# Flatten to DataFrame for filled contour background
df_fill = pd.DataFrame({"x": X.ravel(), "y": Y.ravel(), "z": Z.ravel()})

# Extract contour line segments using marching squares algorithm
levels = np.linspace(0.1, 1.6, 10)
segments = []

for level in levels:
    for i in range(len(y) - 1):
        for j in range(len(x) - 1):
            # Get 4 corners of cell
            z00, z10, z01, z11 = Z[i, j], Z[i + 1, j], Z[i, j + 1], Z[i + 1, j + 1]
            x0, x1, y0, y1 = x[j], x[j + 1], y[i], y[i + 1]

            # Calculate which corners are above/below level (binary case)
            case = int(z00 >= level) | (int(z10 >= level) << 1) | (int(z01 >= level) << 2) | (int(z11 >= level) << 3)

            if case == 0 or case == 15:
                continue

            # Find edge crossings via linear interpolation
            edges = []
            if (case & 1) != (case >> 1) & 1:  # Bottom edge (z00 to z10)
                t = (level - z00) / (z10 - z00) if z10 != z00 else 0.5
                edges.append((x0, y0 + t * (y1 - y0)))
            if (case >> 1) & 1 != (case >> 3) & 1:  # Right edge (z10 to z11)
                t = (level - z10) / (z11 - z10) if z11 != z10 else 0.5
                edges.append((x0 + t * (x1 - x0), y1))
            if (case >> 2) & 1 != (case >> 3) & 1:  # Top edge (z01 to z11)
                t = (level - z01) / (z11 - z01) if z11 != z01 else 0.5
                edges.append((x1, y0 + t * (y1 - y0)))
            if (case & 1) != (case >> 2) & 1:  # Left edge (z00 to z01)
                t = (level - z00) / (z01 - z00) if z01 != z00 else 0.5
                edges.append((x0 + t * (x1 - x0), y0))

            # Connect edge crossings as line segments
            if len(edges) >= 2:
                segments.append(
                    {"x1": edges[0][0], "y1": edges[0][1], "x2": edges[1][0], "y2": edges[1][1], "level": level}
                )
                if len(edges) == 4:  # Saddle point case
                    segments.append(
                        {"x1": edges[2][0], "y1": edges[2][1], "x2": edges[3][0], "y2": edges[3][1], "level": level}
                    )

df_lines = pd.DataFrame(segments)

# Filled contour background using rect marks
filled = (
    alt.Chart(df_fill)
    .mark_rect()
    .encode(
        x=alt.X("x:Q", bin=alt.Bin(maxbins=80), title="X Value"),
        y=alt.Y("y:Q", bin=alt.Bin(maxbins=80), title="Y Value"),
        color=alt.Color(
            "mean(z):Q",
            scale=alt.Scale(scheme="viridis"),
            title="Z Value",
            legend=alt.Legend(titleFontSize=20, labelFontSize=18, gradientLength=500, gradientThickness=30),
        ),
    )
)

# Contour lines overlaid with contrasting white color for visibility
lines = (
    alt.Chart(df_lines)
    .mark_rule(strokeWidth=3, opacity=1.0, color="white")
    .encode(x="x1:Q", y="y1:Q", x2="x2:Q", y2="y2:Q")
)

# Combine filled regions and contour lines (lines layered on top)
chart = (
    (filled + lines)
    .properties(width=1420, height=785, title="contour-basic · altair · pyplots.ai")
    .configure_title(fontSize=32, anchor="middle")
    .configure_axis(labelFontSize=20, titleFontSize=24, tickSize=10)
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3.0 for 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML
chart.save("plot.html")
