""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-21
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

curve_df = pd.DataFrame({"Reaction Coordinate": reaction_coord, "Energy (kJ/mol)": energy})

peak_idx = np.argmax(energy)
actual_peak_energy = energy[peak_idx]
peak_x = reaction_coord[peak_idx]

# Horizontal dashed lines extending to Ea arrow position
ea_x = 0.18
reactant_line_df = pd.DataFrame(
    {"Reaction Coordinate": [0.0, ea_x], "Energy (kJ/mol)": [reactant_energy, reactant_energy]}
)
# Extended reactant dashed line from Ea arrow to past the peak for reference
reactant_ext_df = pd.DataFrame(
    {"Reaction Coordinate": [ea_x, peak_x + 0.06], "Energy (kJ/mol)": [reactant_energy, reactant_energy]}
)
product_line_df = pd.DataFrame(
    {"Reaction Coordinate": [0.68, 1.0], "Energy (kJ/mol)": [product_energy, product_energy]}
)

# Horizontal dashed line at transition state level
ts_line_df = pd.DataFrame(
    {"Reaction Coordinate": [ea_x, peak_x + 0.06], "Energy (kJ/mol)": [actual_peak_energy, actual_peak_energy]}
)

# Ea arrow (vertical double-headed arrow from reactant level to TS level)
ea_line_df = pd.DataFrame(
    {"Reaction Coordinate": [ea_x, ea_x], "Energy (kJ/mol)": [reactant_energy, actual_peak_energy]}
)

# Delta H arrow (vertical double-headed arrow from reactant to product level)
dh_x = 0.82
dh_line_df = pd.DataFrame({"Reaction Coordinate": [dh_x, dh_x], "Energy (kJ/mol)": [product_energy, reactant_energy]})

# Dashed extension lines for delta H
dh_reactant_ext_df = pd.DataFrame(
    {"Reaction Coordinate": [dh_x - 0.04, dh_x + 0.04], "Energy (kJ/mol)": [reactant_energy, reactant_energy]}
)
dh_product_ext_df = pd.DataFrame(
    {"Reaction Coordinate": [dh_x - 0.04, dh_x + 0.04], "Energy (kJ/mol)": [product_energy, product_energy]}
)

# Shared scales
x_scale = alt.Scale(domain=[-0.08, 1.12], nice=False)
y_scale = alt.Scale(domain=[-5, 135])

# Energy curve
curve = (
    alt.Chart(curve_df)
    .mark_line(strokeWidth=4, color="#306998")
    .encode(
        x=alt.X("Reaction Coordinate:Q", scale=x_scale, title="Reaction Coordinate"),
        y=alt.Y("Energy (kJ/mol):Q", scale=y_scale, title="Energy (kJ/mol)"),
        tooltip=[alt.Tooltip("Reaction Coordinate:Q", format=".2f"), alt.Tooltip("Energy (kJ/mol):Q", format=".1f")],
    )
)

# Horizontal dashed lines at reactant and product levels
reactant_hline = (
    alt.Chart(reactant_line_df)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color="#999999")
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)
reactant_ext = (
    alt.Chart(reactant_ext_df)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color="#999999")
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)
product_hline = (
    alt.Chart(product_line_df)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color="#999999")
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)
ts_hline = (
    alt.Chart(ts_line_df)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color="#999999")
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)

# Ea vertical arrow
ea_color = "#C46210"
ea_line = (
    alt.Chart(ea_line_df)
    .mark_line(strokeWidth=2.5, color=ea_color)
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)
ea_arrow_top = (
    alt.Chart(pd.DataFrame({"Reaction Coordinate": [ea_x], "Energy (kJ/mol)": [actual_peak_energy]}))
    .mark_point(shape="triangle-up", filled=True, size=200, color=ea_color)
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)
ea_arrow_bottom = (
    alt.Chart(pd.DataFrame({"Reaction Coordinate": [ea_x], "Energy (kJ/mol)": [reactant_energy]}))
    .mark_point(shape="triangle-down", filled=True, size=200, color=ea_color)
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)

# Ea label
ea_label_df = pd.DataFrame(
    {
        "Reaction Coordinate": [ea_x + 0.03],
        "Energy (kJ/mol)": [(reactant_energy + actual_peak_energy) / 2],
        "text": [f"Ea = {actual_peak_energy - reactant_energy:.0f} kJ/mol"],
    }
)
ea_label = (
    alt.Chart(ea_label_df)
    .mark_text(fontSize=18, align="left", fontWeight="bold", color=ea_color)
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale), text="text:N")
)

# Delta H vertical arrow
dh_color = "#2E8B57"
dh_line = (
    alt.Chart(dh_line_df)
    .mark_line(strokeWidth=2.5, color=dh_color)
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)
dh_arrow_top = (
    alt.Chart(pd.DataFrame({"Reaction Coordinate": [dh_x], "Energy (kJ/mol)": [reactant_energy]}))
    .mark_point(shape="triangle-up", filled=True, size=200, color=dh_color)
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)
dh_arrow_bottom = (
    alt.Chart(pd.DataFrame({"Reaction Coordinate": [dh_x], "Energy (kJ/mol)": [product_energy]}))
    .mark_point(shape="triangle-down", filled=True, size=200, color=dh_color)
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)
dh_reactant_ext = (
    alt.Chart(dh_reactant_ext_df)
    .mark_line(strokeWidth=1.5, strokeDash=[6, 4], color="#bbbbbb")
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)
dh_product_ext = (
    alt.Chart(dh_product_ext_df)
    .mark_line(strokeWidth=1.5, strokeDash=[6, 4], color="#bbbbbb")
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale))
)

# Delta H label
dh_label_df = pd.DataFrame(
    {
        "Reaction Coordinate": [dh_x + 0.04],
        "Energy (kJ/mol)": [(reactant_energy + product_energy) / 2],
        "text": [f"\u0394H = \u2212{reactant_energy - product_energy:.0f} kJ/mol"],
    }
)
dh_label = (
    alt.Chart(dh_label_df)
    .mark_text(fontSize=18, align="left", fontWeight="bold", color=dh_color)
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale), text="text:N")
)

# Labels for reactants, transition state, products
labels_df = pd.DataFrame(
    {
        "Reaction Coordinate": [0.06, peak_x, 0.90],
        "Energy (kJ/mol)": [reactant_energy - 8, actual_peak_energy + 8, product_energy - 8],
        "text": ["Reactants", "Transition State \u2021", "Products"],
    }
)
chem_labels = (
    alt.Chart(labels_df)
    .mark_text(fontSize=20, fontWeight="bold", color="#2C3E50")
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale), text="text:N")
)

# Energy value labels
energy_labels_df = pd.DataFrame(
    {
        "Reaction Coordinate": [0.0, 1.0, peak_x + 0.08],
        "Energy (kJ/mol)": [reactant_energy + 5, product_energy + 5, actual_peak_energy + 1],
        "text": [f"{reactant_energy:.0f} kJ/mol", f"{product_energy:.0f} kJ/mol", f"{actual_peak_energy:.0f} kJ/mol"],
    }
)
energy_labels = (
    alt.Chart(energy_labels_df)
    .mark_text(fontSize=14, color="#777777", fontStyle="italic")
    .encode(x=alt.X("Reaction Coordinate:Q", scale=x_scale), y=alt.Y("Energy (kJ/mol):Q", scale=y_scale), text="text:N")
)

# Combine all layers
chart = (
    alt.layer(
        reactant_hline,
        reactant_ext,
        product_hline,
        ts_hline,
        curve,
        ea_line,
        ea_arrow_top,
        ea_arrow_bottom,
        ea_label,
        dh_line,
        dh_arrow_top,
        dh_arrow_bottom,
        dh_reactant_ext,
        dh_product_ext,
        dh_label,
        chem_labels,
        energy_labels,
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "line-reaction-coordinate \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            anchor="middle",
            color="#2C3E50",
            subtitle="Exothermic Reaction \u00b7 Single-Step Energy Profile",
            subtitleFontSize=16,
            subtitleColor="#7f8c8d",
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
        domainWidth=0.6,
        tickColor="#aaaaaa",
        tickSize=5,
        tickWidth=0.6,
    )
    .configure_title(font="Helvetica Neue, Arial, sans-serif", color="#222222")
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
