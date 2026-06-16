""" anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: plotly 6.7.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-06
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - study hours vs exam scores
np.random.seed(42)
n_points = 100
study_hours = np.random.uniform(2, 10, n_points)
noise = np.random.normal(0, 8, n_points)
exam_scores = study_hours * 8.5 + 45 + noise

# Linear regression
n = len(study_hours)
x_mean = np.mean(study_hours)
y_mean = np.mean(exam_scores)
ss_xy = np.sum((study_hours - x_mean) * (exam_scores - y_mean))
ss_xx = np.sum((study_hours - x_mean) ** 2)
ss_yy = np.sum((exam_scores - y_mean) ** 2)

slope = ss_xy / ss_xx
intercept = y_mean - slope * x_mean
r_value = ss_xy / np.sqrt(ss_xx * ss_yy)
r_squared = r_value**2

# Regression line and confidence interval
x_line = np.linspace(study_hours.min() - 0.5, study_hours.max() + 0.5, 100)
y_line = slope * x_line + intercept

# Calculate 95% confidence interval
y_pred = slope * study_hours + intercept
residuals = exam_scores - y_pred
mse = np.sum(residuals**2) / (n - 2)
se_slope = np.sqrt(mse / ss_xx)

se_line = np.sqrt(mse * (1 / n + (x_line - x_mean) ** 2 / ss_xx))
t_val = 1.98
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
        fillcolor="rgba(0, 158, 115, 0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        name="95% CI",
        showlegend=True,
    )
)

# Scatter points
fig.add_trace(
    go.Scatter(
        x=study_hours,
        y=exam_scores,
        mode="markers",
        marker=dict(size=12, color=BRAND, opacity=0.65),
        name="Data points",
        hovertemplate="Study Hours: %{x:.1f}<br>Exam Score: %{y:.1f}<extra></extra>",
    )
)

# Regression line
fig.add_trace(
    go.Scatter(
        x=x_line,
        y=y_line,
        mode="lines",
        line=dict(color=ACCENT, width=4),
        name=f"Linear Regression (R² = {r_squared:.3f})",
        hoverinfo="skip",
    )
)

# Equation annotation
equation = f"y = {slope:.2f}x + {intercept:.1f}"
fig.add_annotation(
    x=0.98,
    y=0.05,
    xref="paper",
    yref="paper",
    text=f"{equation}<br>R² = {r_squared:.3f}",
    showarrow=False,
    font=dict(size=18, color=INK),
    align="right",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=12,
)

# Layout
fig.update_layout(
    title=dict(
        text="scatter-regression-linear · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Study Hours per Day", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        showgrid=True,
        zeroline=False,
        linecolor=INK_SOFT,
        linewidth=1,
    ),
    yaxis=dict(
        title=dict(text="Exam Score (%)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        showgrid=True,
        zeroline=False,
        linecolor=INK_SOFT,
        linewidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend=dict(
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        font=dict(size=16, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=80, r=60, t=100, b=80),
    hovermode="closest",
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
