"""pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: altair | Python 3.13
Quality: pending | Created: 2026-02-27
"""

import altair as alt
import pandas as pd


# Data - Hydrogen atom energy levels: E_n = -13.6 / n² eV
levels = {n: -13.6 / n**2 for n in range(1, 7)}

# Stagger line endpoints to avoid label overlap on closely spaced upper levels
line_ends = {1: 9.0, 2: 9.0, 3: 9.0, 4: 8.0, 5: 9.0, 6: 8.0}

level_df = pd.DataFrame(
    [{"energy": levels[n], "x_start": 1.5, "x_end": line_ends[n], "label": f"n = {n}"} for n in range(1, 7)]
)

ionization_df = pd.DataFrame([{"energy": 0.0, "x_start": 1.5, "x_end": 9.0, "label": "n = \u221e"}])

all_labels_df = pd.concat([level_df, ionization_df], ignore_index=True)

# Spectral series transitions (emission: upper → lower)
transition_data = [
    # Lyman series (UV) - transitions to n=1
    (2, 1, "Lyman (UV)", 2.5),
    (3, 1, "Lyman (UV)", 3.1),
    (4, 1, "Lyman (UV)", 3.7),
    # Balmer series (Visible) - transitions to n=2
    (3, 2, "Balmer (Visible)", 4.8),
    (4, 2, "Balmer (Visible)", 5.4),
    (5, 2, "Balmer (Visible)", 6.0),
    # Paschen series (IR) - transitions to n=3
    (4, 3, "Paschen (IR)", 6.8),
    (5, 3, "Paschen (IR)", 7.2),
    (6, 3, "Paschen (IR)", 7.6),
]

arrow_df = pd.DataFrame(
    [
        {"x": x, "y_upper": levels[up], "y_lower": levels[lo], "series": s, "transition": f"n={up} \u2192 n={lo}"}
        for up, lo, s, x in transition_data
    ]
)

head_df = pd.DataFrame([{"x": x, "y": levels[lo], "series": s} for up, lo, s, x in transition_data])

series_order = ["Lyman (UV)", "Balmer (Visible)", "Paschen (IR)"]
series_colors = ["#306998", "#E69F00", "#CC79A7"]

# Layer 1: Energy level lines
energy_lines = (
    alt.Chart(level_df)
    .mark_rule(strokeWidth=3, color="#2C3E50")
    .encode(
        x=alt.X("x_start:Q", scale=alt.Scale(domain=[0, 11]), axis=None),
        x2="x_end:Q",
        y=alt.Y(
            "energy:Q",
            title="Energy (eV)",
            scale=alt.Scale(domain=[-15, 1.5]),
            axis=alt.Axis(
                titleFontSize=22, labelFontSize=18, titlePadding=15, values=[-14, -12, -10, -8, -6, -4, -2, 0]
            ),
        ),
        tooltip=[alt.Tooltip("label:N", title="Level"), alt.Tooltip("energy:Q", title="Energy (eV)", format=".2f")],
    )
)

# Layer 2: Ionization limit (dashed line)
ion_line = (
    alt.Chart(ionization_df)
    .mark_rule(strokeWidth=2, strokeDash=[10, 6], color="#999999")
    .encode(x="x_start:Q", x2="x_end:Q", y="energy:Q")
)

# Layer 3: Quantum number labels at line endpoints
level_labels = (
    alt.Chart(all_labels_df)
    .mark_text(align="left", baseline="middle", fontSize=18, dx=8, fontWeight="bold", color="#2C3E50")
    .encode(x="x_end:Q", y="energy:Q", text="label:N")
)

# Layer 4: Transition arrow shafts
arrow_shafts = (
    alt.Chart(arrow_df)
    .mark_rule(strokeWidth=3, opacity=0.85)
    .encode(
        x="x:Q",
        y="y_upper:Q",
        y2="y_lower:Q",
        color=alt.Color(
            "series:N",
            scale=alt.Scale(domain=series_order, range=series_colors),
            legend=alt.Legend(title="Spectral Series", titleFontSize=18, labelFontSize=16, symbolSize=200),
        ),
        tooltip=["transition:N", "series:N"],
    )
)

# Layer 5: Arrowheads (emission = pointing down)
arrowheads = (
    alt.Chart(head_df)
    .mark_point(shape="triangle-down", filled=True, size=300, opacity=0.85)
    .encode(
        x="x:Q",
        y="y:Q",
        color=alt.Color("series:N", scale=alt.Scale(domain=series_order, range=series_colors), legend=None),
    )
)

# Combine all layers
chart = (
    alt.layer(energy_lines, ion_line, level_labels, arrow_shafts, arrowheads)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("energy-level-atomic \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
    .configure_axisY(gridOpacity=0.15)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
