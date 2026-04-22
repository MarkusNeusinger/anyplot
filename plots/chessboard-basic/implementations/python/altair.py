""" pyplots.ai
chessboard-basic: Chess Board Grid Visualization
Library: altair 6.0.0 | Python 3.13.11
Quality: 95/100 | Created: 2026-01-08
"""

import altair as alt
import pandas as pd


# Data - Create 8x8 chess board
columns = list("abcdefgh")
rows = list(range(1, 9))

# Generate all 64 squares with color assignments
# Light squares at h1 and a8 corners (standard chess convention)
data = []
for col_idx, col in enumerate(columns):
    for row in rows:
        # Chess coloring: (col_idx + row) even = dark, odd = light
        is_light = (col_idx + row) % 2 == 1
        data.append({"column": col, "row": row, "color": "light" if is_light else "dark", "x": col_idx, "y": row - 1})

df = pd.DataFrame(data)

# Create chart with rect marks for squares
chart = (
    alt.Chart(df)
    .mark_rect(stroke="#5D4037", strokeWidth=1)
    .encode(
        x=alt.X(
            "column:O",
            axis=alt.Axis(title=None, labelFontSize=24, labelAngle=0, orient="bottom", labelPadding=10),
            sort=columns,
        ),
        y=alt.Y(
            "row:O", axis=alt.Axis(title=None, labelFontSize=24, labelPadding=10), sort=list(range(8, 0, -1))
        ),  # 8 at top, 1 at bottom
        color=alt.Color(
            "color:N",
            scale=alt.Scale(
                domain=["light", "dark"],
                range=["#F5DEB3", "#8B4513"],  # Wheat / Saddle Brown
            ),
            legend=None,
        ),
    )
    .properties(
        width=900,
        height=900,
        title=alt.Title("chessboard-basic · altair · pyplots.ai", fontSize=32, anchor="middle", offset=20),
    )
    .configure_view(strokeWidth=2, stroke="#3E2723")
    .configure_axis(labelColor="#333333", tickColor="#333333")
)

# Save outputs
chart.save("plot.png", scale_factor=4.0)
chart.save("plot.html")
