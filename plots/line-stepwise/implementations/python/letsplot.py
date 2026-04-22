""" pyplots.ai
line-stepwise: Step Line Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401


LetsPlot.setup_html()

# Data - Server Response Time Monitor (discrete state changes)
np.random.seed(42)
hours = np.arange(0, 24)

# Response time that changes in steps (server performance states)
base_response = 50
response_times = [base_response]

for i in range(1, 24):
    # Random step changes at certain hours
    if i in [6, 9, 12, 15, 18, 21]:
        change = np.random.choice([-20, -10, 10, 20, 30])
        new_val = max(20, min(150, response_times[-1] + change))
        response_times.append(new_val)
    else:
        response_times.append(response_times[-1])

response_times = np.array(response_times)

df = pd.DataFrame({"hour": hours, "response_time": response_times})

# Plot
plot = (
    ggplot(df, aes(x="hour", y="response_time"))
    + geom_step(color="#306998", size=2, direction="hv")
    + geom_point(color="#FFD43B", size=5, shape=21, fill="#FFD43B", stroke=1.5)
    + labs(x="Hour of Day", y="Response Time (ms)", title="line-stepwise · letsplot · pyplots.ai")
    + scale_x_continuous(breaks=list(range(0, 25, 3)))
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 x 2700 px)
ggsave(plot, "plot.png", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html")
