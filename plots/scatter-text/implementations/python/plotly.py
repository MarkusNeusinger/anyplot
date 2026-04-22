""" pyplots.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: plotly 6.5.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go


# Data - Programming languages positioned by paradigm characteristics
np.random.seed(42)

# Language names as labels
labels = [
    "Python",
    "JavaScript",
    "Java",
    "C++",
    "Ruby",
    "Go",
    "Rust",
    "Kotlin",
    "Swift",
    "TypeScript",
    "Scala",
    "Haskell",
    "Elixir",
    "Clojure",
    "F#",
    "R",
    "Julia",
    "MATLAB",
    "Perl",
    "PHP",
    "C#",
    "Dart",
    "Lua",
    "Erlang",
    "OCaml",
    "Fortran",
    "COBOL",
    "Assembly",
    "Lisp",
    "Prolog",
]

# Position based on: x = Level of abstraction, y = Type safety
# Coordinates carefully placed to avoid all text overlaps
x = np.array(
    [
        8.5,  # Python
        5.5,  # JavaScript - shifted further left
        6.0,  # Java
        3.0,  # C++
        8.0,  # Ruby
        5.5,  # Go
        4.0,  # Rust
        5.0,  # Kotlin - shifted significantly left
        7.0,  # Swift
        7.5,  # TypeScript
        6.5,  # Scala - shifted left
        9.0,  # Haskell
        8.5,  # Elixir
        9.8,  # Clojure - shifted to far right edge
        8.0,  # F#
        9.5,  # R - shifted right
        7.5,  # Julia
        6.5,  # MATLAB - shifted left
        8.5,  # Perl - shifted significantly right
        7.0,  # PHP
        6.0,  # C#
        8.0,  # Dart - shifted right, away from Kotlin
        6.0,  # Lua - shifted left
        9.2,  # Erlang - shifted right
        8.5,  # OCaml
        2.0,  # Fortran - shifted further left
        5.0,  # COBOL - shifted significantly right
        1.0,  # Assembly
        9.5,  # Lisp - shifted right
        7.5,  # Prolog - shifted significantly left
    ]
)

y = np.array(
    [
        3.0,  # Python
        1.5,  # JavaScript - shifted down
        8.0,  # Java
        6.0,  # C++
        1.5,  # Ruby - shifted down
        7.0,  # Go
        9.0,  # Rust
        8.5,  # Kotlin - shifted up
        9.0,  # Swift - shifted up
        7.0,  # TypeScript - shifted down
        9.0,  # Scala - shifted up
        9.5,  # Haskell
        5.5,  # Elixir - shifted down
        4.5,  # Clojure - shifted down significantly
        8.5,  # F#
        3.0,  # R
        4.5,  # Julia
        3.0,  # MATLAB
        2.5,  # Perl
        1.5,  # PHP - shifted down
        8.5,  # C# - shifted up
        6.0,  # Dart - shifted down, away from Kotlin
        4.0,  # Lua - shifted up
        6.5,  # Erlang
        9.5,  # OCaml - shifted up
        3.5,  # Fortran - shifted down
        6.5,  # COBOL - shifted up, away from Fortran
        2.5,  # Assembly - shifted down
        5.0,  # Lisp - shifted up
        8.0,  # Prolog - shifted up significantly
    ]
)

# Color by category (functional, OOP, multi-paradigm, systems)
categories = [
    "Multi-paradigm",
    "Multi-paradigm",
    "OOP",
    "Systems",
    "OOP",
    "Systems",
    "Systems",
    "OOP",
    "OOP",
    "Multi-paradigm",
    "Functional",
    "Functional",
    "Functional",
    "Functional",
    "Functional",
    "Statistical",
    "Scientific",
    "Scientific",
    "Scripting",
    "Scripting",
    "OOP",
    "OOP",
    "Scripting",
    "Functional",
    "Functional",
    "Scientific",
    "Legacy",
    "Systems",
    "Functional",
    "Functional",
]

# Color mapping (improved distinction between categories)
color_map = {
    "Multi-paradigm": "#1E88E5",  # Bright Blue
    "OOP": "#FFC107",  # Amber Yellow
    "Systems": "#D32F2F",  # Red
    "Functional": "#43A047",  # Green
    "Statistical": "#8E24AA",  # Deep Purple (more distinct from blue)
    "Scientific": "#00ACC1",  # Cyan (more distinct from blue)
    "Scripting": "#FB8C00",  # Orange
    "Legacy": "#757575",  # Gray
}

colors = [color_map[cat] for cat in categories]

# Create figure with text labels as data points
fig = go.Figure()

# Add text labels grouped by category for legend
for category in color_map:
    mask = [c == category for c in categories]
    if any(mask):
        x_cat = [x[i] for i in range(len(x)) if mask[i]]
        y_cat = [y[i] for i in range(len(y)) if mask[i]]
        labels_cat = [labels[i] for i in range(len(labels)) if mask[i]]
        # Create hover text with detailed information
        hover_cat = [
            f"<b>{labels[i]}</b><br>Paradigm: {category}<br>Abstraction: {x[i]:.1f}<br>Type Safety: {y[i]:.1f}"
            for i in range(len(labels))
            if mask[i]
        ]

        fig.add_trace(
            go.Scatter(
                x=x_cat,
                y=y_cat,
                mode="text",
                text=labels_cat,
                textfont=dict(size=18, color=color_map[category], family="Arial Black"),
                textposition="middle center",
                name=category,
                showlegend=True,
                hovertext=hover_cat,
                hoverinfo="text",
            )
        )

# Update layout
fig.update_layout(
    title=dict(text="scatter-text · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Level of Abstraction (0-10 scale)", font=dict(size=24)),
        tickfont=dict(size=18),
        range=[0, 10.5],
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Type Safety (0-10 scale)", font=dict(size=24)),
        tickfont=dict(size=18),
        range=[0, 10.5],
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    legend=dict(
        title=dict(text="Paradigm", font=dict(size=18)),
        font=dict(size=16),
        x=1.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        itemsizing="constant",
    ),
    margin=dict(l=80, r=180, t=100, b=80),
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
