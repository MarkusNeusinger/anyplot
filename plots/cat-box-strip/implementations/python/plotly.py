""" pyplots.ai
cat-box-strip: Box Plot with Strip Overlay
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Performance scores across different training methods
np.random.seed(42)

categories = ["Method A", "Method B", "Method C", "Method D"]
n_per_group = [35, 40, 30, 45]

data = []
# Method A: Normal distribution, moderate spread
data.extend([{"Category": "Method A", "Score": v} for v in np.random.normal(72, 8, n_per_group[0])])
# Method B: Higher scores, tighter spread
data.extend([{"Category": "Method B", "Score": v} for v in np.random.normal(85, 5, n_per_group[1])])
# Method C: Lower scores with some outliers
scores_c = np.concatenate([np.random.normal(58, 10, n_per_group[2] - 3), [25, 28, 95]])
data.extend([{"Category": "Method C", "Score": v} for v in scores_c])
# Method D: Bimodal distribution
scores_d = np.concatenate(
    [np.random.normal(65, 6, n_per_group[3] // 2), np.random.normal(80, 6, n_per_group[3] - n_per_group[3] // 2)]
)
data.extend([{"Category": "Method D", "Score": v} for v in scores_d])

df = pd.DataFrame(data)

# Colors
python_blue = "#306998"
python_yellow = "#FFD43B"

# Create figure
fig = go.Figure()

# Add box plots for each category
for cat in categories:
    cat_data = df[df["Category"] == cat]["Score"]
    fig.add_trace(
        go.Box(
            y=cat_data,
            x=[cat] * len(cat_data),
            name=cat,
            marker_color=python_blue,
            fillcolor="rgba(48, 105, 152, 0.4)",
            line=dict(color=python_blue, width=2),
            boxmean=False,
            boxpoints=False,
            showlegend=False,
            width=0.5,
        )
    )

# Add strip (scatter) points for each category with jitter
np.random.seed(123)  # Separate seed for jitter
for cat in categories:
    cat_data = df[df["Category"] == cat]["Score"]
    jitter_vals = np.random.uniform(-0.15, 0.15, len(cat_data))

    fig.add_trace(
        go.Scatter(
            x=[cat] * len(cat_data),
            y=cat_data,
            mode="markers",
            name=cat,
            marker=dict(color=python_yellow, size=10, opacity=0.7, line=dict(color=python_blue, width=1)),
            showlegend=False,
            hovertemplate=f"{cat}<br>Score: %{{y:.1f}}<extra></extra>",
            customdata=jitter_vals,
        )
    )

# Apply jitter by offsetting x positions
for i, cat in enumerate(categories):
    trace_idx = len(categories) + i
    cat_data = df[df["Category"] == cat]["Score"]
    jitter_vals = fig.data[trace_idx].customdata
    # Convert category to position and add jitter
    fig.data[trace_idx].x = [i + j for j in jitter_vals]

# Update x-axis to use category positions
fig.update_layout(
    title=dict(text="cat-box-strip · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Training Method", font=dict(size=22)),
        tickfont=dict(size=18),
        tickmode="array",
        tickvals=list(range(len(categories))),
        ticktext=categories,
        range=[-0.5, len(categories) - 0.5],
    ),
    yaxis=dict(
        title=dict(text="Performance Score", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    plot_bgcolor="white",
    showlegend=False,
    margin=dict(l=80, r=50, t=100, b=80),
)

# Update box plots to use numeric positions
for i, cat in enumerate(categories):
    fig.data[i].x = [i] * len(df[df["Category"] == cat])

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
