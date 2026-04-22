""" pyplots.ai
donut-basic: Basic Donut Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Budget allocation by department
categories = ["Marketing", "Operations", "R&D", "Sales", "HR"]
values = [28, 22, 25, 18, 7]

df = pd.DataFrame({"category": categories, "value": values})

# Calculate percentages for labels
total = sum(values)
df["pct"] = df["value"] / total * 100

# Preserve category order
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Define colors - Python Blue first, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#4CAF50", "#FF7043", "#AB47BC"]

# Create center label dataframe
center_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": [f"Total\n${total}M"]})

# Plot - donut chart with larger size to fill more canvas space
plot = (
    ggplot(df)  # noqa: F405
    + geom_pie(  # noqa: F405
        aes(slice="value", fill="category"),  # noqa: F405
        stat="identity",
        size=40,  # Increased from 20 to make donut larger
        hole=0.5,  # Creates donut hole (50% of radius)
        labels=layer_labels()  # noqa: F405
        .line("@pct")
        .format("pct", "{.1f}%")
        .size(18),  # Larger labels for visibility
    )
    # Center annotation showing total budget
    + geom_label(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=center_df,
        size=20,  # Increased for larger center
        fill="white",
        alpha=0.9,
        label_padding=0.6,
        label_r=0.2,
    )
    + scale_fill_manual(values=colors)  # noqa: F405
    + labs(  # noqa: F405
        title="donut-basic · letsplot · pyplots.ai", fill="Department"
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=28, hjust=0.5),  # noqa: F405
        legend_title=element_text(size=20),  # noqa: F405
        legend_text=element_text(size=18),  # noqa: F405
        legend_position=[0.85, 0.5],  # noqa: F405  # Position legend to give more space to chart
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
