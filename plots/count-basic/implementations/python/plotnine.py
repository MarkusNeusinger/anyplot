""" pyplots.ai
count-basic: Basic Count Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-25
"""

import pandas as pd
from plotnine import aes, element_text, geom_bar, geom_text, ggplot, labs, scale_fill_manual, theme, theme_minimal


# Data - Survey responses from a product feedback form
categories = ["Excellent"] * 45 + ["Good"] * 78 + ["Average"] * 52 + ["Poor"] * 23 + ["Very Poor"] * 12
df = pd.DataFrame({"Response": categories})

# Create ordered category for logical sorting (not alphabetical)
response_order = ["Excellent", "Good", "Average", "Poor", "Very Poor"]
df["Response"] = pd.Categorical(df["Response"], categories=response_order, ordered=True)

# Count data for labels
counts = df["Response"].value_counts().reindex(response_order)
count_df = pd.DataFrame({"Response": response_order, "Count": counts.values})
count_df["Response"] = pd.Categorical(count_df["Response"], categories=response_order, ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="Response", fill="Response"))
    + geom_bar(width=0.7, show_legend=False)
    + geom_text(aes(x="Response", y="Count", label="Count"), data=count_df, size=14, va="bottom", nudge_y=2)
    + scale_fill_manual(values=["#306998", "#4A82A6", "#6E9DB5", "#93B8C4", "#FFD43B"])
    + labs(x="Customer Response", y="Number of Responses", title="count-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
    )
)

# Save
plot.save("plot.png", dpi=300)
