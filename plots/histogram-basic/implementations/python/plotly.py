""" pyplots.ai
histogram-basic: Basic Histogram
Library: plotly 6.5.2 | Python 3.14.0
Quality: 94/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - simulating exam score distribution with realistic patterns
np.random.seed(42)
scores_main = np.random.normal(loc=72, scale=10, size=180)
scores_high = np.random.normal(loc=88, scale=5, size=40)
scores_low = np.random.normal(loc=45, scale=4, size=15)
values = np.concatenate([scores_main, scores_high, scores_low])
values = np.clip(values, 0, 100)

mean_val = np.mean(values)
median_val = np.median(values)

# Create histogram
fig = go.Figure()
fig.add_trace(
    go.Histogram(
        x=values,
        nbinsx=20,
        marker={"color": "rgba(48, 105, 152, 0.85)", "line": {"color": "rgba(255,255,255,0.6)", "width": 1}},
        hovertemplate="Score: %{x:.0f}<br>Count: %{y}<extra></extra>",
    )
)

# Median vertical line (dashed red)
fig.add_shape(
    type="line",
    x0=median_val,
    x1=median_val,
    y0=0,
    y1=0.88,
    yref="paper",
    line={"color": "#c44e52", "width": 2.5, "dash": "dash"},
)

# Mean vertical line (dotted green)
fig.add_shape(
    type="line",
    x0=mean_val,
    x1=mean_val,
    y0=0,
    y1=0.88,
    yref="paper",
    line={"color": "#4c8c2b", "width": 2.5, "dash": "dot"},
)

# Combined mean/median annotation positioned to the left of the lines
fig.add_annotation(
    x=0.02,
    y=0.97,
    xref="paper",
    yref="paper",
    text=(
        f'<span style="color:#c44e52">▬ ▬</span> Median: {median_val:.1f}'
        f'<br><span style="color:#4c8c2b">·····</span> Mean: {mean_val:.1f}'
    ),
    showarrow=False,
    font={"size": 15},
    align="left",
    bgcolor="rgba(255,255,255,0.9)",
    bordercolor="rgba(0,0,0,0.15)",
    borderwidth=1,
    borderpad=6,
)

# Storytelling annotations for distribution clusters
fig.add_annotation(
    x=72,
    y=44,
    text="Main cluster<br><i>77% of students</i>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowcolor="#306998",
    ax=-90,
    ay=-55,
    font={"size": 15, "color": "#1a3a5c"},
    bgcolor="rgba(255,255,255,0.9)",
    bordercolor="#306998",
    borderwidth=1,
    borderpad=5,
)

fig.add_annotation(
    x=88,
    y=26,
    text="High achievers<br><i>17% of students</i>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowcolor="#306998",
    ax=60,
    ay=-50,
    font={"size": 15, "color": "#1a3a5c"},
    bgcolor="rgba(255,255,255,0.9)",
    bordercolor="#306998",
    borderwidth=1,
    borderpad=5,
)

fig.add_annotation(
    x=45,
    y=6,
    text="Struggling<br><i>6% of students</i>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowcolor="#306998",
    ax=-60,
    ay=-55,
    font={"size": 15, "color": "#1a3a5c"},
    bgcolor="rgba(255,255,255,0.9)",
    bordercolor="#306998",
    borderwidth=1,
    borderpad=5,
)

# Refined layout for 4800x2700 px
fig.update_layout(
    title={
        "text": "histogram-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1a1a2e"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Score (points)", "font": {"size": 22, "color": "#333"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linecolor": "#ccc",
        "linewidth": 1,
        "range": [30, 105],
    },
    yaxis={
        "title": {"text": "Frequency (count)", "font": {"size": 22, "color": "#333"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.07)",
        "gridwidth": 1,
        "griddash": "dot",
        "zeroline": False,
        "showline": False,
        "rangemode": "tozero",
    },
    template="plotly_white",
    bargap=0,
    plot_bgcolor="rgba(248,249,252,1)",
    paper_bgcolor="white",
    margin={"l": 75, "r": 30, "t": 65, "b": 65},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
