""" pyplots.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: plotly 6.5.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

conditions = ["Control", "Low Dose", "Medium Dose", "High Dose"]
n_per_group = 50

data = []
for condition in conditions:
    if condition == "Control":
        values = np.random.normal(450, 80, n_per_group)
    elif condition == "Low Dose":
        values = np.random.normal(400, 90, n_per_group)
    elif condition == "Medium Dose":
        values = np.random.normal(350, 70, n_per_group)
    else:  # High Dose
        values = np.random.normal(320, 60, n_per_group)
    for v in values:
        data.append({"condition": condition, "reaction_time": v})

df = pd.DataFrame(data)

# Create figure
fig = go.Figure()

# Colors - Python Blue for violin, Yellow for points
violin_color = "rgba(48, 105, 152, 0.4)"  # Python Blue with transparency
point_color = "#FFD43B"  # Python Yellow

# Add violin plots for each condition
for i, condition in enumerate(conditions):
    condition_data = df[df["condition"] == condition]["reaction_time"]

    # Add violin
    fig.add_trace(
        go.Violin(
            x0=i,
            y=condition_data,
            name=condition,
            box_visible=False,
            meanline_visible=True,
            fillcolor=violin_color,
            line_color="#306998",
            line_width=2,
            opacity=0.7,
            showlegend=False,
            width=0.7,
            points=False,  # We'll add our own points
        )
    )

# Add swarm points - jitter horizontally within violin boundaries
np.random.seed(123)  # Different seed for jitter
for i, condition in enumerate(conditions):
    condition_data = df[df["condition"] == condition]["reaction_time"].values

    # Create jittered x positions (swarm-like effect within violin width)
    jitter = np.random.uniform(-0.12, 0.12, len(condition_data))
    x_positions = [i + j for j in jitter]

    fig.add_trace(
        go.Scatter(
            x=x_positions,
            y=condition_data,
            mode="markers",
            marker=dict(size=11, color=point_color, line=dict(width=1.5, color="#306998"), opacity=0.9),
            name=condition,
            showlegend=False,
        )
    )

# Update layout
fig.update_layout(
    title=dict(text="violin-swarm · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Experimental Condition", font=dict(size=24)),
        tickfont=dict(size=20),
        tickvals=list(range(len(conditions))),
        ticktext=conditions,
    ),
    yaxis=dict(
        title=dict(text="Reaction Time (ms)", font=dict(size=24)),
        tickfont=dict(size=20),
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    showlegend=False,
    margin=dict(l=100, r=60, t=100, b=100),
    plot_bgcolor="white",
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
