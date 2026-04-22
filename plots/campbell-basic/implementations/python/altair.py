""" pyplots.ai
campbell-basic: Campbell Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-02-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)
speeds = np.linspace(0, 6000, 80)

mode_labels = ["1st Bending", "2nd Bending", "1st Torsional", "Axial", "3rd Bending"]
base_freqs = [45, 95, 130, 175, 220]
slopes = [0.004, -0.003, 0.005, 0.001, -0.004]
curvatures = [5e-7, -4e-7, 2e-7, 1e-7, -3e-7]

mode_rows = []
for label, base, slope, curv in zip(mode_labels, base_freqs, slopes, curvatures, strict=True):
    freqs = base + slope * speeds + curv * speeds**2
    for s, f in zip(speeds, freqs, strict=True):
        mode_rows.append({"RPM": s, "Hz": f, "Mode": label})

engine_orders = [1, 2, 3]
eo_rows = []
for order in engine_orders:
    for s in speeds:
        eo_rows.append({"RPM": s, "Hz": order * s / 60, "EO": f"{order}x"})

df_modes = pd.DataFrame(mode_rows)
df_eo = pd.DataFrame(eo_rows)

# Find critical speed intersections
critical_rows = []
dense_speeds = np.linspace(0, 6000, 5000)
for label, base, slope, curv in zip(mode_labels, base_freqs, slopes, curvatures, strict=True):
    mode_freq = base + slope * dense_speeds + curv * dense_speeds**2
    for order in engine_orders:
        eo_freq = order * dense_speeds / 60
        diff = mode_freq - eo_freq
        sign_changes = np.where(np.diff(np.sign(diff)))[0]
        for idx in sign_changes:
            s_crit = dense_speeds[idx]
            f_crit = eo_freq[idx]
            if 100 < s_crit < 5900 and 5 < f_crit < 295:
                in_op_range = 3000 <= s_crit <= 5000
                critical_rows.append(
                    {
                        "RPM": round(s_crit),
                        "Hz": round(f_crit, 1),
                        "Label": f"{label} / {order}x",
                        "InOpRange": in_op_range,
                    }
                )

df_critical = pd.DataFrame(critical_rows)

# Select well-spaced key critical speeds for annotation
key_in_range = df_critical[df_critical["InOpRange"]]
key_outside = df_critical[~df_critical["InOpRange"]].sort_values("Hz")
# Pick annotations that are well separated: one low outside, one mid in-range, one high in-range
df_annot = pd.DataFrame(
    [
        {**key_outside.iloc[0].to_dict(), "dx": 12, "dy": -18},  # 1st Bending / 3x (~988 RPM, ~49 Hz)
        {**key_in_range.iloc[0].to_dict(), "dx": -130, "dy": -20},  # 1st Bending / 1x (~4273 RPM, ~71 Hz) — left
        {**key_in_range.iloc[2].to_dict(), "dx": 14, "dy": -18},  # 1st Torsional / 2x (~4747 RPM, ~158 Hz)
    ]
)

# Operating range
op_min, op_max = 3000, 5000

# Color palette — colorblind-safe, high contrast between all modes
mode_palette = ["#306998", "#E8833A", "#55A868", "#BA6BC9", "#C44E52"]

x_scale = alt.Scale(domain=[0, 6200], nice=False)
y_scale = alt.Scale(domain=[0, 310])

# Operating range shaded band
op_band = (
    alt.Chart(pd.DataFrame({"x": [op_min], "x2": [op_max]}))
    .mark_rect(opacity=0.08, color="#306998")
    .encode(x=alt.X("x:Q", scale=x_scale), x2="x2:Q")
)

# Operating range label
op_label = (
    alt.Chart(pd.DataFrame({"RPM": [(op_min + op_max) / 2], "Hz": [8], "label": ["Operating Range"]}))
    .mark_text(fontSize=15, fontStyle="italic", color="#306998", fontWeight="bold")
    .encode(x=alt.X("RPM:Q", scale=x_scale), y=alt.Y("Hz:Q", scale=y_scale), text="label:N")
)

# Engine order lines — no legend (direct labels at right edge are cleaner)
eo_chart = (
    alt.Chart(df_eo)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color="#999999", opacity=0.55)
    .encode(x=alt.X("RPM:Q", scale=x_scale), y=alt.Y("Hz:Q", scale=y_scale), detail="EO:N")
)

# Engine order text labels near right edge
eo_label_rows = []
for order in engine_orders:
    max_freq = order * 6000 / 60
    if max_freq <= 295:
        eo_label_rows.append({"RPM": 6080, "Hz": order * 6080 / 60, "label": f"{order}x"})
    else:
        target_speed = 290 * 60 / order
        eo_label_rows.append({"RPM": target_speed + 80, "Hz": 295, "label": f"{order}x"})

eo_label_chart = (
    alt.Chart(pd.DataFrame(eo_label_rows))
    .mark_text(fontSize=15, fontWeight="bold", color="#777777", align="left", dy=-8)
    .encode(x=alt.X("RPM:Q", scale=x_scale), y=alt.Y("Hz:Q", scale=y_scale), text="label:N")
)

# Natural frequency mode lines
modes_chart = (
    alt.Chart(df_modes)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("RPM:Q", title="Rotational Speed (RPM)", scale=x_scale),
        y=alt.Y("Hz:Q", title="Frequency (Hz)", scale=y_scale),
        color=alt.Color(
            "Mode:N",
            scale=alt.Scale(domain=mode_labels, range=mode_palette),
            legend=alt.Legend(
                title="Natural Frequencies", titleFontSize=14, labelFontSize=13, symbolStrokeWidth=3, symbolSize=150
            ),
        ),
    )
)

# Critical speed markers — size-differentiated for operating range emphasis
crit_outside_chart = (
    alt.Chart(df_critical[~df_critical["InOpRange"]])
    .mark_point(size=200, shape="diamond", filled=True, color="#D62728", stroke="white", strokeWidth=1.5)
    .encode(x=alt.X("RPM:Q", scale=x_scale), y=alt.Y("Hz:Q", scale=y_scale), tooltip=["Label:N", "RPM:Q", "Hz:Q"])
)

crit_inside_chart = (
    alt.Chart(df_critical[df_critical["InOpRange"]])
    .mark_point(size=380, shape="diamond", filled=True, color="#D62728", stroke="white", strokeWidth=2.5)
    .encode(x=alt.X("RPM:Q", scale=x_scale), y=alt.Y("Hz:Q", scale=y_scale), tooltip=["Label:N", "RPM:Q", "Hz:Q"])
)

# Annotations for key critical speeds — single consolidated layer per offset group
annot_layers = []
for _, row in df_annot.iterrows():
    annot_layers.append(
        alt.Chart(pd.DataFrame([row]))
        .mark_text(fontSize=13, color="#8B0000", fontWeight="bold", align="left", dx=row["dx"], dy=row["dy"])
        .encode(x=alt.X("RPM:Q", scale=x_scale), y=alt.Y("Hz:Q", scale=y_scale), text="Label:N")
    )

# Compose chart
combined = op_band + eo_chart + modes_chart + crit_outside_chart + crit_inside_chart + eo_label_chart + op_label
for layer in annot_layers:
    combined = combined + layer

chart = (
    combined.properties(
        width=1600,
        height=900,
        title=alt.Title(
            "campbell-basic · altair · pyplots.ai",
            fontSize=28,
            fontWeight=500,
            anchor="start",
            subtitle="Natural Frequency Modes vs Engine Order Excitations",
            subtitleFontSize=16,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleColor="#333333",
        labelColor="#444444",
        grid=True,
        gridOpacity=0.10,
        gridWidth=0.5,
        gridColor="#cccccc",
        domainColor="#aaaaaa",
        domainWidth=0.8,
        tickColor="#aaaaaa",
        tickSize=6,
    )
    .configure_view(strokeWidth=0)
    .configure_legend(orient="right", padding=6, offset=2, titlePadding=4, rowPadding=2)
    .configure_title(anchor="start", offset=10)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
