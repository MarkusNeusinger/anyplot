""" pyplots.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Simulated blood pressure readings from two sphygmomanometers
np.random.seed(42)
n = 80

# True systolic BP values (realistic range: 100-160 mmHg)
true_bp = np.random.normal(125, 15, n)

# Method 1: Reference standard (small measurement error)
method1 = true_bp + np.random.normal(0, 3, n)

# Method 2: New device (slight positive bias + slightly larger error)
method2 = true_bp + np.random.normal(2, 4, n)

# Bland-Altman calculations
mean_values = (method1 + method2) / 2
diff_values = method1 - method2

mean_diff = np.mean(diff_values)
std_diff = np.std(diff_values, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Create DataFrame
df = pd.DataFrame({"mean": mean_values, "diff": diff_values})

# Annotation data - position labels at the left side with offset from line
annot_x = df["mean"].min() + 2
y_offset = 0.8  # Offset so labels don't overlap lines
annot_df = pd.DataFrame(
    {
        "x": [annot_x, annot_x, annot_x],
        "y": [mean_diff + y_offset, upper_loa + y_offset, lower_loa - y_offset],
        "label": [
            f"Mean Bias: {mean_diff:.2f} mmHg",
            f"+1.96 SD: {upper_loa:.2f} mmHg",
            f"-1.96 SD: {lower_loa:.2f} mmHg",
        ],
        "color": ["bias", "loa", "loa"],
    }
)

# Build plot
plot = (
    ggplot()
    # Scatter points
    + geom_point(aes(x="mean", y="diff"), data=df, color="#306998", size=5, alpha=0.7)
    # Mean difference line (bias)
    + geom_hline(yintercept=mean_diff, color="#16a34a", size=1.5)
    # Upper limit of agreement
    + geom_hline(yintercept=upper_loa, color="#dc2626", size=1.2, linetype="dashed")
    # Lower limit of agreement
    + geom_hline(yintercept=lower_loa, color="#dc2626", size=1.2, linetype="dashed")
    # Annotations using geom_label for better visibility
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=annot_df[annot_df["color"] == "bias"],
        size=12,
        color="#16a34a",
        fill="white",
        hjust=0,
        label_padding=0.3,
    )
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=annot_df[annot_df["color"] == "loa"],
        size=12,
        color="#dc2626",
        fill="white",
        hjust=0,
        label_padding=0.3,
    )
    # Labels and title
    + labs(
        x="Mean of Two Methods (mmHg)",
        y="Difference (Method 1 - Method 2) (mmHg)",
        title="bland-altman-basic · letsplot · pyplots.ai",
    )
    # Size and theme
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#e5e5e5", size=0.5),
        panel_grid_minor=element_blank(),
    )
)

# Save PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", scale=3, path=".")

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
