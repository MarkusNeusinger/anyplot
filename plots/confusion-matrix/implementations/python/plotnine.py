""" pyplots.ai
confusion-matrix: Confusion Matrix Heatmap
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


# Data - realistic multi-class classification results
np.random.seed(42)

# Class names for a sentiment analysis classifier
class_names = ["Negative", "Neutral", "Positive"]
n_classes = len(class_names)

# Create a realistic confusion matrix with:
# - Good diagonal (correct predictions)
# - Some confusion between adjacent sentiment classes
confusion_data = np.array(
    [
        [85, 12, 3],  # Negative: mostly correct, some confused with Neutral
        [8, 72, 20],  # Neutral: harder to classify, confused with both
        [4, 15, 81],  # Positive: mostly correct, some confused with Neutral
    ]
)

# Convert to long format for plotnine
rows = []
for i, true_class in enumerate(class_names):
    for j, pred_class in enumerate(class_names):
        rows.append({"True Label": true_class, "Predicted Label": pred_class, "Count": confusion_data[i, j]})

df = pd.DataFrame(rows)

# Set categorical order (reverse for y-axis to have first class at top)
df["True Label"] = pd.Categorical(df["True Label"], categories=class_names[::-1], ordered=True)
df["Predicted Label"] = pd.Categorical(df["Predicted Label"], categories=class_names, ordered=True)

# Add text color based on count (dark text on light cells, white text on dark cells)
threshold = (confusion_data.max() + confusion_data.min()) / 2
df["text_color"] = df["Count"].apply(lambda x: "white" if x >= threshold else "#08519c")

# Create the confusion matrix heatmap
plot = (
    ggplot(df, aes(x="Predicted Label", y="True Label", fill="Count"))
    + geom_tile(color="white", size=2)
    + geom_text(aes(label="Count", color="text_color"), size=20, fontweight="bold", show_legend=False)
    + scale_fill_gradient(low="#c6dbef", high="#08519c", name="Count")
    + scale_color_identity()
    + labs(title="confusion-matrix · plotnine · pyplots.ai", x="Predicted Label", y="True Label")
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        text=element_text(size=14),
        axis_title=element_text(size=22, weight="bold"),
        axis_text=element_text(size=18),
        plot_title=element_text(size=26, weight="bold", ha="center"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, verbose=False)
