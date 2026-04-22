""" pyplots.ai
contour-density: Density Contour Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_text, geom_density_2d, geom_point, ggplot, labs, theme, theme_minimal


# Data - create bivariate distribution with clusters
np.random.seed(42)

# Main cluster
n1 = 300
x1 = np.random.normal(50, 8, n1)
y1 = np.random.normal(45, 10, n1)

# Secondary cluster
n2 = 200
x2 = np.random.normal(75, 6, n2)
y2 = np.random.normal(70, 7, n2)

# Smaller outlying cluster
n3 = 100
x3 = np.random.normal(30, 5, n3)
y3 = np.random.normal(75, 5, n3)

# Combine all data
x = np.concatenate([x1, x2, x3])
y = np.concatenate([y1, y2, y3])

df = pd.DataFrame({"measurement_a": x, "measurement_b": y})

# Plot
plot = (
    ggplot(df, aes(x="measurement_a", y="measurement_b"))
    + geom_point(alpha=0.2, size=2, color="#306998")
    + geom_density_2d(color="#FFD43B", size=1.2)
    + labs(x="Measurement A", y="Measurement B", title="contour-density · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.3, alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
