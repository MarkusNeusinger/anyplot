""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Single-step exothermic reaction
reactant_energy = 50.0  # kJ/mol
transition_energy = 120.0  # kJ/mol
product_energy = 20.0  # kJ/mol

# Smooth energy curve: sigmoid baseline + Gaussian barrier
reaction_coord = np.linspace(0, 1, 300)
peak_pos = 0.40
sigma = 0.11

baseline = reactant_energy + (product_energy - reactant_energy) / (1 + np.exp(-14 * (reaction_coord - 0.55)))
gaussian = np.exp(-((reaction_coord - peak_pos) ** 2) / (2 * sigma**2))
baseline_at_peak = reactant_energy + (product_energy - reactant_energy) / (1 + np.exp(-14 * (peak_pos - 0.55)))
bump_height = transition_energy - baseline_at_peak
energy = baseline + bump_height * gaussian

curve_df = pd.DataFrame({"x": reaction_coord, "y": energy})
peak_idx = int(np.argmax(energy))
actual_peak_energy = float(energy[peak_idx])
peak_x = float(reaction_coord[peak_idx])
ea_value = actual_peak_energy - reactant_energy
dh_value = reactant_energy - product_energy

# Arrow positions
ea_x = 0.16
dh_x = 0.82

# Consolidated annotation data
hlines_df = pd.DataFrame(
    {
        "x": [0.0, ea_x, ea_x, peak_x + 0.06, 0.68, 1.0],
        "y": [reactant_energy, reactant_energy, actual_peak_energy, actual_peak_energy, product_energy, product_energy],
        "group": ["reactant", "reactant", "ts", "ts", "product", "product"],
    }
)

arrows_df = pd.DataFrame(
    {
        "x": [ea_x, ea_x, dh_x, dh_x],
        "y": [reactant_energy, actual_peak_energy, product_energy, reactant_energy],
        "x2": [ea_x, ea_x, dh_x, dh_x],
        "y2": [actual_peak_energy, reactant_energy, reactant_energy, product_energy],
        "color_key": ["ea", "ea", "dh", "dh"],
    }
)

# Shared scales
x_scale = alt.Scale(domain=[-0.04, 1.06], nice=False)
y_scale = alt.Scale(domain=[0, 140])

# Color definitions
ea_color = "#C46210"
dh_color = "#2E8B57"
curve_color = "#306998"
label_color = "#2C3E50"

# Energy curve with gradient-like opacity via condition
curve = (
    alt.Chart(curve_df)
    .mark_line(strokeWidth=4, color=curve_color)
    .encode(
        x=alt.X("x:Q", scale=x_scale, title="Reaction Coordinate"),
        y=alt.Y("y:Q", scale=y_scale, title="Energy (kJ/mol)"),
        tooltip=[
            alt.Tooltip("x:Q", title="Reaction Coordinate", format=".2f"),
            alt.Tooltip("y:Q", title="Energy (kJ/mol)", format=".1f"),
        ],
    )
)

# Horizontal dashed reference lines
hlines = (
    alt.Chart(hlines_df)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color="#aaaaaa", opacity=0.7)
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), detail="group:N")
)

# Ea vertical arrow line + arrowheads
ea_line = (
    alt.Chart(pd.DataFrame({"x": [ea_x, ea_x], "y": [reactant_energy, actual_peak_energy]}))
    .mark_line(strokeWidth=2.5, color=ea_color)
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale))
)
ea_heads = (
    alt.Chart(
        pd.DataFrame(
            {"x": [ea_x, ea_x], "y": [actual_peak_energy, reactant_energy], "shape": ["triangle-up", "triangle-down"]}
        )
    )
    .mark_point(filled=True, size=220, color=ea_color)
    .encode(
        x=alt.X("x:Q", scale=x_scale),
        y=alt.Y("y:Q", scale=y_scale),
        shape=alt.Shape("shape:N", scale=alt.Scale(range=["triangle-up", "triangle-down"]), legend=None),
    )
)

# Delta H vertical arrow line + arrowheads
dh_line = (
    alt.Chart(pd.DataFrame({"x": [dh_x, dh_x], "y": [product_energy, reactant_energy]}))
    .mark_line(strokeWidth=2.5, color=dh_color)
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale))
)
dh_heads = (
    alt.Chart(
        pd.DataFrame(
            {"x": [dh_x, dh_x], "y": [reactant_energy, product_energy], "shape": ["triangle-up", "triangle-down"]}
        )
    )
    .mark_point(filled=True, size=220, color=dh_color)
    .encode(
        x=alt.X("x:Q", scale=x_scale),
        y=alt.Y("y:Q", scale=y_scale),
        shape=alt.Shape("shape:N", scale=alt.Scale(range=["triangle-up", "triangle-down"]), legend=None),
    )
)

# Small dashed tick marks at delta H endpoints
dh_ticks_df = pd.DataFrame(
    {
        "x": [dh_x - 0.03, dh_x + 0.03, dh_x - 0.03, dh_x + 0.03],
        "y": [reactant_energy, reactant_energy, product_energy, product_energy],
        "group": ["r", "r", "p", "p"],
    }
)
dh_ticks = (
    alt.Chart(dh_ticks_df)
    .mark_line(strokeWidth=1.2, strokeDash=[5, 4], color="#bbbbbb")
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), detail="group:N")
)

# Chemical species labels (bold, dark)
species_df = pd.DataFrame(
    {
        "x": [0.06, peak_x, 0.92],
        "y": [reactant_energy - 9, actual_peak_energy + 9, product_energy - 9],
        "text": ["Reactants", "Transition State ‡", "Products"],
    }
)
species_labels = (
    alt.Chart(species_df)
    .mark_text(fontSize=22, fontWeight="bold", color=label_color)
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="text:N")
)

# Arrow value labels (bold, colored)
arrow_labels_df = pd.DataFrame(
    {
        "x": [ea_x + 0.035, dh_x + 0.04],
        "y": [(reactant_energy + actual_peak_energy) / 2, (reactant_energy + product_energy) / 2],
        "text": [f"Ea = {ea_value:.0f} kJ/mol", f"ΔH = −{dh_value:.0f} kJ/mol"],
        "color": [ea_color, dh_color],
    }
)
arrow_labels = (
    alt.Chart(arrow_labels_df)
    .mark_text(fontSize=19, fontWeight="bold", align="left")
    .encode(
        x=alt.X("x:Q", scale=x_scale),
        y=alt.Y("y:Q", scale=y_scale),
        text="text:N",
        color=alt.Color("color:N", scale=None),
    )
)

# Energy value annotations (italic, gray)
energy_vals_df = pd.DataFrame(
    {
        "x": [0.0, 1.0, peak_x + 0.09],
        "y": [reactant_energy + 6, product_energy + 6, actual_peak_energy + 2],
        "text": [f"{reactant_energy:.0f} kJ/mol", f"{product_energy:.0f} kJ/mol", f"{actual_peak_energy:.0f} kJ/mol"],
        "align": ["left", "right", "left"],
    }
)
energy_vals = (
    alt.Chart(energy_vals_df)
    .mark_text(fontSize=16, fontStyle="italic", color="#666666")
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale), text="text:N")
)

# Combine all layers
chart = (
    alt.layer(hlines, curve, ea_line, ea_heads, dh_line, dh_heads, dh_ticks, species_labels, arrow_labels, energy_vals)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "line-reaction-coordinate · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            color=label_color,
            subtitle="Exothermic Reaction · Single-Step Energy Profile",
            subtitleFontSize=18,
            subtitleColor="#7f8c8d",
            subtitlePadding=8,
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleFont="Helvetica Neue, Arial, sans-serif",
        labelFont="Helvetica Neue, Arial, sans-serif",
        titleColor="#333333",
        labelColor="#555555",
        grid=False,
        domainColor="#aaaaaa",
        domainWidth=0.8,
        tickColor="#aaaaaa",
        tickSize=5,
        tickWidth=0.6,
        tickCount=6,
    )
    .configure_title(font="Helvetica Neue, Arial, sans-serif", color="#222222")
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
