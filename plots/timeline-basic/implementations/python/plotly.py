""" pyplots.ai
timeline-basic: Event Timeline
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import pandas as pd
import plotly.graph_objects as go


# Data - Software project milestones with phases
data = {
    "date": pd.to_datetime(
        [
            "2024-01-15",
            "2024-02-20",
            "2024-03-10",
            "2024-04-05",
            "2024-05-15",
            "2024-06-01",
            "2024-07-10",
            "2024-08-20",
            "2024-09-15",
            "2024-10-30",
            "2024-11-15",
            "2024-12-10",
        ]
    ),
    "event": [
        "Project Kickoff",
        "Requirements Complete",
        "Design Review",
        "Development Start",
        "Alpha Release",
        "User Testing",
        "Beta Release",
        "Performance Optimization",
        "Security Audit",
        "Release Candidate",
        "Documentation Complete",
        "Production Launch",
    ],
    "category": [
        "Planning",
        "Planning",
        "Planning",
        "Development",
        "Development",
        "Testing",
        "Testing",
        "Development",
        "Testing",
        "Release",
        "Release",
        "Release",
    ],
}
df = pd.DataFrame(data)

# Color mapping for categories
colors = {
    "Planning": "#306998",  # Python Blue
    "Development": "#FFD43B",  # Python Yellow
    "Testing": "#4ECDC4",  # Teal
    "Release": "#E74C3C",  # Red-Orange
}

# Alternate positions (above/below axis) to prevent label overlap
positions = [1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1]
df["position"] = positions

# Create figure
fig = go.Figure()

# Add the timeline axis line
fig.add_trace(
    go.Scatter(
        x=[df["date"].min() - pd.Timedelta(days=15), df["date"].max() + pd.Timedelta(days=15)],
        y=[0, 0],
        mode="lines",
        line=dict(color="#333333", width=3),
        hoverinfo="skip",
        showlegend=False,
    )
)

# Add vertical connector lines for each event
for _, row in df.iterrows():
    fig.add_trace(
        go.Scatter(
            x=[row["date"], row["date"]],
            y=[0, row["position"] * 0.4],
            mode="lines",
            line=dict(color="#888888", width=2, dash="dot"),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Add event markers and labels by category
for category in df["category"].unique():
    cat_df = df[df["category"] == category]

    fig.add_trace(
        go.Scatter(
            x=cat_df["date"],
            y=[0] * len(cat_df),
            mode="markers",
            marker=dict(size=20, color=colors[category], line=dict(color="white", width=2)),
            name=category,
            hovertemplate="<b>%{text}</b><br>%{x|%B %d, %Y}<extra></extra>",
            text=cat_df["event"],
        )
    )

# Add event labels
for _, row in df.iterrows():
    y_offset = row["position"] * 0.5
    fig.add_annotation(
        x=row["date"],
        y=y_offset,
        text=row["event"],
        showarrow=False,
        font=dict(size=16, color="#333333"),
        xanchor="center",
        yanchor="bottom" if row["position"] > 0 else "top",
    )

# Add date labels below markers
for _, row in df.iterrows():
    fig.add_annotation(
        x=row["date"],
        y=row["position"] * 0.15,
        text=row["date"].strftime("%b %d"),
        showarrow=False,
        font=dict(size=12, color="#666666"),
        xanchor="center",
        yanchor="bottom" if row["position"] > 0 else "top",
    )

# Layout
fig.update_layout(
    title=dict(
        text="timeline-basic · plotly · pyplots.ai", font=dict(size=28, color="#333333"), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Project Timeline (2024)", font=dict(size=22)),
        tickfont=dict(size=18),
        tickformat="%B",
        dtick="M1",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        zeroline=False,
    ),
    yaxis=dict(visible=False, range=[-1, 1], fixedrange=True),
    template="plotly_white",
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=16)),
    margin=dict(l=80, r=80, t=120, b=80),
    plot_bgcolor="white",
    paper_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
