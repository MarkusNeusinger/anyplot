""" pyplots.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-16
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data Matrix encoding - simulate a 14x14 Data Matrix pattern
# Real Data Matrix follows ISO/IEC 16022 with ECC 200 error correction
np.random.seed(42)

size = 14  # Matrix size (excluding quiet zone)
content = "PYPLOTS2024"

# Create the Data Matrix pattern
matrix = np.zeros((size, size), dtype=int)

# L-shaped finder pattern: solid black on left column and bottom row
matrix[:, 0] = 1  # Left column (solid black)
matrix[-1, :] = 1  # Bottom row (solid black)

# Alternating (clock) pattern: top row and right column
# Top row: alternating starting with black
matrix[0, :] = [1 if i % 2 == 0 else 0 for i in range(size)]
# Right column: alternating starting with black
matrix[:, -1] = [1 if i % 2 == 0 else 0 for i in range(size)]

# Data region: encode content as pseudo-random pattern (simulating real encoding)
# Real Data Matrix uses Reed-Solomon error correction (ECC 200)
data_hash = sum(ord(c) for c in content)
np.random.seed(data_hash)
for i in range(1, size - 1):
    for j in range(1, size - 1):
        matrix[i, j] = np.random.randint(0, 2)

# Add quiet zone (1 module white border)
quiet_zone = 1
full_size = size + 2 * quiet_zone
full_matrix = np.zeros((full_size, full_size), dtype=int)
full_matrix[quiet_zone : quiet_zone + size, quiet_zone : quiet_zone + size] = matrix

# Convert matrix to DataFrame for lets-plot
rows = []
for i in range(full_size):
    for j in range(full_size):
        rows.append({"x": j, "y": full_size - 1 - i, "value": full_matrix[i, j]})
df = pd.DataFrame(rows)

# Create the Data Matrix visualization
plot = (
    ggplot(df, aes(x="x", y="y", fill="value"))  # noqa: F405
    + geom_tile(color="white", size=0.1)  # noqa: F405
    + scale_fill_manual(values=["#FFFFFF", "#000000"])  # noqa: F405
    + coord_fixed()  # noqa: F405
    + labs(title="datamatrix-basic · letsplot · pyplots.ai")  # noqa: F405
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=28, face="bold", hjust=0.5),  # noqa: F405
        legend_position="none",
        plot_background=element_rect(fill="#FFFFFF"),  # noqa: F405
        panel_background=element_rect(fill="#FFFFFF"),  # noqa: F405
    )
    + ggsize(1200, 1200)  # noqa: F405
)

# Save PNG (scale 3x for high resolution: 3600x3600 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive viewing
export_ggsave(plot, filename="plot.html", path=".")
