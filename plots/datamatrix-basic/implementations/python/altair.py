""" pyplots.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate Data Matrix pattern (ECC 200 format)
# Data Matrix uses an L-shaped finder pattern and alternating timing pattern
np.random.seed(42)

# Use 16x16 matrix (common size for moderate data)
size = 16
quiet_zone = 2  # Minimum 1 module, we use 2 for clarity
total_size = size + 2 * quiet_zone

# Initialize matrix with white (0)
matrix = np.zeros((total_size, total_size), dtype=int)

# Add L-shaped finder pattern (solid black on left and bottom edges)
# Left edge - solid black column
for row in range(size):
    matrix[quiet_zone + row, quiet_zone] = 1

# Bottom edge - solid black row
for col in range(size):
    matrix[quiet_zone + size - 1, quiet_zone + col] = 1

# Add alternating (clock) timing pattern on top and right edges
# Top edge - alternating pattern starting with black
for col in range(size):
    matrix[quiet_zone, quiet_zone + col] = col % 2

# Right edge - alternating pattern starting with black
for row in range(size):
    matrix[quiet_zone + row, quiet_zone + size - 1] = row % 2

# Fill data area with deterministic pattern representing "SERIAL:12345678"
content = "SERIAL:12345678"
hash_val = hash(content)

# Data area is inside the finder/timing patterns (rows 1 to size-2, cols 1 to size-2)
for row in range(1, size - 1):
    for col in range(1, size - 1):
        # Create deterministic pattern from position and content hash
        idx = row * size + col
        matrix[quiet_zone + row, quiet_zone + col] = ((hash_val >> (idx % 32)) ^ (idx * 13)) % 2

# Convert matrix to DataFrame for Altair
data = []
for row in range(total_size):
    for col in range(total_size):
        # Flip y-axis so bottom-left origin matches Data Matrix convention
        data.append({"x": col, "y": total_size - 1 - row, "value": matrix[row, col]})
df = pd.DataFrame(data)

# Create Data Matrix visualization using mark_rect
chart = (
    alt.Chart(df)
    .mark_rect(stroke=None)
    .encode(
        x=alt.X("x:O", axis=None),
        y=alt.Y("y:O", axis=None),
        color=alt.Color("value:N", scale=alt.Scale(domain=[0, 1], range=["#FFFFFF", "#000000"]), legend=None),
    )
    .properties(
        width=800,
        height=800,
        title=alt.Title("datamatrix-basic · altair · pyplots.ai", fontSize=28, anchor="middle", dy=-10),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
)

# Save as PNG (square format: 3600 x 3600 px with scale_factor)
chart.save("plot.png", scale_factor=4.5)

# Save interactive HTML version
chart.save("plot.html")
