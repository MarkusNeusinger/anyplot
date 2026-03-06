""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: plotly 6.6.0 | Python 3.14.3
Quality: 75/100 | Created: 2026-03-06
"""

import numpy as np
import plotly.graph_objects as go


# Data - transcription factor binding site motif (10-position DNA)
# Position weight matrix: each row is [A, C, G, T] frequencies
pwm = np.array(
    [
        [0.05, 0.80, 0.05, 0.10],
        [0.10, 0.15, 0.10, 0.65],
        [0.05, 0.85, 0.05, 0.05],
        [0.25, 0.25, 0.25, 0.25],
        [0.70, 0.05, 0.15, 0.10],
        [0.10, 0.10, 0.70, 0.10],
        [0.05, 0.05, 0.05, 0.85],
        [0.60, 0.15, 0.15, 0.10],
        [0.10, 0.10, 0.65, 0.15],
        [0.15, 0.55, 0.10, 0.20],
    ]
)

letters = ["A", "C", "G", "T"]
colors = {"A": "#2ca02c", "C": "#1f77b4", "G": "#ff7f0e", "T": "#d62728"}
n_positions = len(pwm)

# Information content: IC = 2 + sum(f * log2(f)) for DNA (max 2 bits)
info_content = np.zeros(n_positions)
for i in range(n_positions):
    entropy = sum(f * np.log2(f) for f in pwm[i] if f > 0)
    info_content[i] = 2.0 + entropy

# Letter heights = frequency * information content at each position
letter_heights = pwm * info_content[:, np.newaxis]

# Plot
fig = go.Figure()
bar_width = 0.7

for pos in range(n_positions):
    heights = letter_heights[pos]
    sorted_indices = np.argsort(heights)
    y_bottom = 0

    for idx in sorted_indices:
        h = heights[idx]
        if h < 0.01:
            continue
        letter = letters[idx]

        fig.add_trace(
            go.Bar(
                x=[pos + 1],
                y=[h],
                base=y_bottom,
                width=bar_width,
                marker={"color": colors[letter], "line": {"width": 0}},
                showlegend=False,
                hovertemplate=(
                    f"Position {pos + 1}<br>{letter}: {pwm[pos][idx]:.2f}<br>Height: {h:.3f} bits<extra></extra>"
                ),
            )
        )

        font_size = max(14, min(36, int(h * 40)))
        fig.add_annotation(
            x=pos + 1,
            y=y_bottom + h / 2,
            text=f"<b>{letter}</b>",
            font={"size": font_size, "color": "white", "family": "Arial Black"},
            showarrow=False,
            yanchor="middle",
        )

        y_bottom += h

# Legend entries for nucleotides
for letter in letters:
    fig.add_trace(go.Bar(x=[None], y=[None], marker={"color": colors[letter]}, name=letter, showlegend=True))

# Style
fig.update_layout(
    title={"text": "sequence-logo-basic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5},
    xaxis={
        "title": {"text": "Position", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickvals": list(range(1, n_positions + 1)),
        "showline": True,
        "linewidth": 2,
        "linecolor": "black",
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Information content (bits)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, 2.1],
        "showline": True,
        "linewidth": 2,
        "linecolor": "black",
        "mirror": False,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.06)",
    },
    template="plotly_white",
    barmode="overlay",
    bargap=0,
    plot_bgcolor="white",
    legend={"font": {"size": 18}, "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
    margin={"l": 80, "r": 40, "t": 100, "b": 60},
)

# Save
fig.write_html("plot.html")
fig.write_image("plot.png", width=1600, height=900, scale=3)
