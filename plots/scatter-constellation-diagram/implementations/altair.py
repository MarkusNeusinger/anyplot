""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-17
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

df_received = pd.DataFrame({"I": received_i, "Q": received_q})
df_ideal = pd.DataFrame({"I": ideal_i, "Q": ideal_q})

# Decision boundaries
boundary_vals = [-4, -2, 0, 2, 4]
boundary_h = pd.DataFrame([{"x": -4.5, "x2": 4.5, "y": v} for v in boundary_vals])
boundary_v = pd.DataFrame([{"y": -4.5, "y2": 4.5, "x": v} for v in boundary_vals])

# EVM annotation
df_evm = pd.DataFrame({"I": [3.2], "Q": [4.0], "label": [f"EVM = {evm_pct:.1f}%"]})

# Plot
received_layer = (
    alt.Chart(df_received)
    .mark_circle(size=40, opacity=0.35)
    .encode(
        x=alt.X("I:Q", title="In-Phase (I)", scale=alt.Scale(domain=[-4.8, 4.8])),
        y=alt.Y("Q:Q", title="Quadrature (Q)", scale=alt.Scale(domain=[-4.8, 4.8])),
        color=alt.value("#306998"),
        tooltip=["I:Q", "Q:Q"],
    )
)

ideal_layer = (
    alt.Chart(df_ideal)
    .mark_point(size=350, filled=False, strokeWidth=3)
    .encode(x="I:Q", y="Q:Q", color=alt.value("#D62728"), shape=alt.value("cross"), tooltip=["I:Q", "Q:Q"])
)

h_rules = (
    alt.Chart(boundary_h)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.2, opacity=0.45)
    .encode(x=alt.X("x:Q"), x2="x2:Q", y=alt.Y("y:Q"), color=alt.value("#999999"))
)

v_rules = (
    alt.Chart(boundary_v)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.2, opacity=0.45)
    .encode(y=alt.Y("y:Q"), y2="y2:Q", x=alt.X("x:Q"), color=alt.value("#999999"))
)

evm_label = (
    alt.Chart(df_evm)
    .mark_text(fontSize=20, fontWeight="bold", align="right")
    .encode(x="I:Q", y="Q:Q", text="label:N", color=alt.value("#333333"))
)

chart = (
    alt.layer(h_rules, v_rules, received_layer, ideal_layer, evm_label)
    .properties(
        width=900,
        height=900,
        title=alt.Title("scatter-constellation-diagram · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=False)
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
