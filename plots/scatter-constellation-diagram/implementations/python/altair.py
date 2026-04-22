""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-17
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

ideal_vals = [-3, -1, 1, 3]
ideal_i, ideal_q = np.meshgrid(ideal_vals, ideal_vals)
ideal_i = ideal_i.flatten()
ideal_q = ideal_q.flatten()

n_symbols = 1000
symbol_indices = np.random.randint(0, 16, size=n_symbols)

snr_db = 20
snr_linear = 10 ** (snr_db / 10)
signal_power = np.mean(ideal_i**2 + ideal_q**2)
noise_std = np.sqrt(signal_power / snr_linear)

received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

error_vectors = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
rms_signal = np.sqrt(signal_power)
evm_pct = np.sqrt(np.mean(error_vectors**2)) / rms_signal * 100

# Per-symbol error magnitude for color encoding
df_received = pd.DataFrame(
    {
        "I": received_i,
        "Q": received_q,
        "Error Magnitude": error_vectors,
        "Nearest I": ideal_i[symbol_indices],
        "Nearest Q": ideal_q[symbol_indices],
    }
)
df_ideal = pd.DataFrame({"I": ideal_i, "Q": ideal_q, "label": "Ideal"})

# Decision boundaries
boundary_vals = [-4, -2, 0, 2, 4]
boundary_h = pd.DataFrame([{"x": -5.2, "x2": 5.2, "y": v} for v in boundary_vals])
boundary_v = pd.DataFrame([{"y": -5.2, "y2": 5.2, "x": v} for v in boundary_vals])

# EVM annotation
df_evm = pd.DataFrame({"I": [4.2], "Q": [4.8], "label": [f"EVM = {evm_pct:.1f}%"]})

# Selection for interactive nearest-point highlighting
nearest = alt.selection_point(on="pointerover", nearest=True, fields=["I", "Q"], empty=False)

# Plot layers
scale_x = alt.Scale(domain=[-5.5, 5.5], nice=False)
scale_y = alt.Scale(domain=[-5.5, 5.5], nice=False)

received_layer = (
    alt.Chart(df_received)
    .mark_circle(size=45)
    .encode(
        x=alt.X("I:Q", title="In-Phase (I)", scale=scale_x),
        y=alt.Y("Q:Q", title="Quadrature (Q)", scale=scale_y),
        color=alt.Color(
            "Error Magnitude:Q",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(
                title="Error Mag.", titleFontSize=16, labelFontSize=14, orient="right", gradientLength=200
            ),
        ),
        opacity=alt.condition(nearest, alt.value(0.85), alt.value(0.3)),
        size=alt.condition(nearest, alt.value(120), alt.value(45)),
        tooltip=[
            alt.Tooltip("I:Q", format=".3f"),
            alt.Tooltip("Q:Q", format=".3f"),
            alt.Tooltip("Error Magnitude:Q", format=".3f", title="Error"),
            alt.Tooltip("Nearest I:Q", format=".0f", title="Ideal I"),
            alt.Tooltip("Nearest Q:Q", format=".0f", title="Ideal Q"),
        ],
    )
    .add_params(nearest)
)

ideal_layer = (
    alt.Chart(df_ideal)
    .mark_point(size=400, filled=False, strokeWidth=3.5)
    .encode(
        x="I:Q",
        y="Q:Q",
        color=alt.value("#E45756"),
        shape=alt.value("cross"),
        tooltip=[alt.Tooltip("I:Q", format=".0f", title="Ideal I"), alt.Tooltip("Q:Q", format=".0f", title="Ideal Q")],
    )
)

h_rules = (
    alt.Chart(boundary_h)
    .mark_rule(strokeDash=[8, 5], strokeWidth=1, opacity=0.35)
    .encode(x=alt.X("x:Q", scale=scale_x), x2="x2:Q", y=alt.Y("y:Q", scale=scale_y), color=alt.value("#AAAAAA"))
)

v_rules = (
    alt.Chart(boundary_v)
    .mark_rule(strokeDash=[8, 5], strokeWidth=1, opacity=0.35)
    .encode(y=alt.Y("y:Q", scale=scale_y), y2="y2:Q", x=alt.X("x:Q", scale=scale_x), color=alt.value("#AAAAAA"))
)

evm_label = (
    alt.Chart(df_evm)
    .mark_text(fontSize=22, fontWeight="bold", align="right", font="monospace")
    .encode(x="I:Q", y="Q:Q", text="label:N", color=alt.value("#222222"))
)

chart = (
    alt.layer(h_rules, v_rules, received_layer, ideal_layer, evm_label)
    .properties(
        width=1020,
        height=1100,
        title=alt.Title(
            "scatter-constellation-diagram \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle", offset=12
        ),
    )
    .configure_axis(
        labelFontSize=18, titleFontSize=22, tickSize=8, domainColor="#666666", tickColor="#888888", grid=False
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
