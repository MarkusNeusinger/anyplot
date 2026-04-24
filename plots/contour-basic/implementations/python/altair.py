""" anyplot.ai
contour-basic: Basic Contour Plot
Library: altair 6.1.0 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-24
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — simulated topographic elevation map of a 10km x 10km mountain region
x = np.linspace(0, 10, 80)
y = np.linspace(0, 10, 80)
X, Y = np.meshgrid(x, y)

elevation = (
    850 * np.exp(-((X - 7) ** 2 + (Y - 7) ** 2) / 4.0)
    + 550 * np.exp(-((X - 2.5) ** 2 + (Y - 3) ** 2) / 3.0)
    - 180 * np.exp(-((X - 5) ** 2 + (Y - 5) ** 2) / 8.0)
    + 12 * X
    + 350
)

df_fill = pd.DataFrame({"x": X.ravel(), "y": Y.ravel(), "elevation": elevation.ravel()})

# Contour line segments via marching squares
levels = np.arange(400, 1251, 100)
segments = []

for level in levels:
    for i in range(len(y) - 1):
        for j in range(len(x) - 1):
            z00, z10, z01, z11 = elevation[i, j], elevation[i + 1, j], elevation[i, j + 1], elevation[i + 1, j + 1]
            x0, x1, y0, y1 = x[j], x[j + 1], y[i], y[i + 1]

            case = int(z00 >= level) | (int(z10 >= level) << 1) | (int(z01 >= level) << 2) | (int(z11 >= level) << 3)

            if case == 0 or case == 15:
                continue

            edges = []
            if (case & 1) != (case >> 1) & 1:
                t = (level - z00) / (z10 - z00) if z10 != z00 else 0.5
                edges.append((x0, y0 + t * (y1 - y0)))
            if (case >> 1) & 1 != (case >> 3) & 1:
                t = (level - z10) / (z11 - z10) if z11 != z10 else 0.5
                edges.append((x0 + t * (x1 - x0), y1))
            if (case >> 2) & 1 != (case >> 3) & 1:
                t = (level - z01) / (z11 - z01) if z11 != z01 else 0.5
                edges.append((x1, y0 + t * (y1 - y0)))
            if (case & 1) != (case >> 2) & 1:
                t = (level - z00) / (z01 - z00) if z01 != z00 else 0.5
                edges.append((x0 + t * (x1 - x0), y0))

            if len(edges) >= 2:
                segments.append(
                    {"x1": edges[0][0], "y1": edges[0][1], "x2": edges[1][0], "y2": edges[1][1], "level": float(level)}
                )
                if len(edges) == 4:
                    segments.append(
                        {
                            "x1": edges[2][0],
                            "y1": edges[2][1],
                            "x2": edges[3][0],
                            "y2": edges[3][1],
                            "level": float(level),
                        }
                    )

df_lines = pd.DataFrame(segments)

# Plot — filled contour background
filled = (
    alt.Chart(df_fill)
    .mark_rect()
    .encode(
        x=alt.X("x:Q", bin=alt.Bin(maxbins=80), title="Distance East (km)"),
        y=alt.Y("y:Q", bin=alt.Bin(maxbins=80), title="Distance North (km)"),
        color=alt.Color(
            "mean(elevation):Q",
            scale=alt.Scale(scheme="viridis"),
            title="Elevation (m)",
            legend=alt.Legend(titleFontSize=22, labelFontSize=18, gradientLength=600, gradientThickness=28),
        ),
    )
)

# Thin contour lines (all levels)
lines = (
    alt.Chart(df_lines)
    .mark_rule(strokeWidth=1.2, opacity=0.35, color="white")
    .encode(x="x1:Q", y="y1:Q", x2="x2:Q", y2="y2:Q")
)

# Emphasised contour lines every 200 m
major_mask = (df_lines["level"] % 200 == 0) if not df_lines.empty else pd.Series([], dtype=bool)
df_major = df_lines[major_mask].copy() if not df_lines.empty else df_lines

major_lines = (
    alt.Chart(df_major)
    .mark_rule(strokeWidth=2.2, opacity=0.95, color="white")
    .encode(x="x1:Q", y="y1:Q", x2="x2:Q", y2="y2:Q")
)

chart = (
    (filled + lines + major_lines)
    .properties(
        width=1420,
        height=785,
        title=alt.Title(
            "Mountain Terrain · contour-basic · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK
        ),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
        tickSize=8,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
