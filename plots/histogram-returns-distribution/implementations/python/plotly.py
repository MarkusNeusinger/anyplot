""" pyplots.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: plotly 6.5.2 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-16
"""

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# Data - Simulated daily stock returns (252 trading days)
np.random.seed(42)
n_days = 504  # 2 years of trading days
daily_returns = np.random.normal(loc=0.0005, scale=0.015, size=n_days)  # ~12% annual return, ~24% annual volatility

# Add some fat tails (realistic financial returns)
outliers = np.random.choice(n_days, size=20, replace=False)
daily_returns[outliers] *= np.random.uniform(2, 4, size=20) * np.random.choice([-1, 1], size=20)

# Convert to percentage
returns_pct = daily_returns * 100

# Calculate statistics
mean_ret = np.mean(returns_pct)
std_ret = np.std(returns_pct)
skewness = stats.skew(returns_pct)
kurtosis = stats.kurtosis(returns_pct)

# Create histogram bins
n_bins = 40
hist_values, bin_edges = np.histogram(returns_pct, bins=n_bins, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

# Normal distribution overlay
x_norm = np.linspace(returns_pct.min(), returns_pct.max(), 200)
y_norm = stats.norm.pdf(x_norm, mean_ret, std_ret)

# Identify tail regions (beyond 2 standard deviations)
lower_tail = mean_ret - 2 * std_ret
upper_tail = mean_ret + 2 * std_ret

# Create colors based on tail regions
bar_colors = ["#D62728" if (c < lower_tail or c > upper_tail) else "#306998" for c in bin_centers]

# Create figure
fig = go.Figure()

# Histogram bars
fig.add_trace(
    go.Bar(
        x=bin_centers,
        y=hist_values,
        width=bin_width * 0.9,
        marker_color=bar_colors,
        name="Returns Distribution",
        opacity=0.75,
        hovertemplate="Return: %{x:.2f}%<br>Density: %{y:.4f}<extra></extra>",
    )
)

# Normal distribution overlay
fig.add_trace(
    go.Scatter(x=x_norm, y=y_norm, mode="lines", line=dict(color="#FFD43B", width=4), name="Normal Distribution")
)

# Add vertical lines for mean and tail boundaries
fig.add_vline(
    x=mean_ret, line=dict(color="#1F77B4", width=3, dash="dash"), annotation_text="Mean", annotation_position="top"
)
fig.add_vline(x=lower_tail, line=dict(color="#D62728", width=2, dash="dot"))
fig.add_vline(x=upper_tail, line=dict(color="#D62728", width=2, dash="dot"))

# Statistics text box
stats_text = (
    f"<b>Statistics</b><br>"
    f"Mean: {mean_ret:.3f}%<br>"
    f"Std Dev: {std_ret:.3f}%<br>"
    f"Skewness: {skewness:.3f}<br>"
    f"Kurtosis: {kurtosis:.3f}"
)

fig.add_annotation(
    x=0.98,
    y=0.98,
    xref="paper",
    yref="paper",
    text=stats_text,
    showarrow=False,
    font=dict(size=18, family="monospace"),
    align="left",
    bgcolor="rgba(255, 255, 255, 0.9)",
    bordercolor="#306998",
    borderwidth=2,
    borderpad=10,
)

# Update layout
fig.update_layout(
    title=dict(
        text="histogram-returns-distribution · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Daily Returns (%)", font=dict(size=22)),
        tickfont=dict(size=18),
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="gray",
        tickformat=".1f",
        ticksuffix="%",
    ),
    yaxis=dict(title=dict(text="Probability Density", font=dict(size=22)), tickfont=dict(size=18)),
    template="plotly_white",
    legend=dict(
        x=0.02, y=0.98, font=dict(size=16), bgcolor="rgba(255, 255, 255, 0.9)", bordercolor="#306998", borderwidth=1
    ),
    bargap=0.05,
    showlegend=True,
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
