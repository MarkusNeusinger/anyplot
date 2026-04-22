""" pyplots.ai
confusion-matrix: Confusion Matrix Heatmap
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_identity,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Multi-class classification results for image classifier
np.random.seed(42)

class_names = ["Cat", "Dog", "Bird", "Fish"]
n_classes = len(class_names)

# Create a realistic confusion matrix with strong diagonal
# and some realistic misclassification patterns
confusion_data = np.array(
    [
        [45, 8, 3, 2],  # Cat: sometimes confused with Dog
        [6, 52, 4, 1],  # Dog: sometimes confused with Cat
        [2, 3, 38, 5],  # Bird: sometimes confused with Fish
        [1, 2, 7, 41],  # Fish: sometimes confused with Bird
    ]
)

# Build long-form data for geom_tile
rows = []
for i, true_label in enumerate(class_names):
    for j, pred_label in enumerate(class_names):
        count = confusion_data[i, j]
        rows.append(
            {"True Label": true_label, "Predicted Label": pred_label, "Count": count, "true_idx": i, "pred_idx": j}
        )

df = pd.DataFrame(rows)

# Calculate percentages for annotation (row normalization = recall)
total_per_row = confusion_data.sum(axis=1, keepdims=True)
percentages = (confusion_data / total_per_row * 100).astype(int)
df["Percentage"] = [percentages[r["true_idx"], r["pred_idx"]] for _, r in df.iterrows()]
df["Label"] = df.apply(lambda r: f"{r['Count']}\n({r['Percentage']}%)", axis=1)

# Set category order for proper matrix layout
df["True Label"] = pd.Categorical(df["True Label"], categories=class_names[::-1], ordered=True)
df["Predicted Label"] = pd.Categorical(df["Predicted Label"], categories=class_names, ordered=True)

# Determine text color based on count (white for dark cells, black for light)
max_count = df["Count"].max()
df["text_color"] = df["Count"].apply(lambda c: "white" if c > max_count * 0.4 else "black")

# Create confusion matrix heatmap
plot = (
    ggplot(df, aes(x="Predicted Label", y="True Label", fill="Count"))
    + geom_tile(color="white", size=1.5, tooltips="none")
    + geom_text(
        aes(label="Label", color="text_color"),
        size=14,
        fontface="bold",
        tooltips={"lines": ["True: @{True Label}", "Pred: @{Predicted Label}", "Count: @Count"]},
    )
    + scale_color_identity()
    + scale_fill_gradient(low="#c6dbef", high="#306998", name="Count")
    + labs(x="Predicted Label", y="True Label", title="confusion-matrix · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        panel_grid=element_blank(),
    )
    + ggsize(1200, 1200)
    + coord_fixed()
)

# Save as PNG (scale 3x for 3600x3600 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML
ggsave(plot, "plot.html", path=".")
