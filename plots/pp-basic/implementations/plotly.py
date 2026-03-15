"""pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: plotly 6.6.0 | Python 3.14.3
"""

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# Data: mixture of normal + exponential simulating process drift
np.random.seed(42)
observed = np.random.normal(loc=50, scale=10, size=200) + np.random.exponential(scale=2, size=200)

observed_sorted = np.sort(observed)
n = len(observed_sorted)

# Fit normal distribution to observed data
mu, sigma = stats.norm.fit(observed_sorted)

# Empirical CDF using plotting position formula i/(n+1)
empirical_cdf = np.arange(1, n + 1) / (n + 1)

# Theoretical CDF from fitted normal
theoretical_cdf = stats.norm.cdf(observed_sorted, loc=mu, scale=sigma)

# Deviation threshold for storytelling
deviation = np.abs(empirical_cdf - theoretical_cdf)
threshold = np.percentile(deviation, 85)
is_deviant = deviation > threshold

# 95% confidence band (Kolmogorov-Smirnov)
ks_band = 1.36 / np.sqrt(n)
diag = np.linspace(0, 1, 200)

# Plot
fig = go.Figure()

# Confidence band
fig.add_trace(
    go.Scatter(
        x=np.concatenate([diag, diag[::-1]]),
        y=np.concatenate([diag + ks_band, (diag - ks_band)[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.08)",
        line={"width": 0},
        name="95% KS confidence band",
        hoverinfo="skip",
    )
)

# Reference line
fig.add_trace(
    go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode="lines",
        line={"color": "#306998", "width": 2.5, "dash": "dash"},
        name="Perfect normal fit",
        hoverinfo="skip",
    )
)

# Data points: within expected range
fig.add_trace(
    go.Scatter(
        x=theoretical_cdf[~is_deviant],
        y=empirical_cdf[~is_deviant],
        mode="markers",
        marker={"size": 9, "color": "#306998", "opacity": 0.7, "line": {"width": 0.5, "color": "white"}},
        name="Within expected range",
        customdata=np.column_stack([observed_sorted[~is_deviant], deviation[~is_deviant]]),
        hovertemplate=(
            "Theoretical: %{x:.3f}<br>"
            "Empirical: %{y:.3f}<br>"
            "Value: %{customdata[0]:.1f}<br>"
            "Deviation: %{customdata[1]:.3f}"
            "<extra></extra>"
        ),
    )
)

# Data points: tail deviations
fig.add_trace(
    go.Scatter(
        x=theoretical_cdf[is_deviant],
        y=empirical_cdf[is_deviant],
        mode="markers",
        marker={
            "size": 11,
            "color": "#E8833A",
            "symbol": "diamond",
            "opacity": 0.85,
            "line": {"width": 0.8, "color": "white"},
        },
        name="Tail deviation",
        customdata=np.column_stack([observed_sorted[is_deviant], deviation[is_deviant]]),
        hovertemplate=(
            "Theoretical: %{x:.3f}<br>"
            "Empirical: %{y:.3f}<br>"
            "Value: %{customdata[0]:.1f}<br>"
            "Deviation: %{customdata[1]:.3f}"
            "<extra></extra>"
        ),
    )
)

# Annotation pointing to right-tail deviation
tail_idx = np.where(is_deviant & (theoretical_cdf > 0.8))[0]
if len(tail_idx) > 0:
    ax_pt = theoretical_cdf[tail_idx[len(tail_idx) // 2]]
    ay_pt = empirical_cdf[tail_idx[len(tail_idx) // 2]]
    fig.add_annotation(
        x=ax_pt,
        y=ay_pt,
        ax=-60,
        ay=-50,
        text="Heavier right tail<br>→ process drift detected",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=2,
        arrowcolor="#E8833A",
        font={"size": 16, "color": "#444444"},
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#E8833A",
        borderwidth=1.5,
        borderpad=6,
    )

# Layout
fig.update_layout(
    title={
        "text": "pp-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Theoretical CDF (Normal)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-0.02, 1.02],
        "showgrid": False,
        "showline": True,
        "linecolor": "#BBBBBB",
        "linewidth": 1.5,
        "zeroline": False,
        "ticks": "outside",
        "tickcolor": "#BBBBBB",
        "dtick": 0.2,
    },
    yaxis={
        "title": {"text": "Empirical CDF", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-0.02, 1.02],
        "showgrid": False,
        "showline": True,
        "linecolor": "#BBBBBB",
        "linewidth": 1.5,
        "zeroline": False,
        "ticks": "outside",
        "tickcolor": "#BBBBBB",
        "dtick": 0.2,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    legend={
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
        "font": {"size": 16},
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "#DDDDDD",
        "borderwidth": 1,
    },
    template="plotly_white",
    width=1200,
    height=1200,
    margin={"l": 70, "r": 30, "t": 60, "b": 70},
    plot_bgcolor="white",
    paper_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
