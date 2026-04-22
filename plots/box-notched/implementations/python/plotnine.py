""" pyplots.ai
box-notched: Notched Box Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_boxplot, ggplot, labs, scale_fill_manual, theme, theme_minimal


# Data - employee productivity scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support", "HR"]
n_per_dept = [120, 85, 100, 75, 50]

data = []
# Engineering: high median, moderate spread
data.extend([{"department": "Engineering", "score": v} for v in np.random.normal(78, 10, n_per_dept[0])])
# Marketing: medium-high median, wider spread
data.extend([{"department": "Marketing", "score": v} for v in np.random.normal(72, 14, n_per_dept[1])])
# Sales: bimodal-ish, with outliers
sales_scores = np.concatenate([np.random.normal(65, 8, 70), np.random.normal(85, 5, 30)])
data.extend([{"department": "Sales", "score": v} for v in sales_scores])
# Support: lower median, tight distribution
data.extend([{"department": "Support", "score": v} for v in np.random.normal(62, 7, n_per_dept[3])])
# HR: medium median, some low outliers
hr_scores = np.concatenate([np.random.normal(70, 9, 45), np.random.normal(45, 3, 5)])
data.extend([{"department": "HR", "score": v} for v in hr_scores])

df = pd.DataFrame(data)
df["department"] = pd.Categorical(df["department"], categories=departments, ordered=True)

# Colors - Python Blue primary, complementary palette
colors = ["#306998", "#FFD43B", "#4A90A4", "#8B5A8C", "#6B8E6B"]

# Plot
plot = (
    ggplot(df, aes(x="department", y="score", fill="department"))
    + geom_boxplot(notch=True, notchwidth=0.5, outlier_size=3, outlier_alpha=0.7, size=0.8)
    + scale_fill_manual(values=colors)
    + labs(x="Department", y="Productivity Score (points)", title="box-notched · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
