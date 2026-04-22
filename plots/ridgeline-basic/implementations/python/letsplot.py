""" pyplots.ai
ridgeline-basic: Basic Ridgeline Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Monthly temperature distributions (realistic weather data)
np.random.seed(42)

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Temperature parameters (mean, std) for each month - Northern hemisphere pattern
temp_params = {
    "January": (2, 5),
    "February": (4, 5),
    "March": (8, 5),
    "April": (13, 4),
    "May": (17, 4),
    "June": (21, 3),
    "July": (24, 3),
    "August": (23, 3),
    "September": (19, 4),
    "October": (14, 4),
    "November": (8, 5),
    "December": (4, 5),
}

# Generate temperature observations for each month
data = []
for month in months:
    mean, std = temp_params[month]
    temps = np.random.normal(mean, std, 150)
    for t in temps:
        data.append({"Month": month, "Temperature": t})

df = pd.DataFrame(data)

# Convert month to categorical with correct order (reversed for ridgeline bottom-to-top)
df["Month"] = pd.Categorical(df["Month"], categories=months[::-1], ordered=True)

# Create ridgeline plot
plot = (
    ggplot(df, aes(x="Temperature", y="Month", fill="Month"))  # noqa: F405
    + geom_area_ridges(  # noqa: F405
        scale=1.2,  # Overlap amount (>1 means overlap)
        alpha=0.8,
        size=1.0,  # Border thickness
        color="white",  # Border color
    )
    + scale_fill_brewer(palette="Spectral")  # noqa: F405
    + labs(  # noqa: F405
        x="Temperature (°C)", y="", title="Monthly Temperature Distribution · ridgeline-basic · letsplot · pyplots.ai"
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text_x=element_text(size=16),  # noqa: F405
        axis_text_y=element_text(size=16),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        legend_position="none",  # Y-axis labels are sufficient
        panel_grid_major_y=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x for 4800x2700) and HTML
export_ggsave(plot, "plot.png", path=".", scale=3)
export_ggsave(plot, "plot.html", path=".")
