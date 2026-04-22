""" pyplots.ai
box-horizontal: Horizontal Box Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, coord_flip, element_text, geom_boxplot, ggplot, labs, scale_fill_manual, theme, theme_minimal


# Data - Response times (ms) by service type
np.random.seed(42)

services = [
    "Authentication Service",
    "Database Query Handler",
    "File Storage API",
    "Email Notification",
    "Payment Gateway",
]

data = []
for service in services:
    if service == "Authentication Service":
        values = np.random.normal(120, 25, 80)
    elif service == "Database Query Handler":
        values = np.random.normal(85, 40, 80)
        values = np.append(values, [220, 250, 280])  # Add outliers
    elif service == "File Storage API":
        values = np.random.normal(200, 50, 80)
    elif service == "Email Notification":
        values = np.random.normal(150, 30, 80)
    else:  # Payment Gateway
        values = np.random.normal(180, 60, 80)
        values = np.append(values, [350, 380])  # Add outliers

    for v in values:
        data.append({"Service": service, "Response Time": max(10, v)})

df = pd.DataFrame(data)

# Sort by median response time for easier comparison
medians = df.groupby("Service")["Response Time"].median().sort_values()
df["Service"] = pd.Categorical(df["Service"], categories=medians.index, ordered=True)

# Colors - Python palette
colors = ["#306998", "#FFD43B", "#4B8BBE", "#646464", "#FFE873"]

# Create horizontal box plot using coord_flip()
plot = (
    ggplot(df, aes(x="Service", y="Response Time", fill="Service"))
    + geom_boxplot(alpha=0.8, size=0.8, outlier_size=3, outlier_alpha=0.7)
    + coord_flip()
    + scale_fill_manual(values=colors)
    + labs(title="box-horizontal · plotnine · pyplots.ai", x="", y="Response Time (ms)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, face="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_position="none",
        panel_grid_major_y=element_text(color="#cccccc"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
