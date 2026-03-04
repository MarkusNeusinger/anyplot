"""pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-04
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

roots_of_unity = [np.exp(2j * np.pi * k / 5) for k in range(5)]
root_labels = [f"ω{k}" for k in range(5)]

arbitrary_points = [2.5 + 1.5j, -1.8 + 2.2j, -0.5 - 1.7j, 1.2 - 2.0j, 3.0 + 0j]
arbitrary_labels = ["z₁", "z₂", "z₃", "z₄", "z₅"]

conjugate_pair = [1.5 + 2j, 1.5 - 2j]
conjugate_labels = ["w", "w̄"]

all_points = roots_of_unity + arbitrary_points + conjugate_pair
all_labels = root_labels + arbitrary_labels + conjugate_labels
categories = (
    ["5th Roots of Unity"] * len(roots_of_unity)
    + ["Arbitrary Points"] * len(arbitrary_points)
    + ["Conjugate Pair"] * len(conjugate_pair)
)

real_parts = [z.real for z in all_points]
imag_parts = [z.imag for z in all_points]


def format_complex(r, im):
    """Format a+bi string for annotation."""
    if im == 0:
        return f"{r:.1f}"
    sign = "+" if im > 0 else "−"
    return f"{r:.1f} {sign} {abs(im):.1f}i"


# Colors
palette = {"5th Roots of Unity": "#306998", "Arbitrary Points": "#E8833A", "Conjugate Pair": "#7B4F9D"}

# Custom text positions to avoid overlap
text_offsets = dict.fromkeys(all_labels, "top right")
# Fix overlapping labels: z₄ at (1.2, -2.0) and w̄ at (1.5, -2.0)
text_offsets["z₄"] = "bottom left"
text_offsets["w̄"] = "top right"
# Avoid crowding near origin for roots of unity
text_offsets["ω2"] = "top left"
text_offsets["ω3"] = "bottom left"

# Plot
fig = go.Figure()

# Unit circle as a shape (not a trace) to keep legend clean
theta = np.linspace(0, 2 * np.pi, 200)
fig.add_trace(
    go.Scatter(
        x=np.cos(theta).tolist(),
        y=np.sin(theta).tolist(),
        mode="lines",
        line={"color": "#999999", "width": 2, "dash": "dash"},
        name="Unit Circle",
        hoverinfo="skip",
        showlegend=False,
    )
)

# Add "r=1" label on the unit circle
fig.add_annotation(
    x=np.cos(np.pi / 4),
    y=np.sin(np.pi / 4),
    text="r = 1",
    showarrow=False,
    font={"size": 14, "color": "#777777", "family": "serif"},
    xshift=12,
    yshift=10,
)

for cat in ["5th Roots of Unity", "Arbitrary Points", "Conjugate Pair"]:
    cat_indices = [i for i, c in enumerate(categories) if c == cat]
    cat_real = [real_parts[i] for i in cat_indices]
    cat_imag = [imag_parts[i] for i in cat_indices]
    cat_labels = [all_labels[i] for i in cat_indices]
    cat_points = [all_points[i] for i in cat_indices]
    color = palette[cat]

    # Vector arrows from origin
    for r, im in zip(cat_real, cat_imag, strict=True):
        fig.add_annotation(
            x=r,
            y=im,
            ax=0,
            ay=0,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1.2,
            arrowwidth=2.5,
            arrowcolor=color,
            opacity=0.5,
        )

    # Visible a+bi annotations for each point
    for r, im, label in zip(cat_real, cat_imag, cat_labels, strict=True):
        pos = text_offsets.get(label, "top right")
        xshift = -8 if "left" in pos else 8
        yshift = -14 if "bottom" in pos else 14
        fig.add_annotation(
            x=r,
            y=im,
            text=f"<b>{label}</b>  ({format_complex(r, im)})",
            showarrow=False,
            font={"size": 13, "color": color, "family": "serif"},
            xanchor="left" if "right" in pos else "right",
            yanchor="bottom" if "top" in pos else "top",
            xshift=xshift,
            yshift=yshift,
        )

    # Custom hover template with Plotly-specific hovertemplate
    hover_custom = [
        f"<b>{label}</b><br>"
        f"z = {format_complex(r, im)}<br>"
        f"|z| = {abs(z):.3f}<br>"
        f"arg(z) = {np.degrees(np.angle(z)):.1f}°"
        for r, im, label, z in zip(cat_real, cat_imag, cat_labels, cat_points, strict=True)
    ]

    fig.add_trace(
        go.Scatter(
            x=cat_real,
            y=cat_imag,
            mode="markers",
            marker={"size": 16, "color": color, "line": {"color": "white", "width": 2}, "symbol": "circle"},
            name=cat,
            hovertext=hover_custom,
            hoverinfo="text",
        )
    )

# Style
fig.update_layout(
    title={"text": "scatter-complex-plane · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Re(z)", "font": {"size": 22, "family": "serif"}},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 2,
        "zerolinecolor": "#444444",
        "gridcolor": "rgba(0,0,0,0.08)",
        "showgrid": True,
        "dtick": 1,
        "range": [-3.5, 4],
    },
    yaxis={
        "title": {"text": "Im(z)", "font": {"size": 22, "family": "serif"}},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 2,
        "zerolinecolor": "#444444",
        "gridcolor": "rgba(0,0,0,0.08)",
        "showgrid": True,
        "scaleanchor": "x",
        "scaleratio": 1,
        "dtick": 1,
        "range": [-3.5, 3.5],
    },
    template="plotly_white",
    plot_bgcolor="white",
    legend={
        "font": {"size": 16},
        "x": 0.01,
        "y": 0.99,
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
    },
    width=1200,
    height=1200,
    margin={"l": 80, "r": 80, "t": 100, "b": 80},
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
