"""anyplot.ai
count-basic: Basic Count Plot
Library: plotly 6.9.0 | Python 3.13.14
Quality: pending | Updated: 2026-08-11
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series

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

# Each bar's own share of all observations
total = sorted_counts.sum()
percentages = sorted_counts / total * 100

bar_hover = [
    f"{cat}<br>Count: {count}<br>Share: {pct:.1f}%"
    for cat, count, pct in zip(sorted_categories, sorted_counts, percentages, strict=True)
]
bar_labels = [f"{count}<br>{pct:.1f}%" for count, pct in zip(sorted_counts, percentages, strict=True)]

# Title fontsize scales linearly with title length off the 67-char baseline,
# both up (short titles) and down (long titles), clamped to a legible range
title_text = "count-basic · python · plotly · anyplot.ai"
title_fontsize = max(11, min(24, round(16 * 67 / len(title_text))))

fig = go.Figure(
    go.Bar(
        x=sorted_categories,
        y=sorted_counts,
        marker=dict(color=BRAND, opacity=0.9, line=dict(color=INK_SOFT, width=1.5)),
        text=bar_labels,
        textposition="outside",
        textfont=dict(size=14, color=INK),
        hovertext=bar_hover,
        hoverinfo="text",
    )
)

# Layout — hard target 3200 x 1800 (see "Canvas — hard rule" in prompts/library/plotly.md)
fig.update_layout(
    autosize=False,
    title=dict(text=title_text, font=dict(size=title_fontsize, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Product Category", font=dict(size=14, color=INK)),
        tickfont=dict(size=12, color=INK_SOFT),
        showline=True,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Count (n)", font=dict(size=14, color=INK)),
        tickfont=dict(size=12, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        showline=True,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        # Headroom above the tallest bar so the two-line count/share label
        # (outside text) never clips against the title.
        range=[0, float(sorted_counts.max()) * 1.22],
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    bargap=0.3,
    showlegend=False,  # single series — a legend would be redundant chrome
    margin=dict(l=90, r=50, t=100, b=90),
)

# Save as PNG — hard target 3200 x 1800 (landscape)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)

# Save as HTML for interactivity
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
