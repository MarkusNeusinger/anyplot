""" anyplot.ai
count-basic: Basic Count Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series

# Data - Product category purchases with heavily skewed distribution
np.random.seed(42)
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Beauty"]
# Generate raw purchase data with heavily right-skewed distribution
# Electronics dominates, others taper off
probabilities = [0.40, 0.25, 0.15, 0.10, 0.05, 0.03, 0.02]
raw_data = np.random.choice(categories, size=250, p=probabilities)

# Count occurrences
unique, counts = np.unique(raw_data, return_counts=True)
# Sort by frequency (descending)
sort_idx = np.argsort(counts)[::-1]
sorted_categories = unique[sort_idx]
sorted_counts = counts[sort_idx]

# Calculate percentages for hover templates
total = sorted_counts.sum()
percentages = (sorted_counts / total * 100).round(1)

# Create hover text with count and percentage
hover_text = [
    f"{cat}<br>Count: {count}<br>Percentage: {pct}%"
    for cat, count, pct in zip(sorted_categories, sorted_counts, percentages)
]

# Create figure
fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=sorted_categories,
        y=sorted_counts,
        marker=dict(color=BRAND, line=dict(color=INK_SOFT, width=2)),
        text=sorted_counts,
        textposition="outside",
        textfont=dict(size=20, color=INK),
        hovertext=hover_text,
        hoverinfo="text",
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    title=dict(text="count-basic · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Product Category", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Count (n)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    bargap=0.3,
    margin=dict(t=120, b=100, l=100, r=60),
    legend=dict(bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1, font=dict(color=INK_SOFT)),
)

# Save as PNG (4800 x 2700 px)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
