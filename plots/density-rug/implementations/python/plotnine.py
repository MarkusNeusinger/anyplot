""" pyplots.ai
density-rug: Density Plot with Rug Marks
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_density, geom_rug, ggplot, labs, theme, theme_minimal


# Data - Response times for a web API (realistic scenario)
np.random.seed(42)
# Mix of fast responses and some slower outliers (bimodal-ish distribution)
fast_responses = np.random.normal(loc=120, scale=25, size=180)  # Most responses around 120ms
slow_responses = np.random.normal(loc=280, scale=40, size=70)  # Some slower responses
response_times = np.concatenate([fast_responses, slow_responses])
response_times = response_times[response_times > 0]  # Ensure positive values

df = pd.DataFrame({"response_time": response_times})

# Create plot
plot = (
    ggplot(df, aes(x="response_time"))
    + geom_density(fill="#306998", alpha=0.5, color="#306998", size=1.5)
    + geom_rug(alpha=0.4, sides="b", size=1.2, color="#306998")
    + labs(x="Response Time (ms)", y="Density", title="density-rug · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(alpha=0.3),
        panel_grid_minor=element_line(alpha=0.15),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
