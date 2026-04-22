""" pyplots.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import plotly.graph_objects as go


# Data - Blood pressure measurements from two sphygmomanometers
np.random.seed(42)
n_subjects = 80

# Method 1: Reference sphygmomanometer (systolic BP in mmHg)
method1 = np.random.normal(125, 15, n_subjects)

# Method 2: New device with small systematic bias and random error
bias = 2.5  # Small positive bias (new device reads slightly higher)
method2 = method1 + bias + np.random.normal(0, 5, n_subjects)

# Calculate Bland-Altman statistics
means = (method1 + method2) / 2
differences = method1 - method2

mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Create figure
fig = go.Figure()

# Scatter plot of differences vs means
fig.add_trace(
    go.Scatter(
        x=means,
        y=differences,
        mode="markers",
        marker={"size": 14, "color": "#306998", "opacity": 0.7, "line": {"width": 1, "color": "white"}},
        name="Observations",
        hovertemplate="Mean: %{x:.1f} mmHg<br>Difference: %{y:.1f} mmHg<extra></extra>",
    )
)

# Mean difference line (bias)
fig.add_hline(
    y=mean_diff,
    line={"color": "#306998", "width": 3},
    annotation_text=f"Mean: {mean_diff:.2f}",
    annotation_position="right",
    annotation_font={"size": 18, "color": "#306998"},
)

# Upper limit of agreement
fig.add_hline(
    y=upper_loa,
    line={"color": "#FFD43B", "width": 2.5, "dash": "dash"},
    annotation_text=f"+1.96 SD: {upper_loa:.2f}",
    annotation_position="right",
    annotation_font={"size": 18, "color": "#B8860B"},
)

# Lower limit of agreement
fig.add_hline(
    y=lower_loa,
    line={"color": "#FFD43B", "width": 2.5, "dash": "dash"},
    annotation_text=f"−1.96 SD: {lower_loa:.2f}",
    annotation_position="right",
    annotation_font={"size": 18, "color": "#B8860B"},
)

# Layout
fig.update_layout(
    title={"text": "bland-altman-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Mean of Two Methods (mmHg)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.1)",
        "showgrid": True,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Difference (Method 1 − Method 2) (mmHg)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.1)",
        "showgrid": True,
        "zeroline": False,
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 100, "r": 180, "t": 100, "b": 100},
    plot_bgcolor="white",
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
