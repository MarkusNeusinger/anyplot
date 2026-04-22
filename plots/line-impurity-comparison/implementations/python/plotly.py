""" pyplots.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: plotly 6.5.2 | Python 3.14.3
Quality: 95/100 | Created: 2026-02-17
"""

import numpy as np
import plotly.graph_objects as go


# Data
p = np.linspace(0, 1, 200)

gini_raw = 2 * p * (1 - p)
gini = gini_raw / gini_raw.max()

entropy_raw = np.where((p == 0) | (p == 1), 0.0, -p * np.log2(p) - (1 - p) * np.log2(1 - p))
entropy = entropy_raw / entropy_raw.max()

# Plot
fig = go.Figure()

# Shaded region between curves to highlight divergence
fig.add_trace(
    go.Scatter(
        x=np.concatenate([p, p[::-1]]),
        y=np.concatenate([entropy, gini[::-1]]),
        fill="toself",
        fillcolor="rgba(48,105,152,0.10)",
        line={"width": 0},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Gini curve
fig.add_trace(
    go.Scatter(
        x=p,
        y=gini,
        mode="lines",
        name="Gini: 2p(1−p) [scaled]",
        line={"color": "#306998", "width": 3.5},
        hovertemplate="p = %{x:.2f}<br>Gini = %{y:.3f}<extra></extra>",
    )
)

# Entropy curve (orange for colorblind accessibility — avoids blue-red pairing)
fig.add_trace(
    go.Scatter(
        x=p,
        y=entropy,
        mode="lines",
        name="Entropy: −p log₂p − (1−p) log₂(1−p)",
        line={"color": "#E69F00", "width": 3.5, "dash": "dash"},
        hovertemplate="p = %{x:.2f}<br>Entropy = %{y:.3f}<extra></extra>",
    )
)

# Annotation at p=0.5 maximum
fig.add_annotation(
    x=0.5,
    y=1.0,
    text="<b>Peak:</b> both measures = 1.0 at p = 0.5",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2,
    arrowcolor="#444444",
    ax=80,
    ay=-55,
    font={"size": 17, "color": "#222222"},
    bgcolor="rgba(255,255,255,0.92)",
    bordercolor="#AAAAAA",
    borderwidth=1,
    borderpad=7,
)

# Annotation highlighting divergence region at point of max difference
max_diff_idx = int(np.argmax(entropy - gini))
fig.add_annotation(
    x=p[max_diff_idx],
    y=(entropy[max_diff_idx] + gini[max_diff_idx]) / 2,
    text="<b>Divergence region</b><br>Entropy is wider than Gini",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor="#444444",
    ax=110,
    ay=60,
    font={"size": 16, "color": "#222222"},
    bgcolor="rgba(255,255,255,0.92)",
    bordercolor="#AAAAAA",
    borderwidth=1,
    borderpad=6,
)

# Vertical line at p=0.5 for visual reference
fig.add_vline(x=0.5, line_width=1.5, line_dash="dot", line_color="rgba(0,0,0,0.2)")

# Style
fig.update_layout(
    title={
        "text": "line-impurity-comparison · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1a1a2e", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Probability (p)", "font": {"size": 22, "color": "#333333"}},
        "tickfont": {"size": 18, "color": "#555555"},
        "range": [-0.02, 1.02],
        "dtick": 0.1,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.05)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#BBBBBB",
        "linewidth": 1.5,
        "zeroline": False,
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Impurity Measure (normalized)", "font": {"size": 22, "color": "#333333"}},
        "tickfont": {"size": 18, "color": "#555555"},
        "range": [-0.02, 1.08],
        "dtick": 0.2,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.05)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#BBBBBB",
        "linewidth": 1.5,
        "zeroline": False,
        "mirror": False,
    },
    template="plotly_white",
    legend={
        "font": {"size": 16, "color": "#333333"},
        "x": 0.02,
        "y": 0.02,
        "xanchor": "left",
        "yanchor": "bottom",
        "bgcolor": "rgba(255,255,255,0.92)",
        "bordercolor": "#CCCCCC",
        "borderwidth": 1,
    },
    plot_bgcolor="#FAFBFC",
    paper_bgcolor="#FFFFFF",
    margin={"l": 80, "r": 50, "t": 80, "b": 65},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
