""" pyplots.ai
bar-diverging: Diverging Bar Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Customer satisfaction survey (Net Promoter Score style)
categories = [
    "Product Quality",
    "Customer Service",
    "Pricing",
    "Delivery Speed",
    "Website Usability",
    "Return Policy",
    "Product Selection",
    "Payment Options",
    "Mobile App",
    "Packaging",
    "Technical Support",
    "Loyalty Program",
]

# Scores range from -100 (all detractors) to +100 (all promoters)
scores = [72, 45, -28, 38, -12, 55, 21, 65, -35, 48, -8, 32]

df = pd.DataFrame(
    {"Category": categories, "Score": scores, "Sentiment": ["Positive" if s >= 0 else "Negative" for s in scores]}
)

# Sort by score for better pattern recognition
df = df.sort_values("Score", ascending=True).reset_index(drop=True)

# Preserve category order after sorting
df["Category"] = pd.Categorical(df["Category"], categories=df["Category"].tolist(), ordered=True)

# Create horizontal diverging bar chart
plot = (
    ggplot(df, aes(x="Score", y="Category", fill="Sentiment"))  # noqa: F405
    + geom_bar(stat="identity", width=0.7, alpha=0.9)  # noqa: F405
    + geom_vline(xintercept=0, color="#333333", size=1.2)  # noqa: F405
    + scale_fill_manual(values=["#DC2626", "#306998"])  # noqa: F405
    + labs(  # noqa: F405
        x="Net Promoter Score", y="Category", title="bar-diverging · letsplot · pyplots.ai"
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=28, face="bold", hjust=0.5),  # noqa: F405
        axis_title_x=element_text(size=22),  # noqa: F405
        axis_title_y=element_text(size=22),  # noqa: F405
        axis_text_x=element_text(size=18),  # noqa: F405
        axis_text_y=element_text(size=18),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_position="right",
        panel_grid_major_y=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
