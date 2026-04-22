""" pyplots.ai
confusion-matrix: Confusion Matrix Heatmap
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


# Data: Multi-class classification results (4 classes - sentiment analysis)
np.random.seed(42)
class_names = ["Negative", "Neutral", "Positive", "Very Positive"]
n_classes = len(class_names)

# Create a realistic confusion matrix with good diagonal but some misclassifications
# Simulating a sentiment classifier that sometimes confuses adjacent classes
confusion_matrix = np.array(
    [
        [85, 12, 2, 1],  # Negative: mostly correct, some confused with Neutral
        [8, 72, 15, 5],  # Neutral: confused with both adjacent classes
        [3, 18, 78, 11],  # Positive: some confusion with Neutral and Very Positive
        [1, 3, 14, 82],  # Very Positive: mostly correct, some confused with Positive
    ]
)

# Create heatmap
fig = go.Figure(
    data=go.Heatmap(
        z=confusion_matrix,
        x=class_names,
        y=class_names,
        colorscale="Blues",
        showscale=True,
        colorbar=dict(title=dict(text="Count", font=dict(size=20)), tickfont=dict(size=16), thickness=25, len=0.8),
        hovertemplate="True: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
    )
)

# Add text annotations for each cell
annotations = []
for i in range(n_classes):
    for j in range(n_classes):
        value = confusion_matrix[i, j]
        # Use white text on dark backgrounds (high values), black on light
        text_color = "white" if value > 50 else "black"
        annotations.append(
            dict(
                x=class_names[j],
                y=class_names[i],
                text=str(value),
                font=dict(size=24, color=text_color),
                showarrow=False,
            )
        )

# Update layout
fig.update_layout(
    title=dict(text="confusion-matrix · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Predicted Label", font=dict(size=22)), tickfont=dict(size=18), side="bottom", tickangle=0
    ),
    yaxis=dict(
        title=dict(text="True Label", font=dict(size=22)),
        tickfont=dict(size=18),
        autorange="reversed",  # Put first class at top
    ),
    annotations=annotations,
    template="plotly_white",
    margin=dict(l=120, r=100, t=100, b=100),
)

# Make cells square
fig.update_xaxes(scaleanchor="y", scaleratio=1)

# Save outputs
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
