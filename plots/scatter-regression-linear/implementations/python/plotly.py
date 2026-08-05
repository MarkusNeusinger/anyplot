""" anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: plotly 6.9.0 | Python 3.13.14
Quality: 90/100 | Updated: 2026-08-05
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (Imprint palette — prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
FONT_FAMILY = "Arial, Helvetica, sans-serif"

BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series
ACCENT = "#C475FD"  # Imprint palette position 2

# Data - study hours vs exam scores (clipped to a realistic 0-100% range)
np.random.seed(42)
n_points = 100
study_hours = np.random.uniform(2, 10, n_points)
noise = np.random.normal(0, 6, n_points)
exam_scores = np.clip(study_hours * 4.5 + 45 + noise, 0, 100)

# Linear regression
n = len(study_hours)
x_mean = np.mean(study_hours)
slope, intercept = np.polyfit(study_hours, exam_scores, 1)

y_pred = slope * study_hours + intercept
residuals = exam_scores - y_pred
ss_res = np.sum(residuals**2)
ss_tot = np.sum((exam_scores - np.mean(exam_scores)) ** 2)
r_squared = 1 - ss_res / ss_tot

# Regression line and confidence interval
x_line = np.linspace(study_hours.min() - 0.5, study_hours.max() + 0.5, 100)
y_line = slope * x_line + intercept

# Calculate 95% confidence interval
ss_xx = np.sum((study_hours - x_mean) ** 2)
mse = ss_res / (n - 2)
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
        line=dict(color="rgba(0, 158, 115, 0.35)", width=1),
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
        marker=dict(size=8, color=BRAND, opacity=0.55, line=dict(width=0.5, color=PAGE_BG)),
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
        line=dict(color=ACCENT, width=3),
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
    font=dict(size=12, color=INK),
    align="right",
    bgcolor=ELEVATED_BG,
    borderpad=8,
)

# Layout
title_text = "scatter-regression-linear · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    font=dict(family=FONT_FAMILY, color=INK),
    title=dict(text=title_text, font=dict(size=16, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Study Hours per Day", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        showgrid=True,
        zeroline=False,
        linecolor=INK_SOFT,
        linewidth=1,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="dot",
        spikecolor=INK_SOFT,
        spikethickness=1,
    ),
    yaxis=dict(
        title=dict(text="Exam Score (%)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        showgrid=True,
        zeroline=False,
        linecolor=INK_SOFT,
        linewidth=1,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="dot",
        spikecolor=INK_SOFT,
        spikethickness=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend=dict(x=0.02, y=0.98, xanchor="left", yanchor="top", font=dict(size=10, color=INK_SOFT), bgcolor=ELEVATED_BG),
    margin=dict(l=80, r=40, t=80, b=60),
    hovermode="closest",
)

# Save as PNG and HTML — hard target 3200x1800 (see prompts/library/plotly.md "Canvas")
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
