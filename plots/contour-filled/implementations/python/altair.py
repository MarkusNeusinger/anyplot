"""anyplot.ai
contour-filled: Filled Contour Plot
Library: altair | Python 3.13
Quality: pending | Created: 2025-05-11
"""

import os
import sys

# Remove script directory from sys.path to avoid importing local altair.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - 2D Gaussian peaks for filled contour visualization
np.random.seed(42)
n_points = 80
x = np.linspace(-3, 3, n_points)
y = np.linspace(-3, 3, n_points)
X, Y = np.meshgrid(x, y)

# Create surface with multiple peaks and valleys
Z = (
    1.5 * np.exp(-((X - 1) ** 2 + (Y - 1) ** 2) / 0.8)
    + 1.2 * np.exp(-((X + 1) ** 2 + (Y + 0.5) ** 2) / 1.0)
    - 0.6 * np.exp(-((X) ** 2 + (Y - 1.5) ** 2) / 0.6)
    + 0.2 * np.sin(X * 2) * np.cos(Y * 2)
)

# Create contour levels
n_levels = 12
z_min, z_max = Z.min(), Z.max()
levels = np.linspace(z_min, z_max, n_levels + 1)

# Bin z-values and map to level centers for color mapping
Z_binned = np.digitize(Z, levels) - 1
Z_binned = np.clip(Z_binned, 0, n_levels - 1)
level_centers = (levels[:-1] + levels[1:]) / 2
Z_discrete = level_centers[Z_binned]

# Create rectangle grid for filled contours
step = x[1] - x[0]
half_step = step / 2

df = pd.DataFrame(
    {
        "x": X.ravel() - half_step,
        "x2": X.ravel() + half_step,
        "y": Y.ravel() - half_step,
        "y2": Y.ravel() + half_step,
        "z": Z_discrete.ravel(),
    }
)

# Filled contour using mark_rect
filled_contour = (
    alt.Chart(df)
    .mark_rect(stroke="none")
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
            legend=alt.Legend(
                titleFontSize=20,
                labelFontSize=16,
                gradientLength=400,
                gradientThickness=25,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
            ),
        ),
    )
)


# Create contour line overlay
def find_contours(Z, level, x_coords, y_coords):
    """Extract contour lines using marching squares algorithm."""
    rows, cols = Z.shape
    segments = []

    for i in range(rows - 1):
        for j in range(cols - 1):
            z00, z01, z10, z11 = Z[i, j], Z[i, j + 1], Z[i + 1, j], Z[i + 1, j + 1]
            cell = [z00, z01, z10, z11]
            case = sum([1 << k for k, v in enumerate(cell) if v >= level])

            if case in (0, 15):
                continue

            x0, x1 = x_coords[j], x_coords[j + 1]
            y0, y1 = y_coords[i], y_coords[i + 1]

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


contour_lines_data = []
contour_levels_subset = levels[2:-2:2]

for idx, level_val in enumerate(contour_levels_subset):
    segments = find_contours(Z, level_val, x, y)
    for seg_idx, (p1, p2) in enumerate(segments):
        contour_id = f"L{idx}_S{seg_idx}"
        contour_lines_data.append({"x": p1[0], "y": p1[1], "order": 0, "contour_id": contour_id})
        contour_lines_data.append({"x": p2[0], "y": p2[1], "order": 1, "contour_id": contour_id})

contour_df = pd.DataFrame(contour_lines_data)

# Contour line overlay with theme-adaptive color
contour_color = "#2A2A25" if THEME == "light" else "#D5D4CC"
contour_overlay = (
    alt.Chart(contour_df)
    .mark_line(strokeWidth=1.2, opacity=0.4)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-3.1, 3.1])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-3.1, 3.1])),
        order="order:O",
        detail="contour_id:N",
        color=alt.value(contour_color),
    )
)

# Combine layers with theme-adaptive styling
chart = (
    alt.layer(filled_contour, contour_overlay)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(text="contour-filled · altair · anyplot.ai", fontSize=28, anchor="middle"),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .configure_title(color=INK)
)

# Save PNG and HTML with theme suffix
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
