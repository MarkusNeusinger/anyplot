""" pyplots.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: plotly 6.5.2 | Python 3.14.3
Quality: 93/100 | Created: 2026-02-17
"""

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Data - PCA on Wine dataset
wine = load_wine()
X_scaled = StandardScaler().fit_transform(wine.data)
pca = PCA().fit(X_scaled)

explained_variance = pca.explained_variance_ratio_
cumulative_variance = np.cumsum(explained_variance) * 100
n_components = np.arange(1, len(explained_variance) + 1)

# Threshold crossings
threshold_90_idx = np.argmax(cumulative_variance >= 90)
threshold_95_idx = np.argmax(cumulative_variance >= 95)
threshold_90_comp = threshold_90_idx + 1
threshold_95_comp = threshold_95_idx + 1

# Detect elbow point: first component where marginal gain drops below average gain
individual_pct = explained_variance * 100
mean_gain = individual_pct.mean()
elbow_idx = int(np.argmax(individual_pct < mean_gain))
elbow_comp = elbow_idx + 1  # 1-based component number
elbow_var = cumulative_variance[elbow_idx]

# Plot
fig = go.Figure()

# Filled area under cumulative curve for visual depth
fig.add_trace(
    go.Scatter(
        x=n_components,
        y=cumulative_variance,
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.08)",
        line={"width": 0},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Individual variance as bars (increased opacity)
fig.add_trace(
    go.Bar(
        x=n_components,
        y=explained_variance * 100,
        marker={"color": "rgba(48, 105, 152, 0.4)", "line": {"width": 1, "color": "rgba(48, 105, 152, 0.6)"}},
        name="Individual",
        hovertemplate="PC%{x}<br>Variance: %{y:.1f}%<extra></extra>",
    )
)

# Cumulative variance line
fig.add_trace(
    go.Scatter(
        x=n_components,
        y=cumulative_variance,
        mode="lines+markers",
        line={"color": "#306998", "width": 5, "shape": "spline"},
        marker={"size": 14, "color": "#306998", "line": {"width": 2, "color": "white"}},
        name="Cumulative",
        hovertemplate="PC%{x}<br>Cumulative: %{y:.1f}%<extra></extra>",
    )
)

# 90% threshold line
fig.add_hline(
    y=90,
    line_dash="dash",
    line_color="#E8871E",
    line_width=2.5,
    annotation_text="90%",
    annotation_position="top left",
    annotation_font={"size": 22, "color": "#E8871E", "family": "Arial Black"},
)

# 95% threshold line
fig.add_hline(
    y=95,
    line_dash="dash",
    line_color="#C7402D",
    line_width=2.5,
    annotation_text="95%",
    annotation_position="top left",
    annotation_font={"size": 22, "color": "#C7402D", "family": "Arial Black"},
)

# Vertical drop lines from threshold crossings to x-axis
fig.add_shape(
    type="line",
    x0=threshold_90_comp,
    x1=threshold_90_comp,
    y0=0,
    y1=90,
    line={"color": "#E8871E", "width": 1.5, "dash": "dot"},
)
fig.add_shape(
    type="line",
    x0=threshold_95_comp,
    x1=threshold_95_comp,
    y0=0,
    y1=95,
    line={"color": "#C7402D", "width": 1.5, "dash": "dot"},
)

# Elbow point annotation with distinctive marker
fig.add_trace(
    go.Scatter(
        x=[elbow_comp],
        y=[elbow_var],
        mode="markers",
        marker={
            "size": 24,
            "color": "rgba(255, 255, 255, 0.9)",
            "line": {"width": 3.5, "color": "#D4442B"},
            "symbol": "diamond",
        },
        showlegend=False,
        hovertemplate=f"Elbow Point<br>PC{elbow_comp}<br>Cumulative: {elbow_var:.1f}%<extra></extra>",
    )
)

fig.add_annotation(
    x=elbow_comp,
    y=elbow_var,
    text=f"<b>Elbow</b> — PC{elbow_comp}<br>{elbow_var:.0f}% variance",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2,
    arrowcolor="#D4442B",
    ax=-70,
    ay=-60,
    font={"size": 22, "color": "#D4442B", "family": "Arial"},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="#D4442B",
    borderwidth=1.5,
    borderpad=6,
)

# Layout
fig.update_layout(
    title={
        "text": "line-pca-variance-cumulative · plotly · pyplots.ai",
        "font": {"size": 40, "family": "Arial Black", "color": "#1a1a2e"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Principal Component", "font": {"size": 36, "color": "#333"}},
        "tickfont": {"size": 28, "color": "#555"},
        "tickmode": "linear",
        "tick0": 1,
        "dtick": 1,
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linewidth": 2,
        "linecolor": "#ccc",
    },
    yaxis={
        "title": {"text": "Explained Variance (%)", "font": {"size": 36, "color": "#333"}},
        "tickfont": {"size": 28, "color": "#555"},
        "range": [0, 105],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.06)",
        "zeroline": False,
        "showline": True,
        "linewidth": 2,
        "linecolor": "#ccc",
    },
    template="plotly_white",
    plot_bgcolor="rgba(250,250,252,1)",
    legend={
        "font": {"size": 26},
        "x": 0.02,
        "y": 0.38,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
    },
    margin={"t": 120, "b": 100, "l": 120, "r": 100},
    bargap=0.4,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
