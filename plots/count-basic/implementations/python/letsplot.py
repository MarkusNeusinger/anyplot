""" pyplots.ai
count-basic: Basic Count Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 97/100 | Created: 2025-12-25
"""
# ruff: noqa: F405

import os
import shutil

import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Data - Survey responses with varying frequencies
responses = ["Excellent"] * 45 + ["Good"] * 78 + ["Average"] * 52 + ["Poor"] * 23 + ["Very Poor"] * 12

df = pd.DataFrame({"Response": responses})

# Create ordered category for proper sorting
response_order = ["Excellent", "Good", "Average", "Poor", "Very Poor"]
df["Response"] = pd.Categorical(df["Response"], categories=response_order, ordered=True)

# Create count plot
plot = (
    ggplot(df, aes(x="Response"))
    + geom_bar(fill="#306998", alpha=0.85, width=0.7)
    + geom_text(aes(label="..count.."), stat="count", size=14, vjust=-0.5, color="#333333")
    + labs(x="Customer Satisfaction Rating", y="Number of Responses", title="count-basic · letsplot · pyplots.ai")
    + scale_y_continuous(expand=[0, 0, 0.12, 0], limits=[0, 90])
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html")

# Move files from lets-plot-images to current directory
if os.path.exists("lets-plot-images/plot.png"):
    shutil.move("lets-plot-images/plot.png", "plot.png")
if os.path.exists("lets-plot-images/plot.html"):
    shutil.move("lets-plot-images/plot.html", "plot.html")
if os.path.exists("lets-plot-images") and not os.listdir("lets-plot-images"):
    os.rmdir("lets-plot-images")
