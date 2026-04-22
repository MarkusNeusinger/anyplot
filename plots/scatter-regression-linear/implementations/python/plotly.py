""" pyplots.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: plotly 6.5.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-24
"""

import numpy as np
import plotly.graph_objects as go


# Data - advertising spend vs sales revenue
np.random.seed(42)
n_points = 80
x = np.random.uniform(10, 100, n_points)  # Advertising spend (thousands $)
noise = np.random.normal(0, 12, n_points)
y = 2.5 * x + 30 + noise  # Sales revenue (thousands $)

# Linear regression using numpy (no scipy needed)
n = len(x)
x_mean = np.mean(x)
y_mean = np.mean(y)
ss_xy = np.sum((x - x_mean) * (y - y_mean))
ss_xx = np.sum((x - x_mean) ** 2)
ss_yy = np.sum((y - y_mean) ** 2)

slope = ss_xy / ss_xx
intercept = y_mean - slope * x_mean
r_value = ss_xy / np.sqrt(ss_xx * ss_yy)
r_squared = r_value**2

# Regression line and confidence interval
x_line = np.linspace(x.min() - 5, x.max() + 5, 100)
y_line = slope * x_line + intercept

# Calculate standard error and 95% confidence interval
y_pred = slope * x + intercept
residuals = y - y_pred
mse = np.sum(residuals**2) / (n - 2)
se_slope = np.sqrt(mse / ss_xx)

# Standard error of the regression line at each x_line point
se_line = np.sqrt(mse * (1 / n + (x_line - x_mean) ** 2 / ss_xx))

# t-value for 95% CI with n-2 degrees of freedom (approx 1.99 for n=80)
t_val = 1.99
ci_upper = y_line + t_val * se_line
ci_lower = y_line - t_val * se_line

# Create figure
fig = go.Figure()

# Confidence interval band
fig.add_trace(
    go.Scatter(
        x=np.concatenate([x_line, x_line[::-1]]),
        y=np.concatenate([ci_upper, ci_lower[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.2)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        name="95% CI",
        showlegend=True,
    )
)

# Scatter points
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker=dict(size=14, color="#306998", opacity=0.65, line=dict(width=1, color="#1a3d5c")),
        name="Data points",
    )
)

# Regression line
fig.add_trace(
    go.Scatter(
        x=x_line, y=y_line, mode="lines", line=dict(color="#FFD43B", width=4), name=f"Regression (R² = {r_squared:.3f})"
    )
)

# Equation annotation
equation = f"y = {slope:.2f}x + {intercept:.2f}"
fig.add_annotation(
    x=0.02,
    y=0.98,
    xref="paper",
    yref="paper",
    text=f"{equation}<br>R² = {r_squared:.3f}<br>r = {r_value:.3f}",
    showarrow=False,
    font=dict(size=20, color="#333"),
    align="left",
    bgcolor="rgba(255,255,255,0.8)",
    bordercolor="#306998",
    borderwidth=2,
    borderpad=10,
)

# Layout
fig.update_layout(
    title=dict(
        text="scatter-regression-linear · plotly · pyplots.ai",
        font=dict(size=28, color="#333"),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Advertising Spend (thousands $)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Sales Revenue (thousands $)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        zeroline=False,
    ),
    template="plotly_white",
    legend=dict(
        x=0.98,
        y=0.02,
        xanchor="right",
        yanchor="bottom",
        font=dict(size=18),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#ccc",
        borderwidth=1,
    ),
    margin=dict(l=80, r=60, t=100, b=80),
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
