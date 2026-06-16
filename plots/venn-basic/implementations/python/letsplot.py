""" anyplot.ai
venn-basic: Venn Diagram
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


np.random.seed(42)

LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data: Three research fields with overlapping expertise
set_a_label = "Machine Learning"
set_b_label = "Statistics"
set_c_label = "Data Engineering"

# Set sizes and intersections
only_a = 45
only_b = 35
only_c = 30
ab_only = 25
ac_only = 15
bc_only = 20
abc = 10

# Circle parameters (for 3-set Venn diagram)
r = 1.8
cx_a, cy_a = -0.85, 0.6
cx_b, cy_b = 0.85, 0.6
cx_c, cy_c = 0.0, -0.75

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

# Label positions and values
labels_data = pd.DataFrame(
    {
        "x": [cx_a - 0.6, cx_b + 0.6, cx_c, (cx_a + cx_b) / 2, (cx_a + cx_c) / 2 - 0.35, (cx_b + cx_c) / 2 + 0.35, 0.0],
        "y": [cy_a + 0.4, cy_b + 0.4, cy_c - 0.75, cy_a + 0.75, (cy_a + cy_c) / 2 - 0.4, (cy_b + cy_c) / 2 - 0.4, 0.0],
        "label": [str(only_a), str(only_b), str(only_c), str(ab_only), str(ac_only), str(bc_only), str(abc)],
    }
)

# Set name labels (outside circles)
set_labels_data = pd.DataFrame(
    {
        "x": [cx_a - 0.9, cx_b + 0.9, cx_c],
        "y": [cy_a + 1.5, cy_b + 1.5, cy_c - 1.6],
        "label": [set_a_label, set_b_label, set_c_label],
    }
)

# Map sets to Okabe-Ito palette
set_colors = {set_a_label: IMPRINT[0], set_b_label: IMPRINT[1], set_c_label: IMPRINT[2]}

# Create custom theme for chrome styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    axis_title=element_text(color=INK),
    axis_text=element_text(color=INK_SOFT),
    axis_line=element_blank(),
    plot_title=element_text(size=28, face="bold", hjust=0.5, color=INK),
    legend_position="none",
    plot_margin=[50, 30, 30, 30],
)

# Create plot
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill="set"), data=df_circles, alpha=0.35, color=INK_SOFT, size=2.5)
    + geom_text(aes(x="x", y="y", label="label"), data=labels_data, size=20, fontface="bold", color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=set_labels_data, size=18, fontface="bold", color=INK)
    + scale_fill_manual(values=set_colors)
    + coord_fixed(ratio=1)
    + labs(title="venn-basic · letsplot · anyplot.ai")
    + theme_void()
    + anyplot_theme
    + ggsize(1200, 1200)
)

# Save as PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images subdirectory if needed
if os.path.exists(f"lets-plot-images/plot-{THEME}.png"):
    os.rename(f"lets-plot-images/plot-{THEME}.png", f"plot-{THEME}.png")
if os.path.exists(f"lets-plot-images/plot-{THEME}.html"):
    os.rename(f"lets-plot-images/plot-{THEME}.html", f"plot-{THEME}.html")
if os.path.exists("lets-plot-images") and not os.listdir("lets-plot-images"):
    os.rmdir("lets-plot-images")
