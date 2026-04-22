""" pyplots.ai
wordcloud-basic: Basic Word Cloud
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import random

import numpy as np
import plotly.graph_objects as go


# Data - Programming language popularity (realistic survey data)
word_frequencies = {
    "Python": 100,
    "JavaScript": 95,
    "Java": 75,
    "TypeScript": 70,
    "C++": 60,
    "C#": 55,
    "Go": 50,
    "Rust": 48,
    "PHP": 45,
    "Swift": 40,
    "Kotlin": 38,
    "Ruby": 35,
    "Scala": 30,
    "R": 28,
    "Dart": 25,
    "Perl": 22,
    "Lua": 20,
    "Haskell": 18,
    "Julia": 16,
    "Elixir": 14,
    "Clojure": 12,
    "OCaml": 10,
    "Erlang": 9,
    "Lisp": 8,
    "SQL": 85,
    "HTML": 80,
    "CSS": 72,
    "Shell": 42,
}

# Seed for reproducibility
random.seed(42)
np.random.seed(42)

# Calculate font sizes based on frequency
max_freq = max(word_frequencies.values())
min_freq = min(word_frequencies.values())

# Scale font sizes for 4800x2700 output
min_size = 28
max_size = 90

# Colors - using Python-themed palette with variations
colors = [
    "#306998",  # Python Blue
    "#FFD43B",  # Python Yellow
    "#4B8BBE",  # Lighter blue
    "#646464",  # Gray
    "#3776AB",  # Another blue
    "#FFE873",  # Light yellow
    "#5A9BD5",  # Sky blue
    "#7F7F7F",  # Medium gray
]

# Sort by frequency (largest first) for better placement
sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
words = [w[0] for w in sorted_words]
freqs = [w[1] for w in sorted_words]

# Manual placement for a visually pleasing word cloud layout
# Positions adjusted to avoid overlap while creating cloud-like appearance
positions = [
    # Top section - largest words spread out
    (0.50, 0.85),  # Python - center top
    (0.15, 0.70),  # JavaScript - left
    (0.80, 0.72),  # SQL - right
    (0.50, 0.60),  # HTML - center
    (0.25, 0.50),  # Java - left mid
    (0.75, 0.52),  # CSS - right mid
    (0.50, 0.40),  # TypeScript - center
    (0.10, 0.35),  # C++ - far left
    (0.88, 0.38),  # C# - far right
    (0.35, 0.28),  # Go - left lower
    (0.65, 0.28),  # Rust - right lower
    (0.50, 0.20),  # PHP - center lower
    (0.20, 0.18),  # Shell - left bottom
    (0.80, 0.18),  # Swift - right bottom
    # Middle-small words
    (0.08, 0.55),  # Kotlin
    (0.92, 0.55),  # Ruby
    (0.30, 0.68),  # Scala
    (0.70, 0.42),  # R
    (0.15, 0.08),  # Dart
    (0.40, 0.08),  # Perl
    (0.60, 0.08),  # Lua
    (0.85, 0.08),  # Haskell
    # Smallest words - edges
    (0.05, 0.88),  # Julia
    (0.95, 0.88),  # Elixir
    (0.05, 0.22),  # Clojure
    (0.95, 0.22),  # OCaml
    (0.25, 0.92),  # Erlang
    (0.75, 0.92),  # Lisp
]

# Create figure
fig = go.Figure()

# Add each word as a scatter trace with text
for i, (word, freq) in enumerate(zip(words, freqs)):
    if i < len(positions):
        x, y = positions[i]
    else:
        # Fallback for any extra words
        x = random.uniform(0.1, 0.9)
        y = random.uniform(0.1, 0.9)

    # Scale frequency to font size range (inline calculation)
    font_size = min_size + (freq - min_freq) / (max_freq - min_freq) * (max_size - min_size)
    color = colors[i % len(colors)]

    fig.add_trace(
        go.Scatter(
            x=[x],
            y=[y],
            mode="text",
            text=[word],
            textfont=dict(size=font_size, color=color, family="Arial Black"),
            hoverinfo="text",
            hovertext=f"{word}: {freq}",
            showlegend=False,
        )
    )

# Update layout for clean word cloud appearance
fig.update_layout(
    title=dict(
        text="wordcloud-basic · plotly · pyplots.ai", font=dict(size=32, color="#306998"), x=0.5, xanchor="center"
    ),
    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-0.05, 1.05]),
    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-0.02, 1.02]),
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=20, r=20, t=80, b=20),
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True)
