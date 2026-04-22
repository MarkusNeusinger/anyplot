""" pyplots.ai
venn-basic: Venn Diagram
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


np.random.seed(42)

LetsPlot.setup_html()

# Data: Three research fields with overlapping expertise
set_a_label = "Machine Learning"
set_b_label = "Statistics"
set_c_label = "Data Engineering"

# Set sizes and intersections
only_a = 45  # Only ML
only_b = 35  # Only Statistics
only_c = 30  # Only Data Engineering
ab_only = 25  # ML & Statistics (not DE)
ac_only = 15  # ML & DE (not Stats)
bc_only = 20  # Stats & DE (not ML)
abc = 10  # All three

# Circle parameters (for 3-set Venn diagram) - larger for better canvas utilization
r = 1.8  # radius (increased from 1.5)
cx_a, cy_a = -0.85, 0.6  # Center of set A (top left)
cx_b, cy_b = 0.85, 0.6  # Center of set B (top right)
cx_c, cy_c = 0.0, -0.75  # Center of set C (bottom)

# Generate circle points
theta = np.linspace(0, 2 * np.pi, 100)

# Create circle data
circle_a_x = cx_a + r * np.cos(theta)
circle_a_y = cy_a + r * np.sin(theta)
circle_b_x = cx_b + r * np.cos(theta)
circle_b_y = cy_b + r * np.sin(theta)
circle_c_x = cx_c + r * np.cos(theta)
circle_c_y = cy_c + r * np.sin(theta)

# Create DataFrames for circles
df_a = pd.DataFrame({"x": circle_a_x, "y": circle_a_y, "set": set_a_label})
df_b = pd.DataFrame({"x": circle_b_x, "y": circle_b_y, "set": set_b_label})
df_c = pd.DataFrame({"x": circle_c_x, "y": circle_c_y, "set": set_c_label})
df_circles = pd.concat([df_a, df_b, df_c], ignore_index=True)

# Label positions and values (adjusted for larger circles and better spacing)
labels_data = pd.DataFrame(
    {
        "x": [
            cx_a - 0.6,  # Only A (left side of A)
            cx_b + 0.6,  # Only B (right side of B)
            cx_c,  # Only C (bottom of C) - moved further down
            (cx_a + cx_b) / 2,  # A & B intersection
            (cx_a + cx_c) / 2 - 0.35,  # A & C intersection
            (cx_b + cx_c) / 2 + 0.35,  # B & C intersection
            0.0,  # Center (A & B & C)
        ],
        "y": [
            cy_a + 0.4,  # Only A
            cy_b + 0.4,  # Only B
            cy_c - 0.75,  # Only C - moved much further down to avoid center overlap
            cy_a + 0.75,  # A & B intersection
            (cy_a + cy_c) / 2 - 0.4,  # A & C intersection
            (cy_b + cy_c) / 2 - 0.4,  # B & C intersection
            0.0,  # Center (A & B & C)
        ],
        "label": [str(only_a), str(only_b), str(only_c), str(ab_only), str(ac_only), str(bc_only), str(abc)],
    }
)

# Set name labels (outside circles) - adjusted for larger circles
set_labels_data = pd.DataFrame(
    {
        "x": [cx_a - 0.9, cx_b + 0.9, cx_c],
        "y": [cy_a + 1.5, cy_b + 1.5, cy_c - 1.6],
        "label": [set_a_label, set_b_label, set_c_label],
    }
)

# Colors
colors = {"Machine Learning": "#306998", "Statistics": "#FFD43B", "Data Engineering": "#DC2626"}

# Create plot
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill="set"), data=df_circles, alpha=0.35, color="white", size=2.5)
    + geom_text(aes(x="x", y="y", label="label"), data=labels_data, size=20, fontface="bold", color="#1a1a1a")
    + geom_text(aes(x="x", y="y", label="label"), data=set_labels_data, size=18, fontface="bold", color="#222222")
    + scale_fill_manual(values=colors)
    + coord_fixed(ratio=1)
    + labs(title="venn-basic · lets-plot · pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=28, face="bold", hjust=0.5), legend_position="none", plot_margin=[50, 30, 30, 30]
    )
    + ggsize(1200, 1200)
)

# Save as PNG and HTML
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")

# Move files from lets-plot-images subdirectory to current directory
if os.path.exists("lets-plot-images/plot.png"):
    os.rename("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    os.rename("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images") and not os.listdir("lets-plot-images"):
    os.rmdir("lets-plot-images")
