""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-18
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
flow_rise = np.linspace(0, pef_measured, pef_idx + 1)
vol_remaining = vol_exp[pef_idx:] - vol_exp[pef_idx]
vol_range = fvc_measured - vol_exp[pef_idx]
flow_decline = pef_measured * (1 - (vol_remaining / vol_range) ** 0.85)
flow_exp = np.concatenate([flow_rise, flow_decline[1:]])
flow_exp += np.random.normal(0, 0.015, len(flow_exp))  # subtle noise
flow_exp = np.clip(flow_exp, 0, None)
flow_exp[0] = 0
flow_exp[-1] = 0

# Measured inspiratory limb: symmetric U-shape
vol_insp = np.linspace(fvc_measured, 0, n_points)
t_insp = np.linspace(0, np.pi, n_points)
flow_insp = -5.5 * np.sin(t_insp)
flow_insp += np.random.normal(0, 0.015, len(flow_insp))
flow_insp[0] = 0
flow_insp[-1] = 0

# Predicted expiratory limb
vol_pred_exp = np.linspace(0, fvc_predicted, n_points)
pred_pef_idx = int(n_points * 0.12)
pred_flow_rise = np.linspace(0, pef_predicted, pred_pef_idx + 1)
pred_vol_remaining = vol_pred_exp[pred_pef_idx:] - vol_pred_exp[pred_pef_idx]
pred_vol_range = fvc_predicted - vol_pred_exp[pred_pef_idx]
pred_flow_decline = pef_predicted * (1 - (pred_vol_remaining / pred_vol_range) ** 0.85)
flow_pred_exp = np.concatenate([pred_flow_rise, pred_flow_decline[1:]])
flow_pred_exp = np.clip(flow_pred_exp, 0, None)
flow_pred_exp[0] = 0
flow_pred_exp[-1] = 0

# Predicted inspiratory limb
vol_pred_insp = np.linspace(fvc_predicted, 0, n_points)
t_pred_insp = np.linspace(0, np.pi, n_points)
flow_pred_insp = -6.2 * np.sin(t_pred_insp)
flow_pred_insp[0] = 0
flow_pred_insp[-1] = 0

# Combine into dataframes
df_measured = pd.concat(
    [pd.DataFrame({"volume": vol_exp, "flow": flow_exp}), pd.DataFrame({"volume": vol_insp, "flow": flow_insp})],
    ignore_index=True,
)
df_measured["curve"] = "Measured"
df_measured["order"] = range(len(df_measured))

df_predicted = pd.concat(
    [
        pd.DataFrame({"volume": vol_pred_exp, "flow": flow_pred_exp}),
        pd.DataFrame({"volume": vol_pred_insp, "flow": flow_pred_insp}),
    ],
    ignore_index=True,
)
df_predicted["curve"] = "Predicted"
df_predicted["order"] = range(len(df_predicted))

df_all = pd.concat([df_measured, df_predicted], ignore_index=True)

# PEF annotation point
pef_vol = vol_exp[np.argmax(flow_exp)]
pef_flow = float(flow_exp.max())
df_pef = pd.DataFrame({"volume": [pef_vol], "flow": [pef_flow], "label": [f"PEF = {pef_flow:.1f} L/s"]})

# Clinical values annotation
df_clinical = pd.DataFrame(
    {
        "volume": [4.2],
        "flow": [8.5],
        "label": [f"FVC = {fvc_measured:.1f} L\nFEV\u2081 = {fev1_measured:.1f} L\nPEF = {pef_flow:.1f} L/s"],
    }
)

# FEV1 marker: vertical reference at 1-second volume (approx FEV1 volume)
df_fev1_line = pd.DataFrame({"volume": [fev1_measured, fev1_measured], "flow": [-1.5, 8.0]})

df_fev1_label = pd.DataFrame({"volume": [fev1_measured], "flow": [8.5], "label": ["FEV\u2081"]})

# Color and dash scales for legend
color_scale = alt.Scale(domain=["Measured", "Predicted"], range=["#306998", "#999999"])
dash_scale = alt.Scale(domain=["Measured", "Predicted"], range=[[0], [8, 6]])

# Nearest selection for interactive tooltip on hover (Altair-distinctive)
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["order"], empty=False)

# Main curves with legend
curves = (
    alt.Chart(df_all)
    .mark_line(strokeWidth=2.5)
    .encode(
        x=alt.X("volume:Q", title="Volume (L)", scale=alt.Scale(domain=[-0.3, 5.6])),
        y=alt.Y("flow:Q", title="Flow (L/s)", scale=alt.Scale(domain=[-8, 12])),
        order="order:Q",
        color=alt.Color(
            "curve:N",
            title=None,
            scale=color_scale,
            legend=alt.Legend(labelFontSize=16, symbolSize=300, symbolStrokeWidth=3, orient="top-right", offset=-10),
        ),
        strokeDash=alt.StrokeDash("curve:N", title=None, scale=dash_scale, legend=None),
        strokeWidth=alt.condition(alt.datum.curve == "Measured", alt.value(3), alt.value(2)),
    )
)

# Interactive tooltip layer (Altair-distinctive: hover reveals flow/volume values)
tooltip_points = (
    alt.Chart(df_measured)
    .mark_point(opacity=0, size=80)
    .encode(
        x="volume:Q",
        y="flow:Q",
        tooltip=[
            alt.Tooltip("volume:Q", title="Volume (L)", format=".2f"),
            alt.Tooltip("flow:Q", title="Flow (L/s)", format=".2f"),
        ],
    )
    .add_params(nearest)
)

hover_rule = (
    alt.Chart(df_measured)
    .mark_rule(color="#666666", strokeWidth=1, strokeDash=[3, 3])
    .encode(x="volume:Q")
    .transform_filter(nearest)
)

hover_point = (
    alt.Chart(df_measured)
    .mark_point(size=120, filled=True, color="#306998")
    .encode(x="volume:Q", y="flow:Q")
    .transform_filter(nearest)
)

# PEF marker and label
pef_point = alt.Chart(df_pef).mark_point(size=300, filled=True, color="#C0392B").encode(x="volume:Q", y="flow:Q")

pef_label = (
    alt.Chart(df_pef)
    .mark_text(align="left", dx=16, dy=-16, fontSize=18, fontWeight="bold", color="#C0392B")
    .encode(x="volume:Q", y="flow:Q", text="label:N")
)

# FEV1 vertical reference line with label
fev1_line = (
    alt.Chart(df_fev1_line)
    .mark_line(strokeWidth=1.5, strokeDash=[6, 4], color="#E67E22", opacity=0.7)
    .encode(x="volume:Q", y="flow:Q")
)

fev1_label = (
    alt.Chart(df_fev1_label)
    .mark_text(fontSize=15, fontWeight="bold", color="#E67E22", dy=-8)
    .encode(x="volume:Q", y="flow:Q", text="label:N")
)

# Clinical values text
clinical_text = (
    alt.Chart(df_clinical)
    .mark_text(align="left", fontSize=17, lineBreak="\n", lineHeight=22, color="#333333", fontWeight="bold")
    .encode(x="volume:Q", y="flow:Q", text="label:N")
)

# Zero flow reference line
df_zero = pd.DataFrame({"volume": [-0.3, 5.6], "flow": [0, 0]})
zero_line = (
    alt.Chart(df_zero).mark_line(strokeWidth=1, strokeDash=[4, 4], color="#bbbbbb").encode(x="volume:Q", y="flow:Q")
)

# Expiratory/Inspiratory region labels
df_region_exp = pd.DataFrame({"volume": [0.2], "flow": [11.0], "label": ["Expiration"]})
df_region_insp = pd.DataFrame({"volume": [0.2], "flow": [-7.0], "label": ["Inspiration"]})

region_exp_label = (
    alt.Chart(df_region_exp)
    .mark_text(fontSize=14, color="#888888", fontStyle="italic", align="left")
    .encode(x="volume:Q", y="flow:Q", text="label:N")
)

region_insp_label = (
    alt.Chart(df_region_insp)
    .mark_text(fontSize=14, color="#888888", fontStyle="italic", align="left")
    .encode(x="volume:Q", y="flow:Q", text="label:N")
)

chart = (
    (
        zero_line
        + curves
        + tooltip_points
        + hover_rule
        + hover_point
        + fev1_line
        + fev1_label
        + pef_point
        + pef_label
        + clinical_text
        + region_exp_label
        + region_insp_label
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title("spirometry-flow-volume · altair · pyplots.ai", fontSize=28, anchor="start", color="#222222"),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        gridOpacity=0.12,
        gridColor="#cccccc",
        domainColor="#444444",
        tickColor="#888888",
        labelColor="#333333",
        titleColor="#222222",
    )
    .configure_view(strokeWidth=0)
    .configure_legend(padding=10, cornerRadius=4, strokeColor="#dddddd")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
