""" pyplots.ai
rug-basic: Basic Rug Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_blank, element_text, geom_rug, ggplot, labs, theme, theme_minimal


# Data - simulated response times with realistic clustering and gaps
np.random.seed(42)
cluster1 = np.random.normal(150, 20, 40)  # Fast responses around 150ms
cluster2 = np.random.normal(280, 35, 30)  # Medium responses around 280ms
cluster3 = np.random.normal(450, 50, 20)  # Slow responses around 450ms
outliers = np.array([620, 680, 750, 820])  # A few slow outliers

values = np.concatenate([cluster1, cluster2, cluster3, outliers])
df = pd.DataFrame({"response_time": values})

# Plot - rug plot showing response time distribution
plot = (
    ggplot(df, aes(x="response_time"))
    + geom_rug(alpha=0.7, sides="b", size=1.5, color="#306998")
    + labs(x="Response Time (ms)", y="", title="rug-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title_x=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        plot_title=element_text(size=24),
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
