""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: altair 6.0.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-21
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Third-order open-loop transfer function:
# G(s) = 10 / (s/1 + 1)(s/10 + 1)(s/50 + 1)
# Poles at s = -1, -10, -50; DC gain = 20 dB
omega = np.logspace(-2, 3, 600)
s = 1j * omega

K = 10.0
G = K / ((s / 1 + 1) * (s / 10 + 1) * (s / 50 + 1))

magnitude_db = 20 * np.log10(np.abs(G))
phase_deg = np.degrees(np.unwrap(np.angle(G)))

df = pd.DataFrame({"frequency": omega, "magnitude_db": magnitude_db, "phase_deg": phase_deg})

# Find gain crossover frequency (|G| = 0 dB)
# Search where magnitude crosses 0 dB from above
sign_changes_mag = np.where(np.diff(np.sign(magnitude_db)))[0]
gain_cross_idx = sign_changes_mag[0] if len(sign_changes_mag) > 0 else np.argmin(np.abs(magnitude_db))
gain_cross_freq = omega[gain_cross_idx]
gain_cross_phase = phase_deg[gain_cross_idx]
phase_margin = 180 + gain_cross_phase

# Find phase crossover frequency (phase = -180°)
sign_changes_phase = np.where(np.diff(np.sign(phase_deg - (-180))))[0]
phase_cross_idx = sign_changes_phase[0] if len(sign_changes_phase) > 0 else np.argmin(np.abs(phase_deg + 180))
phase_cross_freq = omega[phase_cross_idx]
phase_cross_mag = magnitude_db[phase_cross_idx]
gain_margin = -phase_cross_mag

# Reference line data
ref_0db = pd.DataFrame({"x": [omega.min(), omega.max()], "y": [0, 0]})
ref_180 = pd.DataFrame({"x": [omega.min(), omega.max()], "y": [-180, -180]})

# Gain margin vertical line (on magnitude plot)
gm_line = pd.DataFrame({"frequency": [phase_cross_freq, phase_cross_freq], "magnitude_db": [phase_cross_mag, 0]})
gm_label = pd.DataFrame(
    {"frequency": [phase_cross_freq], "magnitude_db": [phase_cross_mag / 2], "label": [f"GM = {gain_margin:.1f} dB"]}
)

# Phase margin vertical line (on phase plot)
pm_line = pd.DataFrame({"frequency": [gain_cross_freq, gain_cross_freq], "phase_deg": [gain_cross_phase, -180]})
pm_label = pd.DataFrame(
    {
        "frequency": [gain_cross_freq],
        "phase_deg": [(gain_cross_phase - 180) / 2],
        "label": [f"PM = {phase_margin:.1f}°"],
    }
)

# Crossover point markers
gc_mag_pt = pd.DataFrame({"frequency": [gain_cross_freq], "magnitude_db": [0.0]})
pc_mag_pt = pd.DataFrame({"frequency": [phase_cross_freq], "magnitude_db": [phase_cross_mag]})
gc_phase_pt = pd.DataFrame({"frequency": [gain_cross_freq], "phase_deg": [gain_cross_phase]})
pc_phase_pt = pd.DataFrame({"frequency": [phase_cross_freq], "phase_deg": [-180.0]})

# Shared axis config
freq_scale = alt.Scale(type="log", domain=[0.01, 1000], nice=False)
axis_config = {
    "labelFontSize": 16,
    "titleFontSize": 20,
    "titleFontWeight": "bold",
    "titleColor": "#2a2a2a",
    "labelColor": "#444444",
    "gridOpacity": 0.15,
    "gridWidth": 0.5,
    "gridColor": "#cccccc",
    "domainColor": "#aaaaaa",
    "tickColor": "#aaaaaa",
}

# Magnitude plot
mag_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color="#306998")
    .encode(
        x=alt.X("frequency:Q", scale=freq_scale, axis=alt.Axis(labels=False, title="", **axis_config)),
        y=alt.Y("magnitude_db:Q", title="Magnitude (dB)", axis=alt.Axis(**axis_config)),
        tooltip=[
            alt.Tooltip("frequency:Q", title="ω (rad/s)", format=".2f"),
            alt.Tooltip("magnitude_db:Q", title="Magnitude (dB)", format=".1f"),
        ],
    )
)

mag_ref = (
    alt.Chart(ref_0db)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color="#999999", opacity=0.6)
    .encode(x=alt.X("x:Q", scale=freq_scale), y=alt.Y("y:Q"))
)

mag_gm_line = (
    alt.Chart(gm_line)
    .mark_line(strokeWidth=2.5, color="#D62728", strokeDash=[4, 3])
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("magnitude_db:Q"))
)

mag_gm_label = (
    alt.Chart(gm_label)
    .mark_text(fontSize=16, fontWeight="bold", color="#D62728", align="left", dx=14)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("magnitude_db:Q"), text="label:N")
)

mag_gc_point = (
    alt.Chart(gc_mag_pt)
    .mark_point(size=250, shape="circle", filled=True, color="#306998", stroke="white", strokeWidth=2)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("magnitude_db:Q"))
)

mag_pc_point = (
    alt.Chart(pc_mag_pt)
    .mark_point(size=250, shape="diamond", filled=True, color="#D62728", stroke="white", strokeWidth=2)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("magnitude_db:Q"))
)

magnitude_chart = (mag_line + mag_ref + mag_gm_line + mag_gm_label + mag_gc_point + mag_pc_point).properties(
    width=1600,
    height=400,
    title=alt.Title(
        "bode-basic · altair · pyplots.ai",
        fontSize=28,
        fontWeight="bold",
        color="#1a1a1a",
        subtitle="G(s) = 10 / (s+1)(s/10+1)(s/50+1)  ·  Open-Loop Frequency Response",
        subtitleFontSize=18,
        subtitleColor="#555555",
        subtitlePadding=10,
        anchor="start",
        offset=10,
    ),
)

# Phase plot
phase_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color="#E8833A")
    .encode(
        x=alt.X("frequency:Q", scale=freq_scale, title="Frequency (rad/s)", axis=alt.Axis(**axis_config)),
        y=alt.Y(
            "phase_deg:Q", title="Phase (degrees)", scale=alt.Scale(domain=[-270, 0]), axis=alt.Axis(**axis_config)
        ),
        tooltip=[
            alt.Tooltip("frequency:Q", title="ω (rad/s)", format=".2f"),
            alt.Tooltip("phase_deg:Q", title="Phase (°)", format=".1f"),
        ],
    )
)

phase_ref = (
    alt.Chart(ref_180)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color="#999999", opacity=0.6)
    .encode(x=alt.X("x:Q", scale=freq_scale), y=alt.Y("y:Q"))
)

phase_pm_line = (
    alt.Chart(pm_line)
    .mark_line(strokeWidth=2.5, color="#2CA02C", strokeDash=[4, 3])
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("phase_deg:Q"))
)

phase_pm_label = (
    alt.Chart(pm_label)
    .mark_text(fontSize=16, fontWeight="bold", color="#2CA02C", align="left", dx=14)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("phase_deg:Q"), text="label:N")
)

phase_gc_point = (
    alt.Chart(gc_phase_pt)
    .mark_point(size=250, shape="circle", filled=True, color="#E8833A", stroke="white", strokeWidth=2)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("phase_deg:Q"))
)

phase_pc_point = (
    alt.Chart(pc_phase_pt)
    .mark_point(size=250, shape="diamond", filled=True, color="#D62728", stroke="white", strokeWidth=2)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("phase_deg:Q"))
)

phase_chart = (phase_line + phase_ref + phase_pm_line + phase_pm_label + phase_gc_point + phase_pc_point).properties(
    width=1600, height=400
)

# Combine vertically
chart = alt.vconcat(magnitude_chart, phase_chart, spacing=20).configure_view(strokeWidth=0).configure_concat(spacing=20)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
