""" pyplots.ai
point-basic: Point Estimate Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - Research study results with confidence intervals
np.random.seed(42)
categories = ["Treatment A", "Treatment B", "Treatment C", "Control", "Placebo"]
estimates = [4.2, 5.8, 3.1, 2.5, 1.8]
# Generate realistic confidence intervals (narrower for larger effects)
ci_width = [0.9, 1.1, 0.7, 0.8, 0.6]
lower = [e - w for e, w in zip(estimates, ci_width)]
upper = [e + w for e, w in zip(estimates, ci_width)]

df = pd.DataFrame({"group": categories, "estimate": estimates, "lower": lower, "upper": upper})

# Plot - Horizontal point estimate plot with confidence intervals
plot = (
    ggplot(df, aes(x="group", y="estimate", ymin="lower", ymax="upper"))
    + geom_pointrange(color="#306998", size=1.5, linewidth=1.5)
    + geom_hline(yintercept=0, linetype="dashed", color="#666666", size=0.8, alpha=0.7)
    + labs(y="Effect Size (95% CI)", x="Treatment Group", title="point-basic · lets-plot · pyplots.ai")
    + coord_flip()
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML
ggsave(plot, "plot.html", path=".")
