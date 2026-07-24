""" anyplot.ai
qq-basic: Basic Q-Q Plot
Library: plotly 6.9.0 | Python 3.13.14
Quality: 88/100 | Updated: 2026-07-24
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"  # Imprint palette position 1 — Q-Q scatter points
REF_COLOR = INK  # Imprint semantic anchor "neutral" — reference line (baseline role)
BAND_COLOR = INK_MUTED  # Imprint semantic anchor "muted" — confidence envelope

# Data - sample with slight positive skew to demonstrate Q-Q plot interpretation
np.random.seed(42)
sample = np.concatenate(
    [
        np.random.normal(50, 10, 80),  # Main normal distribution
        np.random.normal(75, 5, 20),  # Slight right tail for interest
    ]
)
sample = np.sort(sample)

# Standardize sample for comparison with standard normal
sample_standardized = (sample - np.mean(sample)) / np.std(sample)

# Theoretical quantiles via Blom's plotting positions + Winitzki erfinv approximation
n = len(sample)
probabilities = (np.arange(1, n + 1) - 0.375) / (n + 0.25)
q = 2 * probabilities - 1  # map to [-1, 1] for erfinv
a = 0.147
ln1q2 = np.log(1 - q**2)
b = 2 / (np.pi * a) + ln1q2 / 2
theoretical_quantiles = np.sign(q) * np.sqrt(2) * np.sqrt(np.sqrt(b**2 - ln1q2 / a) - b)

# 95% confidence envelope from the asymptotic variance of normal order statistics
normal_density = np.exp(-(theoretical_quantiles**2) / 2) / np.sqrt(2 * np.pi)
band_half_width = 1.96 * np.sqrt(probabilities * (1 - probabilities) / n) / normal_density

# Reference line (y=x for standardized data)
margin = 0.3
line_min = min(theoretical_quantiles.min(), sample_standardized.min()) - margin
line_max = max(theoretical_quantiles.max(), sample_standardized.max()) + margin

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=np.concatenate([theoretical_quantiles, theoretical_quantiles[::-1]]),
        y=np.concatenate([theoretical_quantiles + band_half_width, (theoretical_quantiles - band_half_width)[::-1]]),
        fill="toself",
        fillcolor=BAND_COLOR,
        opacity=0.15,
        line={"width": 0},
        hoverinfo="skip",
        name="95% Confidence Band",
        legendrank=3,
    )
)

fig.add_trace(
    go.Scatter(
        x=[line_min, line_max],
        y=[line_min, line_max],
        mode="lines",
        line={"color": REF_COLOR, "width": 2.5, "dash": "dash"},
        name="Reference (y=x)",
        hoverinfo="skip",
        legendrank=2,
    )
)

fig.add_trace(
    go.Scatter(
        x=theoretical_quantiles,
        y=sample_standardized,
        mode="markers",
        marker={"size": 10, "color": BRAND, "opacity": 0.85},
        name="Sample Quantiles",
        hovertemplate="Theoretical: %{x:.3f}<br>Sample: %{y:.3f}<extra></extra>",
        legendrank=1,
    )
)

# Style
title_text = "qq-basic · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={"text": title_text, "font": {"size": 16, "color": INK}},
    xaxis={
        "title": {"text": "Theoretical Quantiles", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": INK_SOFT,
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Sample Quantiles", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linewidth": 1.5,
        "linecolor": INK_SOFT,
        "mirror": False,
    },
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
