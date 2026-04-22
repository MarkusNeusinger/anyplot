""" pyplots.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Reference impedance
Z0 = 50  # ohms

# Generate Smith chart grid - constant resistance circles
theta = np.linspace(0, 2 * np.pi, 100)

resistance_circles = []
resistance_values = [0, 0.2, 0.5, 1.0, 2.0, 5.0]
for r in resistance_values:
    center_x = r / (r + 1)
    radius = 1 / (r + 1)
    x = center_x + radius * np.cos(theta)
    y = radius * np.sin(theta)
    mask = x**2 + y**2 <= 1.0
    for i in range(len(x)):
        if mask[i]:
            resistance_circles.append({"x": x[i], "y": y[i], "group": f"r_{r}", "idx": i})

resistance_df = pd.DataFrame(resistance_circles)

# Generate constant reactance arcs
reactance_arcs = []
reactance_values = [0.2, 0.5, 1.0, 2.0, 5.0]
arc_theta = np.linspace(-np.pi, np.pi, 100)

for x_val in reactance_values:
    # Positive reactance (upper half)
    center_y = 1 / x_val
    radius = 1 / x_val
    x = 1 + radius * np.cos(arc_theta)
    y = center_y + radius * np.sin(arc_theta)
    mask = (x**2 + y**2 <= 1.0) & (x >= -0.01)
    for i in range(len(x)):
        if mask[i]:
            reactance_arcs.append({"x": x[i], "y": y[i], "group": f"x_pos_{x_val}", "idx": i})

    # Negative reactance (lower half)
    y_neg = -center_y - radius * np.sin(arc_theta)
    for i in range(len(x)):
        if mask[i]:
            reactance_arcs.append({"x": x[i], "y": y_neg[i], "group": f"x_neg_{x_val}", "idx": i})

# Zero reactance line (horizontal axis)
x_line = np.linspace(-1, 1, 50)
for i, xi in enumerate(x_line):
    reactance_arcs.append({"x": xi, "y": 0, "group": "x_zero", "idx": i})

reactance_df = pd.DataFrame(reactance_arcs)

# Unit circle boundary
unit_theta = np.linspace(0, 2 * np.pi, 100)
unit_circle_df = pd.DataFrame({"x": np.cos(unit_theta), "y": np.sin(unit_theta), "idx": range(len(unit_theta))})

# Generate sample impedance data - antenna impedance sweep from 1-6 GHz
np.random.seed(42)
n_points = 50
frequency = np.linspace(1e9, 6e9, n_points)

# Simulate antenna impedance that traces a spiral pattern on Smith chart
t = np.linspace(0, 2.5 * np.pi, n_points)
z_real = 50 * (1 - 0.7 * np.exp(-t / 3))
z_imag = 40 * np.sin(t) * np.exp(-t / 4)

# Normalize impedance and convert to reflection coefficient (gamma)
z_norm = (z_real + 1j * z_imag) / Z0
gamma = (z_norm - 1) / (z_norm + 1)

impedance_df = pd.DataFrame(
    {
        "x": gamma.real,
        "y": gamma.imag,
        "frequency_ghz": frequency / 1e9,
        "z_real": z_real,
        "z_imag": z_imag,
        "idx": range(n_points),
    }
)

# Add frequency labels at key points
label_indices = [0, 12, 24, 36, 49]
labels_df = impedance_df.iloc[label_indices].copy()
labels_df["label"] = labels_df["frequency_ghz"].apply(lambda f: f"{f:.1f} GHz")

# Scale domain for consistent axes
scale_x = alt.Scale(domain=[-1.2, 1.2])
scale_y = alt.Scale(domain=[-1.2, 1.2])

# Unit circle boundary
boundary = (
    alt.Chart(unit_circle_df)
    .mark_line(color="#306998", strokeWidth=4)
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), order="idx:O")
)

# Resistance circles
res_circles = (
    alt.Chart(resistance_df)
    .mark_line(strokeWidth=1.5, opacity=0.4, color="#666666")
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), detail="group:N", order="idx:O")
)

# Reactance arcs
react_arcs = (
    alt.Chart(reactance_df)
    .mark_line(strokeWidth=1.5, opacity=0.4, color="#888888")
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), detail="group:N", order="idx:O")
)

# Impedance locus curve
impedance_line = (
    alt.Chart(impedance_df)
    .mark_line(strokeWidth=5, color="#FFD43B")
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), order="idx:O")
)

# Impedance data points
impedance_points = (
    alt.Chart(impedance_df)
    .mark_circle(size=120, color="#FFD43B", stroke="#306998", strokeWidth=1)
    .encode(
        x=alt.X("x:Q", scale=scale_x),
        y=alt.Y("y:Q", scale=scale_y),
        tooltip=[
            alt.Tooltip("frequency_ghz:Q", title="Frequency (GHz)", format=".2f"),
            alt.Tooltip("z_real:Q", title="R (Ω)", format=".1f"),
            alt.Tooltip("z_imag:Q", title="X (Ω)", format=".1f"),
        ],
    )
)

# Frequency labels
freq_labels = (
    alt.Chart(labels_df)
    .mark_text(fontSize=18, fontWeight="bold", color="#306998", dx=18, dy=-18)
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), text="label:N")
)

# Center point marker (matched condition Z = Z0)
center_df = pd.DataFrame({"x": [0], "y": [0]})
center_point = (
    alt.Chart(center_df)
    .mark_point(size=300, shape="cross", color="#306998", strokeWidth=3)
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y))
)

# Resistance value labels
r_labels_data = [
    {"x": 0.0, "y": 0.08, "label": "0"},
    {"x": 0.17, "y": 0.08, "label": "0.2"},
    {"x": 0.33, "y": 0.08, "label": "0.5"},
    {"x": 0.5, "y": 0.08, "label": "1"},
    {"x": 0.67, "y": 0.08, "label": "2"},
    {"x": 0.83, "y": 0.08, "label": "5"},
]
r_labels_df = pd.DataFrame(r_labels_data)

r_labels = (
    alt.Chart(r_labels_df)
    .mark_text(fontSize=14, color="#444444", fontWeight="bold")
    .encode(x=alt.X("x:Q", scale=scale_x), y=alt.Y("y:Q", scale=scale_y), text="label:N")
)

# Combine all layers
chart = (
    alt.layer(res_circles, react_arcs, boundary, center_point, impedance_line, impedance_points, freq_labels, r_labels)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(
            "smith-chart-basic · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="Antenna Impedance Sweep (1-6 GHz, Z₀ = 50Ω)",
            subtitleFontSize=20,
            subtitleColor="#666666",
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False, domain=False, labels=False, ticks=False, title=None)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
