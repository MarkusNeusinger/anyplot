""" pyplots.ai
bar-horizontal: Horizontal Bar Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-25
"""

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Programming language popularity survey results (sorted by value)
data = pd.DataFrame(
    {
        "language": ["JavaScript", "Python", "Java", "TypeScript", "C#", "C++", "PHP", "C", "Go", "Rust"],
        "developers": [65.36, 49.28, 35.35, 34.83, 29.81, 22.55, 20.87, 19.34, 13.24, 11.76],
    }
)

# Sort by value for better comparison (largest to smallest, displayed bottom to top)
data = data.sort_values("developers", ascending=True)
data["language"] = pd.Categorical(data["language"], categories=data["language"].tolist(), ordered=True)

# Create horizontal bar chart
plot = (
    ggplot(data, aes(x="language", y="developers"))
    + geom_bar(stat="identity", fill="#306998", width=0.7, alpha=0.9)
    + coord_flip()
    + labs(x="Programming Language", y="Developers (%)", title="bar-horizontal · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        panel_grid_major_x=element_line(color="#cccccc", size=0.5),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
