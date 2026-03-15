""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: plotly 6.6.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-15
"""

import numpy as np
import plotly.graph_objects as go


# Data: Meta-analysis of 15 RCTs comparing drug vs placebo (log odds ratios)
np.random.seed(42)

studies = [
    "Adams et al. 2016",
    "Baker et al. 2017",
    "Chen et al. 2017",
    "Davis & Park 2018",
    "Evans et al. 2018",
    "Fischer 2019",
    "Gupta et al. 2019",
    "Harris et al. 2020",
    "Ibrahim et al. 2020",
    "Jensen & Liu 2021",
    "Kim et al. 2021",
    "Lambert et al. 2022",
    "Morales et al. 2022",
    "Nielsen 2023",
    "Olsen et al. 2023",
]

# Log odds ratios and standard errors
log_or = np.array(
    [-0.52, -0.38, -0.71, -0.15, -0.45, -0.63, -0.29, -0.55, -0.42, -0.33, -0.80, -0.48, -0.36, -0.61, -0.10]
)
std_error = np.array([0.18, 0.25, 0.12, 0.30, 0.20, 0.15, 0.28, 0.17, 0.22, 0.26, 0.11, 0.19, 0.24, 0.14, 0.35])

# Pooled (summary) effect size via inverse-variance weighting
weights = 1.0 / std_error**2
pooled_effect = np.sum(weights * log_or) / np.sum(weights)

# Funnel confidence limits
se_range = np.linspace(0, max(std_error) * 1.15, 200)
upper_limit = pooled_effect + 1.96 * se_range
lower_limit = pooled_effect - 1.96 * se_range

# Plot
fig = go.Figure()

# Pseudo 95% confidence region (filled funnel)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([lower_limit, upper_limit[::-1]]),
        y=np.concatenate([se_range, se_range[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.08)",
        line={"color": "rgba(48, 105, 152, 0.3)", "width": 1.5},
        showlegend=False,
        hoverinfo="skip",
        name="95% CI",
    )
)

# Vertical line at pooled effect
fig.add_vline(x=pooled_effect, line={"color": "#306998", "width": 2.5})

# Vertical dashed line at null effect (0 for log scale)
fig.add_vline(x=0, line={"color": "#888888", "width": 1.5, "dash": "dash"})

# Study points
fig.add_trace(
    go.Scatter(
        x=log_or,
        y=std_error,
        mode="markers",
        marker={"size": 14, "color": "#306998", "line": {"color": "white", "width": 1.5}, "opacity": 0.85},
        text=[f"{s}<br>Log OR: {e:.2f}<br>SE: {se:.2f}" for s, e, se in zip(studies, log_or, std_error, strict=False)],
        hovertemplate="%{text}<extra></extra>",
        showlegend=False,
        name="Studies",
    )
)

# Style
fig.update_layout(
    title={"text": "funnel-meta-analysis · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Log Odds Ratio", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "zeroline": False,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": "Standard Error", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "autorange": "reversed",
        "showgrid": False,
        "rangemode": "tozero",
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 100, "r": 60, "t": 80, "b": 80},
    showlegend=False,
)

# Annotations for direction
fig.add_annotation(
    x=-0.9,
    y=max(std_error) * 1.1,
    text="← Favors Treatment",
    showarrow=False,
    font={"size": 16, "color": "#306998"},
    xanchor="center",
)

fig.add_annotation(
    x=0.1,
    y=max(std_error) * 1.1,
    text="Favors Control →",
    showarrow=False,
    font={"size": 16, "color": "#888888"},
    xanchor="center",
)

fig.add_annotation(
    x=pooled_effect + 0.03,
    y=0.005,
    text=f"Pooled ({pooled_effect:.2f})",
    showarrow=False,
    font={"size": 15, "color": "#306998"},
    xanchor="left",
    yanchor="bottom",
)

fig.add_annotation(
    x=0.03,
    y=0.005,
    text="Null (0)",
    showarrow=False,
    font={"size": 15, "color": "#888888"},
    xanchor="left",
    yanchor="bottom",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
