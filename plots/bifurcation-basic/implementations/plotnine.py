""" pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_point,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — logistic map: x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 2000)
n_discard = 200
n_keep = 100

parameter = []
state = []

x0 = 0.5
for r in r_values:
    x = x0
    for _ in range(n_discard):
        x = r * x * (1.0 - x)
    for _ in range(n_keep):
        x = r * x * (1.0 - x)
        parameter.append(r)
        state.append(x)

df = pd.DataFrame({"parameter": parameter, "state": state})

# Plot
plot = (
    ggplot(df, aes(x="parameter", y="state"))
    + geom_point(size=0.1, alpha=0.7, color="#306998", stroke=0)
    + labs(x="Growth Rate (r)", y="Steady-State Population (x)", title="bifurcation-basic · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=np.arange(2.5, 4.1, 0.25))
    + scale_y_continuous(breaks=np.arange(0, 1.1, 0.2))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#cccccc", alpha=0.2, size=0.5),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
