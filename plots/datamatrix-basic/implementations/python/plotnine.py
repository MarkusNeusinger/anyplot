""" pyplots.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-16
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_blank, element_rect, element_text, geom_tile, ggplot, labs, scale_fill_manual, theme


# Data - Create a Data Matrix barcode pattern
# Data Matrix uses an L-shaped finder pattern and alternating clock pattern
np.random.seed(42)

# Data Matrix dimensions (10x10 is smallest standard size)
size = 16  # Using 16x16 for better visibility

# Initialize matrix (0 = white, 1 = black)
dm_matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern: solid black on left edge and bottom edge
# Left edge (solid black column)
dm_matrix[:, 0] = 1

# Bottom edge (solid black row)
dm_matrix[size - 1, :] = 1

# Alternating clock pattern on top and right edges
# Top edge (alternating, starting with black)
for i in range(size):
    dm_matrix[0, i] = i % 2

# Right edge (alternating, starting with black at bottom)
for i in range(size):
    dm_matrix[i, size - 1] = (size - 1 - i) % 2

# Data encoding area - fill with deterministic pattern representing encoded content
# This simulates encoded data "SERIAL:12345678" as mentioned in the spec
content = "SERIAL:12345678"
data_values = [ord(c) for c in content]

# Fill the interior data area with a pattern
# The data area is inside the finder/clock patterns (rows 1 to size-2, cols 1 to size-2)
data_idx = 0
for row in range(1, size - 1):
    for col in range(1, size - 1):
        # Create a deterministic pattern based on content
        val = data_values[data_idx % len(data_values)]
        # Use bit manipulation for a barcode-like pattern
        bit_pos = (row + col) % 8
        dm_matrix[row, col] = (val >> bit_pos) & 1
        data_idx += 1

# Add quiet zone (white border) for scanning reliability
quiet_zone = 2
padded_size = size + 2 * quiet_zone
dm_with_border = np.zeros((padded_size, padded_size), dtype=int)
dm_with_border[quiet_zone : quiet_zone + size, quiet_zone : quiet_zone + size] = dm_matrix

# Convert matrix to DataFrame for plotnine
data = []
for row in range(padded_size):
    for col in range(padded_size):
        # Flip y-axis so origin is at bottom-left (standard barcode orientation)
        data.append({"x": col, "y": padded_size - 1 - row, "value": str(dm_with_border[row, col])})

df = pd.DataFrame(data)

# Create Data Matrix visualization using geom_tile
plot = (
    ggplot(df, aes(x="x", y="y", fill="value"))
    + geom_tile(color=None, size=0)
    + scale_fill_manual(values={"0": "#FFFFFF", "1": "#000000"})
    + labs(title="datamatrix-basic \u00b7 plotnine \u00b7 pyplots.ai")
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", color="#306998", weight="bold"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#FFFFFF"),
        plot_background=element_rect(fill="#FFFFFF"),
        legend_position="none",
    )
)

# Save as PNG (square format for barcode)
plot.save("plot.png", dpi=300, verbose=False)
