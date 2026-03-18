""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: altair 6.0.0 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-18
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

fvc_measured = 4.8
fev1_measured = 3.2
pef_measured = 9.5

fvc_predicted = 5.2
pef_predicted = 10.5

n_points = 150

# Measured expiratory limb: sharp rise to PEF then linear decline
vol_exp = np.linspace(0, fvc_measured, n_points)
pef_idx = int(n_points * 0.12)
flow_exp_rise = np.linspace(0, pef_measured, pef_idx + 1)
vol_remaining = vol_exp[pef_idx:] - vol_exp[pef_idx]
vol_range = fvc_measured - vol_exp[pef_idx]
flow_exp_decline = pef_measured * (1 - (vol_remaining / vol_range) ** 0.85)
flow_exp = np.concatenate([flow_exp_rise, flow_exp_decline[1:]])
flow_exp += np.random.normal(0, 0.03, len(flow_exp))
flow_exp = np.clip(flow_exp, 0, None)
flow_exp[0] = 0
flow_exp[-1] = 0

# Measured inspiratory limb: symmetric U-shape below zero
vol_insp = np.linspace(fvc_measured, 0, n_points)
t_insp = np.linspace(0, np.pi, n_points)
flow_insp = -5.5 * np.sin(t_insp)
flow_insp += np.random.normal(0, 0.03, len(flow_insp))
flow_insp[0] = 0
flow_insp[-1] = 0

# Predicted expiratory limb
vol_pred_exp = np.linspace(0, fvc_predicted, n_points)
pef_idx_p = int(n_points * 0.12)
flow_pred_rise = np.linspace(0, pef_predicted, pef_idx_p + 1)
vol_pred_remaining = vol_pred_exp[pef_idx_p:] - vol_pred_exp[pef_idx_p]
vol_pred_range = fvc_predicted - vol_pred_exp[pef_idx_p]
flow_pred_decline = pef_predicted * (1 - (vol_pred_remaining / vol_pred_range) ** 0.85)
flow_pred_exp = np.concatenate([flow_pred_rise, flow_pred_decline[1:]])
flow_pred_exp[0] = 0
flow_pred_exp[-1] = 0

# Predicted inspiratory limb
vol_pred_insp = np.linspace(fvc_predicted, 0, n_points)
t_pred_insp = np.linspace(0, np.pi, n_points)
flow_pred_insp = -6.2 * np.sin(t_pred_insp)
flow_pred_insp[0] = 0
flow_pred_insp[-1] = 0

# Combine into dataframes
df_measured_exp = pd.DataFrame({"volume": vol_exp, "flow": flow_exp, "curve": "Measured", "limb": "expiratory"})
df_measured_insp = pd.DataFrame({"volume": vol_insp, "flow": flow_insp, "curve": "Measured", "limb": "inspiratory"})
df_predicted_exp = pd.DataFrame(
    {"volume": vol_pred_exp, "flow": flow_pred_exp, "curve": "Predicted", "limb": "expiratory"}
)
df_predicted_insp = pd.DataFrame(
    {"volume": vol_pred_insp, "flow": flow_pred_insp, "curve": "Predicted", "limb": "inspiratory"}
)

df_measured = pd.concat([df_measured_exp, df_measured_insp], ignore_index=True)
df_predicted = pd.concat([df_predicted_exp, df_predicted_insp], ignore_index=True)
df_measured["order"] = range(len(df_measured))
df_predicted["order"] = range(len(df_predicted))

# PEF annotation point
pef_vol = vol_exp[np.argmax(flow_exp)]
pef_flow = flow_exp.max()
df_pef = pd.DataFrame({"volume": [pef_vol], "flow": [pef_flow], "label": [f"PEF = {pef_flow:.1f} L/s"]})

# Clinical values annotation
fev1_vol_idx = np.argmin(np.abs(vol_exp - fev1_measured))
fev1_flow = flow_exp[fev1_vol_idx]
df_clinical = pd.DataFrame(
    {
        "volume": [5.5],
        "flow": [8.0],
        "label": [f"FVC = {fvc_measured:.1f} L\nFEV₁ = {fev1_measured:.1f} L\nPEF = {pef_flow:.1f} L/s"],
    }
)

# Plot
measured_line = (
    alt.Chart(df_measured)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("volume:Q", title="Volume (L)", scale=alt.Scale(domain=[-0.3, 6.5])),
        y=alt.Y("flow:Q", title="Flow (L/s)", scale=alt.Scale(domain=[-8, 12])),
        order="order:Q",
        color=alt.value("#306998"),
    )
)

predicted_line = (
    alt.Chart(df_predicted)
    .mark_line(strokeWidth=2, strokeDash=[8, 6])
    .encode(x="volume:Q", y="flow:Q", order="order:Q", color=alt.value("#999999"))
)

pef_point = alt.Chart(df_pef).mark_point(size=250, filled=True, color="#C0392B").encode(x="volume:Q", y="flow:Q")

pef_label = (
    alt.Chart(df_pef)
    .mark_text(align="left", dx=14, dy=-14, fontSize=18, fontWeight="bold", color="#C0392B")
    .encode(x="volume:Q", y="flow:Q", text="label:N")
)

clinical_text = (
    alt.Chart(df_clinical)
    .mark_text(align="left", fontSize=17, lineBreak="\n", color="#333333", fontWeight="bold")
    .encode(x="volume:Q", y="flow:Q", text="label:N")
)

# Zero flow reference line
df_zero = pd.DataFrame({"volume": [-0.3, 6.5], "flow": [0, 0]})
zero_line = (
    alt.Chart(df_zero).mark_line(strokeWidth=1, strokeDash=[4, 4], color="#aaaaaa").encode(x="volume:Q", y="flow:Q")
)

# Legend entries
df_legend = pd.DataFrame({"curve": ["Measured", "Predicted"], "x": [0, 0], "y": [0, 0]})
legend_marks = (
    alt.Chart(df_legend)
    .mark_point(opacity=0)
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("y:Q"),
        strokeDash=alt.StrokeDash(
            "curve:N",
            legend=alt.Legend(title=None, labelFontSize=16, symbolSize=200),
            scale=alt.Scale(domain=["Measured", "Predicted"], range=[[0], [8, 6]]),
        ),
        color=alt.Color(
            "curve:N", legend=None, scale=alt.Scale(domain=["Measured", "Predicted"], range=["#306998", "#999999"])
        ),
    )
)

chart = (
    (zero_line + predicted_line + measured_line + pef_point + pef_label + clinical_text)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("spirometry-flow-volume · altair · pyplots.ai", fontSize=28, anchor="start"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.2, domainColor="#333333")
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
