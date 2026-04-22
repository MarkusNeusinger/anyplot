""" pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import pandas as pd
from plotnine import aes, element_text, geom_errorbar, geom_point, ggplot, labs, theme, theme_minimal


# Data - Lab measurements with measurement uncertainty
data = pd.DataFrame(
    {
        "experiment": ["Sample A", "Sample B", "Sample C", "Sample D", "Sample E", "Sample F"],
        "measurement": [42.5, 38.2, 55.1, 47.8, 33.6, 51.3],
        "error": [3.2, 4.1, 2.8, 5.5, 3.8, 4.2],
    }
)

# Calculate error bar positions
data["ymin"] = data["measurement"] - data["error"]
data["ymax"] = data["measurement"] + data["error"]

# Plot
plot = (
    ggplot(data, aes(x="experiment", y="measurement"))
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.3, size=1.5, color="#306998")
    + geom_point(size=6, color="#306998")
    + labs(x="Experiment", y="Measurement Value", title="errorbar-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        axis_text_x=element_text(size=16),
    )
)

# Save
plot.save("plot.png", dpi=300)
