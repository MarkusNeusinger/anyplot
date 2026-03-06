""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: plotly 6.6.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-06
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
# Colorblind-safe palette: teal, blue, amber, purple (avoids red-green confusion)
colors = {"A": "#009E73", "C": "#0072B2", "G": "#E69F00", "T": "#CC79A7"}
n_positions = len(pwm)

# Information content: IC = 2 + sum(f * log2(f)) for DNA (max 2 bits)
info_content = np.zeros(n_positions)
for i in range(n_positions):
    entropy = sum(f * np.log2(f) for f in pwm[i] if f > 0)
    info_content[i] = max(0, 2.0 + entropy)

# Letter heights = frequency * information content at each position
letter_heights = pwm * info_content[:, np.newaxis]

# Compute max stack height for y-axis scaling
max_ic = max(info_content)

# Plot
fig = go.Figure()
bar_width = 0.75

for pos in range(n_positions):
    heights = letter_heights[pos]
    sorted_indices = np.argsort(heights)
    y_bottom = 0

    for idx in sorted_indices:
        h = heights[idx]
        if h < 0.005:
            continue
        letter = letters[idx]

        fig.add_trace(
            go.Bar(
                x=[pos + 1],
                y=[h],
                base=y_bottom,
                width=bar_width,
                marker={"color": colors[letter], "line": {"width": 0.5, "color": "rgba(255,255,255,0.6)"}},
                showlegend=False,
                hovertemplate=(
                    f"<b>Position {pos + 1}</b><br>"
                    f"Nucleotide: {letter}<br>"
                    f"Frequency: {pwm[pos][idx]:.0%}<br>"
                    f"Height: {h:.3f} bits"
                    f"<extra></extra>"
                ),
            )
        )

        # Only annotate letters on segments tall enough to be readable
        # Scale font size proportionally to bar height relative to max IC
        if h >= 0.07:
            # Font size scaled by segment height: bigger segments get bigger letters
            font_size = max(16, min(42, int(h / max_ic * 60)))
            fig.add_annotation(
                x=pos + 1,
                y=y_bottom + h / 2,
                text=f"<b>{letter}</b>",
                font={"size": font_size, "color": "white", "family": "Arial Black, Impact, sans-serif"},
                showarrow=False,
                yanchor="middle",
                xanchor="center",
            )

        y_bottom += h

# Legend entries for nucleotides using scatter for cleaner legend markers
for letter in letters:
    fig.add_trace(go.Bar(x=[None], y=[None], marker={"color": colors[letter]}, name=f"  {letter}  ", showlegend=True))

# Style
fig.update_layout(
    title={
        "text": "sequence-logo-basic · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Arial, Helvetica, sans-serif", "color": "#2d3436"},
        "x": 0.5,
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Position", "font": {"size": 22, "color": "#2d3436"}, "standoff": 12},
        "tickfont": {"size": 18, "color": "#636e72"},
        "tickvals": list(range(1, n_positions + 1)),
        "showline": True,
        "linewidth": 2,
        "linecolor": "#2d3436",
        "mirror": False,
        "showgrid": False,
        "zeroline": False,
        "ticks": "outside",
        "ticklen": 6,
        "tickwidth": 1.5,
        "tickcolor": "#636e72",
    },
    yaxis={
        "title": {"text": "Information content (bits)", "font": {"size": 22, "color": "#2d3436"}, "standoff": 10},
        "tickfont": {"size": 18, "color": "#636e72"},
        "range": [0, max_ic * 1.12],
        "showline": True,
        "linewidth": 2,
        "linecolor": "#2d3436",
        "mirror": False,
        "gridwidth": 0.5,
        "gridcolor": "rgba(0,0,0,0.05)",
        "griddash": "dot",
        "zeroline": True,
        "zerolinewidth": 2,
        "zerolinecolor": "#2d3436",
        "ticks": "outside",
        "ticklen": 6,
        "tickwidth": 1.5,
        "tickcolor": "#636e72",
        "dtick": 0.2,
    },
    template="plotly_white",
    barmode="overlay",
    bargap=0,
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend={
        "font": {"size": 20, "family": "Arial Black, Impact, sans-serif"},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.04,
        "xanchor": "center",
        "x": 0.5,
        "bgcolor": "rgba(0,0,0,0)",
        "tracegroupgap": 20,
    },
    margin={"l": 90, "r": 50, "t": 120, "b": 70},
    hoverlabel={"bgcolor": "white", "bordercolor": "#636e72", "font": {"size": 14, "family": "Arial, sans-serif"}},
)

# Add a subtle annotation for the highest-conservation position
max_pos = int(np.argmax(info_content))
fig.add_annotation(
    x=max_pos + 1,
    y=info_content[max_pos] + max_ic * 0.06,
    text="▼ most conserved",
    font={"size": 13, "color": "#636e72", "family": "Arial, sans-serif"},
    showarrow=False,
    yanchor="bottom",
    xanchor="center",
)

# Save
fig.write_html("plot.html")
fig.write_image("plot.png", width=1600, height=900, scale=3)
