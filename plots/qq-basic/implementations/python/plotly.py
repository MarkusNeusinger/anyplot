""" anyplot.ai
qq-basic: Basic Q-Q Plot
Library: plotly 6.7.0 | Python 3.14.4
Quality: 82/100 | Updated: 2026-04-27
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

BRAND = "#009E73"  # Okabe-Ito position 1 — Q-Q scatter points
REF_COLOR = "#D55E00"  # Okabe-Ito position 2 — reference line

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

# Reference line (y=x for standardized data)
margin = 0.3
line_min = min(theoretical_quantiles.min(), sample_standardized.min()) - margin
line_max = max(theoretical_quantiles.max(), sample_standardized.max()) + margin

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=theoretical_quantiles,
        y=sample_standardized,
        mode="markers",
        marker={"size": 14, "color": BRAND, "opacity": 0.85},
        name="Sample Quantiles",
    )
)

fig.add_trace(
    go.Scatter(
        x=[line_min, line_max],
        y=[line_min, line_max],
        mode="lines",
        line={"color": REF_COLOR, "width": 3, "dash": "dash"},
        name="Reference (y=x)",
    )
)

# Style
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={"text": "qq-basic · plotly · anyplot.ai", "font": {"size": 28, "color": INK}},
    xaxis={
        "title": {"text": "Theoretical Quantiles", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Sample Quantiles", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 18, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
