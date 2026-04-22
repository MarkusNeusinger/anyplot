""" pyplots.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: plotly 6.5.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go


# Data - Server response times by endpoint (large dataset for boxen plot)
np.random.seed(42)

endpoints = ["API Gateway", "Auth Service", "Data Query", "File Upload"]
n_points = 5000

# Generate different distributions for each endpoint
data = {
    "API Gateway": np.concatenate(
        [
            np.random.lognormal(mean=4, sigma=0.5, size=int(n_points * 0.9)),
            np.random.uniform(200, 500, size=int(n_points * 0.1)),
        ]
    ),
    "Auth Service": np.random.exponential(scale=30, size=n_points) + 10,
    "Data Query": np.concatenate(
        [
            np.random.normal(loc=100, scale=20, size=int(n_points * 0.7)),
            np.random.normal(loc=250, scale=30, size=int(n_points * 0.3)),
        ]
    ),
    "File Upload": np.concatenate(
        [
            np.random.gamma(shape=2, scale=50, size=int(n_points * 0.85)),
            np.random.uniform(400, 800, size=int(n_points * 0.15)),
        ]
    ),
}

# Colors for quantile levels (darker for inner boxes, lighter for outer)
colors = [
    "rgba(48, 105, 152, 1.0)",
    "rgba(48, 105, 152, 0.85)",
    "rgba(48, 105, 152, 0.7)",
    "rgba(48, 105, 152, 0.55)",
    "rgba(48, 105, 152, 0.4)",
    "rgba(48, 105, 152, 0.3)",
    "rgba(48, 105, 152, 0.2)",
    "rgba(48, 105, 152, 0.15)",
]

fig = go.Figure()

box_width_base = 0.7
positions = list(range(len(endpoints)))
n_levels = 7  # Number of letter value levels

for idx, endpoint in enumerate(endpoints):
    pos = positions[idx]
    values = data[endpoint]
    n = len(values)
    sorted_vals = np.sort(values)
    median = np.median(values)

    # Compute letter values (quantiles at 1/2, 1/4, 1/8, 1/16, etc.)
    letter_values = []
    for i in range(n_levels):
        depth = 2 ** (i + 1)
        lower_idx = max(0, min(int(n / depth), n - 1))
        upper_idx = max(0, min(int(n - n / depth), n - 1))
        letter_values.append((sorted_vals[lower_idx], sorted_vals[upper_idx]))

    # Draw boxes from outermost (widest, lightest) to innermost (narrowest, darkest)
    for i in range(n_levels - 1, -1, -1):
        lower, upper = letter_values[i]
        width = box_width_base * (1 - i * 0.1)

        fig.add_shape(
            type="rect",
            x0=pos - width / 2,
            x1=pos + width / 2,
            y0=lower,
            y1=upper,
            fillcolor=colors[i],
            line={"color": "#306998", "width": 1.5},
            layer="below",
        )

    # Add median line
    fig.add_shape(
        type="line",
        x0=pos - box_width_base / 2,
        x1=pos + box_width_base / 2,
        y0=median,
        y1=median,
        line={"color": "#FFD43B", "width": 5},
    )

    # Find and plot outliers (beyond the outermost letter value)
    outer_lower, outer_upper = letter_values[-1]
    outliers = values[(values < outer_lower) | (values > outer_upper)]

    if len(outliers) > 0:
        outlier_sample = outliers if len(outliers) <= 100 else np.random.choice(outliers, 100, replace=False)
        jitter = np.random.uniform(-0.08, 0.08, size=len(outlier_sample))

        fig.add_trace(
            go.Scatter(
                x=pos + jitter,
                y=outlier_sample,
                mode="markers",
                marker={"color": "#306998", "size": 8, "opacity": 0.6},
                showlegend=False,
                hovertemplate="Response: %{y:.0f}ms<extra></extra>",
            )
        )

# Add legend entries for quantile levels
quantile_labels = ["50% (IQR)", "75%", "87.5%", "93.75%", "96.9%", "98.4%", "99.2%"]
for i, label in enumerate(quantile_labels):
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 20, "color": colors[i], "symbol": "square", "line": {"color": "#306998", "width": 1}},
            name=label,
            showlegend=True,
        )
    )

# Add median legend entry
fig.add_trace(
    go.Scatter(x=[None], y=[None], mode="lines", line={"color": "#FFD43B", "width": 5}, name="Median", showlegend=True)
)

# Layout
fig.update_layout(
    title={
        "text": "boxen-basic · plotly · pyplots.ai",
        "font": {"size": 36, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Server Endpoint", "font": {"size": 26}},
        "tickfont": {"size": 20},
        "tickvals": positions,
        "ticktext": endpoints,
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Response Time (ms)", "font": {"size": 26}},
        "tickfont": {"size": 20},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    legend={
        "title": {"text": "Quantile Level", "font": {"size": 20}},
        "font": {"size": 18},
        "x": 1.02,
        "y": 0.5,
        "yanchor": "middle",
        "bgcolor": "rgba(255,255,255,0.95)",
        "bordercolor": "#cccccc",
        "borderwidth": 1,
    },
    margin={"l": 120, "r": 220, "t": 100, "b": 100},
    plot_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
