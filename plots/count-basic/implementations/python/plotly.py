""" pyplots.ai
count-basic: Basic Count Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import plotly.graph_objects as go


# Data - Survey responses with varying frequencies
np.random.seed(42)
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
# Generate raw survey data with realistic distribution
raw_data = np.random.choice(categories, size=200, p=[0.25, 0.35, 0.20, 0.12, 0.08])

# Count occurrences
unique, counts = np.unique(raw_data, return_counts=True)
# Sort by frequency (descending)
sort_idx = np.argsort(counts)[::-1]
sorted_categories = unique[sort_idx]
sorted_counts = counts[sort_idx]

# Create figure
fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=sorted_categories,
        y=sorted_counts,
        marker=dict(color="#306998", line=dict(color="#1e4d6b", width=2)),
        text=sorted_counts,
        textposition="outside",
        textfont=dict(size=20),
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    title=dict(text="count-basic · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(title=dict(text="Survey Response", font=dict(size=24)), tickfont=dict(size=18)),
    yaxis=dict(
        title=dict(text="Count", font=dict(size=24)), tickfont=dict(size=18), gridcolor="rgba(0,0,0,0.1)", gridwidth=1
    ),
    template="plotly_white",
    bargap=0.3,
    margin=dict(t=120, b=100, l=100, r=60),
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
