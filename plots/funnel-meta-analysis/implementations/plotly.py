""" pyplots.ai
funnel-meta-analysis: Meta-Analysis Funnel Plot for Publication Bias
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-15
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

# Study weights (inverse-variance) for marker sizing
weights = 1.0 / std_error**2
pooled_effect = np.sum(weights * log_or) / np.sum(weights)

# Normalize weights for marker sizes (larger weight = bigger marker)
w_norm = weights / weights.max()
marker_sizes = 18 + w_norm * 22  # Range 18-40px

# Classify studies: inside vs outside funnel for color coding
outside_funnel = np.abs(log_or - pooled_effect) > 1.96 * std_error
marker_colors = np.where(outside_funnel, "#c0392b", "#306998")
marker_borders = np.where(outside_funnel, "#922b21", "#1a3d5c")

# Funnel confidence limits
se_max = max(std_error) * 1.1
se_range = np.linspace(0, se_max, 200)
upper_limit = pooled_effect + 1.96 * se_range
lower_limit = pooled_effect - 1.96 * se_range

# Plot
fig = go.Figure()

# Outer shading: 99% CI region for depth
upper_99 = pooled_effect + 2.576 * se_range
lower_99 = pooled_effect - 2.576 * se_range
fig.add_trace(
    go.Scatter(
        x=np.concatenate([lower_99, upper_99[::-1]]),
        y=np.concatenate([se_range, se_range[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.04)",
        line={"color": "rgba(48, 105, 152, 0.12)", "width": 1, "dash": "dot"},
        showlegend=False,
        hoverinfo="skip",
        name="99% CI",
    )
)

# Pseudo 95% confidence region (filled funnel)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([lower_limit, upper_limit[::-1]]),
        y=np.concatenate([se_range, se_range[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.08)",
        line={"color": "rgba(48, 105, 152, 0.35)", "width": 1.5},
        showlegend=False,
        hoverinfo="skip",
        name="95% CI",
    )
)

# Vertical line at pooled effect
fig.add_trace(
    go.Scatter(
        x=[pooled_effect, pooled_effect],
        y=[0, se_max],
        mode="lines",
        line={"color": "#306998", "width": 3},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Vertical dashed line at null effect (0 for log scale)
fig.add_trace(
    go.Scatter(
        x=[0, 0],
        y=[0, se_max],
        mode="lines",
        line={"color": "#999999", "width": 2, "dash": "dash"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Study points with weight-proportional sizing and inside/outside coloring
fig.add_trace(
    go.Scatter(
        x=log_or,
        y=std_error,
        mode="markers",
        marker={
            "size": marker_sizes,
            "color": marker_colors,
            "line": {"color": marker_borders, "width": 1.5},
            "opacity": 0.88,
        },
        text=[
            f"<b>{s}</b><br>Log OR: {e:.2f}<br>SE: {se:.2f}<br>Weight: {w:.1f}%"
            for s, e, se, w in zip(studies, log_or, std_error, 100 * weights / weights.sum(), strict=False)
        ],
        hovertemplate="%{text}<extra></extra>",
        hoverlabel={"bgcolor": "white", "bordercolor": "#306998", "font": {"size": 14, "family": "Arial"}},
        showlegend=False,
        name="Studies",
    )
)

# Style
fig.update_layout(
    title={
        "text": "funnel-meta-analysis · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2c3e50", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Log Odds Ratio", "font": {"size": 22, "color": "#34495e"}, "standoff": 15},
        "tickfont": {"size": 18, "color": "#555"},
        "zeroline": False,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#bbb",
        "linewidth": 1,
        "range": [-1.15, 0.55],
    },
    yaxis={
        "title": {"text": "Standard Error", "font": {"size": 22, "color": "#34495e"}, "standoff": 10},
        "tickfont": {"size": 18, "color": "#555"},
        "autorange": "reversed",
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.04)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#bbb",
        "linewidth": 1,
        "rangemode": "tozero",
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="#fafbfc",
    margin={"l": 100, "r": 130, "t": 90, "b": 100},
    showlegend=False,
)

# Direction annotations - paper-relative x to avoid clipping
fig.add_annotation(
    x=0.12,
    xref="paper",
    y=se_max * 0.92,
    text="<b>← Favors Treatment</b>",
    showarrow=False,
    font={"size": 16, "color": "#306998", "family": "Arial"},
    xanchor="left",
)

fig.add_annotation(
    x=0.88,
    xref="paper",
    y=se_max * 0.92,
    text="<b>Favors Control →</b>",
    showarrow=False,
    font={"size": 16, "color": "#888888", "family": "Arial"},
    xanchor="right",
)

# Pooled effect label (at top of chart where SE is small = top visually)
fig.add_annotation(
    x=pooled_effect + 0.02,
    y=0.02,
    text=f"<b>Pooled ({pooled_effect:.2f})</b>",
    showarrow=False,
    font={"size": 16, "color": "#306998"},
    xanchor="left",
    yanchor="top",
)

# Null effect label
fig.add_annotation(
    x=0.02,
    y=0.02,
    text="<b>Null (0)</b>",
    showarrow=False,
    font={"size": 16, "color": "#888888"},
    xanchor="left",
    yanchor="top",
)

# Subtitle annotation for asymmetry insight
fig.add_annotation(
    x=0.5,
    xref="paper",
    y=1.0,
    yref="paper",
    text="Asymmetry at lower precision suggests possible publication bias  •  Red markers fall outside 95% CI",
    showarrow=False,
    font={"size": 14, "color": "#7f8c8d", "family": "Arial"},
    xanchor="center",
    yanchor="bottom",
)

# Funnel region labels
fig.add_annotation(
    x=pooled_effect + 1.96 * se_max * 0.55,
    y=se_max * 0.55,
    text="95% CI",
    showarrow=False,
    font={"size": 14, "color": "rgba(48, 105, 152, 0.6)"},
    textangle=-28,
)

fig.add_annotation(
    x=pooled_effect + 2.576 * se_max * 0.55,
    y=se_max * 0.55,
    text="99% CI",
    showarrow=False,
    font={"size": 13, "color": "rgba(48, 105, 152, 0.45)"},
    textangle=-35,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
