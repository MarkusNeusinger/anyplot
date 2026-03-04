"""pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-04
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

# Sum example: z₁ + z₂ to demonstrate complex addition (spec mentions sums)
z_sum = arbitrary_points[0] + arbitrary_points[1]
sum_points = [z_sum]
sum_labels = ["z₁+z₂"]

all_points = roots_of_unity + arbitrary_points + conjugate_pair + sum_points
all_labels = root_labels + arbitrary_labels + conjugate_labels + sum_labels
categories = (
    ["5th Roots of Unity"] * len(roots_of_unity)
    + ["Arbitrary Points"] * len(arbitrary_points)
    + ["Conjugate Pair"] * len(conjugate_pair)
    + ["Sum (z₁+z₂)"] * len(sum_points)
)

real_parts = [z.real for z in all_points]
imag_parts = [z.imag for z in all_points]

# Colors — 4-category colorblind-safe palette starting with Python Blue
palette = {
    "5th Roots of Unity": "#306998",
    "Arbitrary Points": "#E8833A",
    "Conjugate Pair": "#7B4F9D",
    "Sum (z₁+z₂)": "#2CA02C",
}

# Marker sizes per category for visual hierarchy
marker_sizes = {"5th Roots of Unity": 14, "Arbitrary Points": 16, "Conjugate Pair": 16, "Sum (z₁+z₂)": 20}

# Custom text positions to avoid overlap
text_offsets = dict.fromkeys(all_labels, "top right")
text_offsets["z₄"] = "bottom left"
text_offsets["w̄"] = "bottom right"
text_offsets["ω2"] = "top left"
text_offsets["ω3"] = "bottom left"
text_offsets["ω4"] = "bottom right"
text_offsets["z₁+z₂"] = "top left"
text_offsets["z₃"] = "bottom right"

# Plot
fig = go.Figure()

# Unit circle (dashed reference)
theta = np.linspace(0, 2 * np.pi, 200)
fig.add_trace(
    go.Scatter(
        x=np.cos(theta).tolist(),
        y=np.sin(theta).tolist(),
        mode="lines",
        line={"color": "#BBBBBB", "width": 2, "dash": "dash"},
        name="Unit Circle",
        hoverinfo="skip",
        showlegend=False,
    )
)

# "r=1" label repositioned to ~70° to avoid ω1 crowding
fig.add_annotation(
    x=np.cos(np.pi * 70 / 180),
    y=np.sin(np.pi * 70 / 180),
    text="<i>r</i> = 1",
    showarrow=False,
    font={"size": 14, "color": "#999999", "family": "serif"},
    xshift=-20,
    yshift=14,
)

# Dashed lines from z₁ and z₂ to z₁+z₂ to show addition (parallelogram rule)
for src in [arbitrary_points[0], arbitrary_points[1]]:
    fig.add_trace(
        go.Scatter(
            x=[src.real, z_sum.real],
            y=[src.imag, z_sum.imag],
            mode="lines",
            line={"color": "#2CA02C", "width": 1.5, "dash": "dot"},
            hoverinfo="skip",
            showlegend=False,
        )
    )

for cat in ["5th Roots of Unity", "Arbitrary Points", "Conjugate Pair", "Sum (z₁+z₂)"]:
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
            opacity=0.65,
        )

    # Annotations with a+bi form (inline formatting, no helper function)
    for r, im, label in zip(cat_real, cat_imag, cat_labels, strict=True):
        pos = text_offsets.get(label, "top right")
        xshift = -10 if "left" in pos else 10
        yshift = -16 if "bottom" in pos else 16
        sign = "+" if im >= 0 else "−"
        complex_str = f"{r:.1f}" if im == 0 else f"{r:.1f} {sign} {abs(im):.1f}i"
        fig.add_annotation(
            x=r,
            y=im,
            text=f"<b>{label}</b>  ({complex_str})",
            showarrow=False,
            font={"size": 15, "color": color, "family": "serif"},
            xanchor="left" if "right" in pos else "right",
            yanchor="bottom" if "top" in pos else "top",
            xshift=xshift,
            yshift=yshift,
        )

    # Scatter trace with hovertemplate (idiomatic Plotly)
    magnitudes = [abs(z) for z in cat_points]
    phases = [np.degrees(np.angle(z)) for z in cat_points]
    fig.add_trace(
        go.Scatter(
            x=cat_real,
            y=cat_imag,
            mode="markers",
            marker={
                "size": marker_sizes[cat],
                "color": color,
                "line": {"color": "white", "width": 2},
                "symbol": "circle",
            },
            name=cat,
            customdata=list(zip(cat_labels, magnitudes, phases, strict=True)),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Re: %{x:.2f}<br>"
                "Im: %{y:.2f}<br>"
                "|z| = %{customdata[1]:.3f}<br>"
                "arg(z) = %{customdata[2]:.1f}°"
                "<extra>%{fullData.name}</extra>"
            ),
        )
    )

# Layout
fig.update_layout(
    title={
        "text": (
            "scatter-complex-plane · plotly · pyplots.ai"
            "<br><sup style='color:#888; font-weight:normal'>"
            "Argand diagram — roots of unity, conjugates & vector addition"
            "</sup>"
        ),
        "font": {"size": 28, "family": "serif"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Re(z)", "font": {"size": 22, "family": "serif"}},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 2.5,
        "zerolinecolor": "#333333",
        "gridcolor": "rgba(0,0,0,0.06)",
        "showgrid": True,
        "dtick": 1,
        "range": [-3.5, 4.5],
    },
    yaxis={
        "title": {"text": "Im(z)", "font": {"size": 22, "family": "serif"}},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 2.5,
        "zerolinecolor": "#333333",
        "gridcolor": "rgba(0,0,0,0.06)",
        "showgrid": True,
        "scaleanchor": "x",
        "scaleratio": 1,
        "dtick": 1,
        "range": [-3.5, 4.5],
    },
    template="plotly_white",
    plot_bgcolor="white",
    legend={
        "font": {"size": 16, "family": "serif"},
        "x": 0.01,
        "y": 0.99,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.15)",
        "borderwidth": 1,
    },
    width=1200,
    height=1200,
    margin={"l": 80, "r": 80, "t": 120, "b": 80},
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
