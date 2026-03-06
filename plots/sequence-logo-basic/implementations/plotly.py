""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-06
"""

import numpy as np
import plotly.graph_objects as go


# Data - transcription factor binding site motif (10-position DNA)
# Position weight matrix: each row is [A, C, G, T] frequencies
pwm = np.array(
    [
        [0.05, 0.80, 0.05, 0.10],  # pos 1: C dominant
        [0.10, 0.15, 0.10, 0.65],  # pos 2: T dominant
        [0.02, 0.96, 0.01, 0.01],  # pos 3: C highly conserved (~1.8 bits)
        [0.25, 0.25, 0.25, 0.25],  # pos 4: uniform (0 bits)
        [0.70, 0.05, 0.15, 0.10],  # pos 5: A dominant
        [0.10, 0.10, 0.70, 0.10],  # pos 6: G dominant
        [0.001, 0.001, 0.001, 0.997],  # pos 7: T near-perfect conservation (~1.97 bits)
        [0.60, 0.15, 0.15, 0.10],  # pos 8: A dominant
        [0.10, 0.10, 0.65, 0.15],  # pos 9: G dominant
        [0.15, 0.55, 0.10, 0.20],  # pos 10: C dominant
    ]
)

letters = ["A", "C", "G", "T"]
# Standard DNA sequence logo colors: A=green, C=blue, G=orange, T=red
# Using colorblind-safe Wong palette variants
colors = {"A": "#009E73", "C": "#0072B2", "G": "#E69F00", "T": "#D55E00"}
n_positions = len(pwm)

# Information content: IC = 2 + sum(f * log2(f)) for DNA (max 2 bits)
info_content = np.zeros(n_positions)
for i in range(n_positions):
    entropy = sum(f * np.log2(f) for f in pwm[i] if f > 0)
    info_content[i] = max(0, 2.0 + entropy)

# Letter heights = frequency * information content at each position
letter_heights = pwm * info_content[:, np.newaxis]

# SVG path data for letters (simplified block-style glyphs within 0-1 x 0-1 box)
letter_paths = {
    "A": "M 0.5 0 L 0.05 1 L 0.25 1 L 0.35 0.7 L 0.65 0.7 L 0.75 1 L 0.95 1 L 0.5 0 Z M 0.4 0.52 L 0.6 0.52 L 0.55 0.38 L 0.45 0.38 Z",
    "C": "M 0.85 0.2 C 0.65 -0.05 0.2 0 0.1 0.3 C 0 0.6 0.15 0.95 0.5 1 C 0.7 1.02 0.85 0.9 0.88 0.8 L 0.68 0.7 C 0.6 0.82 0.5 0.82 0.4 0.78 C 0.28 0.7 0.25 0.5 0.3 0.35 C 0.35 0.2 0.5 0.15 0.6 0.18 C 0.68 0.2 0.72 0.28 0.75 0.32 Z",
    "G": "M 0.85 0.2 C 0.65 -0.05 0.2 0 0.1 0.3 C 0 0.6 0.15 0.95 0.5 1 C 0.7 1.02 0.85 0.9 0.88 0.8 L 0.68 0.7 C 0.6 0.82 0.5 0.82 0.4 0.78 C 0.28 0.7 0.25 0.5 0.3 0.35 C 0.35 0.2 0.5 0.15 0.6 0.18 C 0.68 0.2 0.72 0.28 0.75 0.32 L 0.85 0.2 Z M 0.55 0.45 L 0.85 0.45 L 0.85 0.55 L 0.55 0.55 Z",
    "T": "M 0.05 0 L 0.05 0.18 L 0.38 0.18 L 0.38 1 L 0.62 1 L 0.62 0.18 L 0.95 0.18 L 0.95 0 Z",
}

# Plot - using Plotly shapes for stretched letter glyphs
fig = go.Figure()
bar_width = 0.38  # half-width for shapes

# Build letter shapes at each position
for pos in range(n_positions):
    heights = letter_heights[pos]
    sorted_indices = np.argsort(heights)
    y_bottom = 0

    for idx in sorted_indices:
        h = heights[idx]
        if h < 0.005:
            continue
        letter = letters[idx]

        # Add invisible bar for hover interaction
        fig.add_trace(
            go.Bar(
                x=[pos + 1],
                y=[h],
                base=y_bottom,
                width=bar_width * 2,
                marker={"color": "rgba(0,0,0,0)", "line": {"width": 0}},
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

        # Transform SVG path from 0-1 space to data coordinates (inline)
        tokens = letter_paths[letter].split()
        path_parts = []
        ti = 0
        while ti < len(tokens):
            cmd = tokens[ti]
            if cmd in ("M", "L", "Z"):
                path_parts.append(cmd)
                if cmd != "Z":
                    px = float(tokens[ti + 1])
                    py = float(tokens[ti + 2])
                    path_parts.append(str((pos + 1) - bar_width + px * 2 * bar_width))
                    path_parts.append(str(y_bottom + py * h))
                    ti += 3
                else:
                    ti += 1
            elif cmd == "C":
                path_parts.append(cmd)
                for j in range(3):
                    px = float(tokens[ti + 1 + j * 2])
                    py = float(tokens[ti + 2 + j * 2])
                    path_parts.append(str((pos + 1) - bar_width + px * 2 * bar_width))
                    path_parts.append(str(y_bottom + py * h))
                ti += 7
            else:
                ti += 1
        path_data = " ".join(path_parts)

        fig.add_shape(
            type="path",
            path=path_data,
            fillcolor=colors[letter],
            line={"width": 0.5, "color": colors[letter]},
            layer="above",
            xref="x",
            yref="y",
        )

        y_bottom += h

# Legend entries
for letter in letters:
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 18, "color": colors[letter], "symbol": "square"},
            name=f"  {letter}  ",
            showlegend=True,
        )
    )

# Style
fig.update_layout(
    title={
        "text": "sequence-logo-basic · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Arial, Helvetica, sans-serif", "color": "#1a1a2e"},
        "x": 0.5,
        "y": 0.96,
    },
    xaxis={
        "title": {
            "text": "Position",
            "font": {"size": 22, "color": "#1a1a2e", "family": "Arial, sans-serif"},
            "standoff": 12,
        },
        "tickfont": {"size": 18, "color": "#4a4a68", "family": "Arial, sans-serif"},
        "tickvals": list(range(1, n_positions + 1)),
        "showline": True,
        "linewidth": 2,
        "linecolor": "#1a1a2e",
        "mirror": False,
        "showgrid": False,
        "zeroline": False,
        "ticks": "outside",
        "ticklen": 8,
        "tickwidth": 1.5,
        "tickcolor": "#4a4a68",
    },
    yaxis={
        "title": {
            "text": "Information content (bits)",
            "font": {"size": 22, "color": "#1a1a2e", "family": "Arial, sans-serif"},
            "standoff": 10,
        },
        "tickfont": {"size": 18, "color": "#4a4a68", "family": "Arial, sans-serif"},
        "range": [0, 2.15],
        "showline": True,
        "linewidth": 2,
        "linecolor": "#1a1a2e",
        "mirror": False,
        "gridwidth": 0.5,
        "gridcolor": "rgba(100,100,140,0.08)",
        "griddash": "dot",
        "zeroline": True,
        "zerolinewidth": 2,
        "zerolinecolor": "#1a1a2e",
        "ticks": "outside",
        "ticklen": 8,
        "tickwidth": 1.5,
        "tickcolor": "#4a4a68",
        "dtick": 0.5,
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
    hoverlabel={"bgcolor": "white", "bordercolor": "#4a4a68", "font": {"size": 15, "family": "Arial, sans-serif"}},
)

# Annotate highly conserved positions with larger, more prominent labels
conserved_positions = [2, 6]  # positions 3 and 7 (0-indexed)
for pos_idx in conserved_positions:
    ic_val = info_content[pos_idx]
    fig.add_annotation(
        x=pos_idx + 1,
        y=ic_val + 0.08,
        text=f"▼ {ic_val:.2f} bits",
        font={
            "size": 16,
            "color": "#1a1a2e",
            "family": "Arial, sans-serif",
            "weight": "bold" if ic_val > 1.9 else "normal",
        },
        showarrow=False,
        yanchor="bottom",
        xanchor="center",
    )

# Add subtle annotation for the zero-information position
fig.add_annotation(
    x=4,
    y=-0.08,
    text="no signal",
    font={"size": 13, "color": "#999999", "family": "Arial, sans-serif"},
    showarrow=False,
    yanchor="top",
    xanchor="center",
)

# Save
fig.write_html("plot.html")
fig.write_image("plot.png", width=1600, height=900, scale=3)
