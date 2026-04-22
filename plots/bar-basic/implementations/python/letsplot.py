""" pyplots.ai
bar-basic: Basic Bar Chart
Library: letsplot 4.8.2 | Python 3.14
Quality: 90/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Quarterly revenue by department (not monotonically ordered for richer comparison)
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys & Games"]
values = [45200, 32800, 28500, 31400, 18900, 19800]

df = pd.DataFrame({"category": categories, "value": values})

# Highlight the leader bar with a darker shade; others get standard Python Blue
leader_val = max(values)
mean_val = sum(values) / len(values)
df["fill_color"] = ["#1E4F72" if v == leader_val else "#306998" for v in values]

# Build annotation text for the leader
second_val = sorted(values, reverse=True)[1]
leader_pct = (leader_val - second_val) / second_val
leader_annotation = f"+{leader_pct:.0%} vs. next"

# Annotation data — use category name for discrete x-axis positioning
ann_df = pd.DataFrame({"category": ["Electronics"], "y": [leader_val + 3500], "lbl": [leader_annotation]})

# Mean label data — position near the last category
mean_df = pd.DataFrame({"category": ["Toys & Games"], "y": [mean_val + 1000], "lbl": [f"Avg: ${mean_val:,.0f}"]})

# Plot
plot = (
    ggplot(df, aes(x="category", y="value"))  # noqa: F405
    + geom_bar(  # noqa: F405
        aes(fill="fill_color"),  # noqa: F405
        stat="identity",
        width=0.7,
        tooltips=layer_tooltips()  # noqa: F405
        .title("@category")
        .line("Revenue|$@{value}"),
        show_legend=False,
    )
    + scale_fill_identity()  # noqa: F405
    # Value labels above each bar with currency formatting
    + geom_text(  # noqa: F405
        aes(label="value"),  # noqa: F405
        position=position_nudge(y=1200),  # noqa: F405
        size=13,
        label_format="${,d}",
        color="#333333",
        fontface="bold",
    )
    # Leader insight annotation above the top bar
    + geom_text(  # noqa: F405
        aes(x="category", y="y", label="lbl"),  # noqa: F405
        data=ann_df,
        size=10,
        color="#1E4F72",
        fontface="bold italic",
        inherit_aes=False,
    )
    # Mean reference line for context
    + geom_hline(yintercept=mean_val, color="#999999", size=0.8, linetype="dashed")  # noqa: F405
    + geom_text(  # noqa: F405
        aes(x="category", y="y", label="lbl"),  # noqa: F405
        data=mean_df,
        size=10,
        color="#777777",
        fontface="italic",
        hjust=1.0,
        inherit_aes=False,
    )
    + labs(  # noqa: F405
        x="Department", y="Quarterly Revenue ($)", title="bar-basic · letsplot · pyplots.ai"
    )
    + scale_x_discrete(limits=categories)  # noqa: F405
    + scale_y_continuous(  # noqa: F405
        limits=[0, 50000], format="${,.0f}", expand=[0, 0, 0.08, 0]
    )
    + flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        axis_text_x=element_text(angle=45, hjust=1, size=16),  # noqa: F405
        axis_text_y=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24, hjust=0.5, face="bold"),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.4),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
