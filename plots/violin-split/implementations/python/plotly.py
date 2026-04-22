""" pyplots.ai
violin-split: Split Violin Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Employee performance scores before and after training program
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Operations"]
n_per_group = 80

data = []
for dept in departments:
    # Before training - varying baseline distributions by department
    if dept == "Engineering":
        before = np.random.normal(65, 12, n_per_group)
    elif dept == "Marketing":
        before = np.random.normal(58, 15, n_per_group)
    elif dept == "Sales":
        before = np.random.normal(62, 18, n_per_group)
    else:  # Operations
        before = np.random.normal(55, 10, n_per_group)

    # After training - improved scores with tighter distributions
    if dept == "Engineering":
        after = np.random.normal(78, 10, n_per_group)
    elif dept == "Marketing":
        after = np.random.normal(72, 12, n_per_group)
    elif dept == "Sales":
        after = np.random.normal(75, 14, n_per_group)
    else:  # Operations
        after = np.random.normal(68, 9, n_per_group)

    # Clamp scores to valid 0-100 range
    before = np.clip(before, 0, 100)
    after = np.clip(after, 0, 100)

    for val in before:
        data.append({"Department": dept, "Score": val, "Period": "Before Training"})
    for val in after:
        data.append({"Department": dept, "Score": val, "Period": "After Training"})

df = pd.DataFrame(data)

# Create split violin plot
fig = go.Figure()

# Python Blue and Yellow for the two groups
colors = {"Before Training": "#306998", "After Training": "#FFD43B"}

for period in ["Before Training", "After Training"]:
    subset = df[df["Period"] == period]
    side = "negative" if period == "Before Training" else "positive"

    fig.add_trace(
        go.Violin(
            x=subset["Department"],
            y=subset["Score"],
            name=period,
            side=side,
            line_color=colors[period],
            fillcolor=colors[period],
            opacity=0.7,
            meanline_visible=True,
            meanline_color="#333333",
            points=False,
            scalemode="width",
            width=0.9,
        )
    )

# Layout for 4800x2700 px
fig.update_layout(
    title=dict(text="violin-split · plotly · pyplots.ai", font=dict(size=32, color="#333333"), x=0.5, xanchor="center"),
    xaxis=dict(title=dict(text="Department", font=dict(size=24)), tickfont=dict(size=20)),
    yaxis=dict(
        title=dict(text="Performance Score (0-100 points)", font=dict(size=24)),
        tickfont=dict(size=20),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        range=[0, 100],
    ),
    template="plotly_white",
    legend=dict(
        title=dict(text="Period", font=dict(size=20)),
        font=dict(size=18),
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5,
    ),
    violingap=0.1,
    violinmode="overlay",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=100, r=60, t=120, b=80),
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
