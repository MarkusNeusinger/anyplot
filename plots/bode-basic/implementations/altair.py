"""pyplots.ai
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

# Colors - colorblind-safe palette (no red-green pairing)
CLR_MAG = "#306998"  # Python Blue - magnitude curve
CLR_PHASE = "#E8833A"  # Orange - phase curve
CLR_GM = "#7B2D8E"  # Purple - gain margin annotation
CLR_PM = "#1B7FA3"  # Teal/cerulean - phase margin annotation
CLR_REF = "#888888"  # Gray - reference lines
CLR_GRID = "#d0d0d0"  # Light gray - grid
CLR_TITLE = "#1a1a1a"  # Near-black - title
CLR_SUBTITLE = "#555555"  # Medium gray - subtitle
CLR_AXIS = "#333333"  # Dark gray - axis labels
CLR_TICK = "#555555"  # Medium gray - tick labels
CLR_BG = "#FAFBFC"  # Very light blue-gray - background

# Reference line data
ref_0db = pd.DataFrame({"x": [omega.min(), omega.max()], "y": [0, 0]})
ref_180 = pd.DataFrame({"x": [omega.min(), omega.max()], "y": [-180, -180]})

# Gain margin vertical line data (on magnitude plot)
gm_line = pd.DataFrame({"frequency": [phase_cross_freq, phase_cross_freq], "magnitude_db": [phase_cross_mag, 0]})
gm_label = pd.DataFrame(
    {
        "frequency": [phase_cross_freq],
        "magnitude_db": [phase_cross_mag / 2 + 2],
        "label": [f"GM = {gain_margin:.1f} dB"],
    }
)

# Phase margin vertical line data (on phase plot)
pm_line = pd.DataFrame({"frequency": [gain_cross_freq, gain_cross_freq], "phase_deg": [gain_cross_phase, -180]})
pm_label = pd.DataFrame(
    {
        "frequency": [gain_cross_freq],
        "phase_deg": [(gain_cross_phase - 180) / 2 + 8],
        "label": [f"PM = {phase_margin:.1f}°"],
    }
)

# Crossover point markers
gc_mag_pt = pd.DataFrame({"frequency": [gain_cross_freq], "magnitude_db": [0.0]})
pc_mag_pt = pd.DataFrame({"frequency": [phase_cross_freq], "magnitude_db": [phase_cross_mag]})
gc_phase_pt = pd.DataFrame({"frequency": [gain_cross_freq], "phase_deg": [gain_cross_phase]})
pc_phase_pt = pd.DataFrame({"frequency": [phase_cross_freq], "phase_deg": [-180.0]})

# Stability region shading (magnitude plot: above 0 dB band)
stability_band_mag = pd.DataFrame({"x": [omega.min(), omega.max()], "y1": [0, 0], "y2": [5, 5]})
stability_band_phase = pd.DataFrame({"x": [omega.min(), omega.max()], "y1": [-180, -180], "y2": [-170, -170]})

# Shared axis config
freq_scale = alt.Scale(type="log", domain=[0.01, 1000], nice=False)
y_mag_scale = alt.Scale(domain=[-60, 30])
y_phase_scale = alt.Scale(domain=[-280, 10])

axis_config_x = {
    "labelFontSize": 16,
    "titleFontSize": 20,
    "titleFontWeight": "bold",
    "titleColor": CLR_AXIS,
    "labelColor": CLR_TICK,
    "gridOpacity": 0.25,
    "gridWidth": 0.5,
    "gridColor": CLR_GRID,
    "domainColor": "#bbbbbb",
    "domainWidth": 1.5,
    "tickColor": "#bbbbbb",
    "tickSize": 6,
    "labelPadding": 6,
}

axis_config_y = {**axis_config_x, "titlePadding": 14}

# --- Nearest-point selection for interactive crosshair tooltip ---
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["frequency"], empty=False)

# Magnitude plot
mag_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color=CLR_MAG, interpolate="monotone")
    .encode(
        x=alt.X("frequency:Q", scale=freq_scale, axis=alt.Axis(labels=False, title="", ticks=False, **axis_config_x)),
        y=alt.Y("magnitude_db:Q", title="Magnitude (dB)", scale=y_mag_scale, axis=alt.Axis(**axis_config_y)),
        tooltip=[
            alt.Tooltip("frequency:Q", title="ω (rad/s)", format=".2f"),
            alt.Tooltip("magnitude_db:Q", title="Magnitude (dB)", format=".1f"),
        ],
    )
)

# Invisible selection layer for crosshair
mag_selectable = (
    alt.Chart(df)
    .mark_point(opacity=0)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("magnitude_db:Q", scale=y_mag_scale))
    .add_params(nearest)
)

# Crosshair vertical rule
mag_crosshair = (
    alt.Chart(df)
    .mark_rule(color="#666666", strokeWidth=0.8, strokeDash=[3, 3])
    .encode(x=alt.X("frequency:Q", scale=freq_scale))
    .transform_filter(nearest)
)

mag_ref = (
    alt.Chart(ref_0db)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color=CLR_REF, opacity=0.5)
    .encode(x=alt.X("x:Q", scale=freq_scale), y=alt.Y("y:Q", scale=y_mag_scale))
)

mag_gm_line = (
    alt.Chart(gm_line)
    .mark_line(strokeWidth=2.5, color=CLR_GM, strokeDash=[5, 3])
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("magnitude_db:Q", scale=y_mag_scale))
)

mag_gm_label = (
    alt.Chart(gm_label)
    .mark_text(fontSize=15, fontWeight="bold", color=CLR_GM, align="left", dx=14, font="monospace")
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("magnitude_db:Q", scale=y_mag_scale), text="label:N")
)

mag_gc_point = (
    alt.Chart(gc_mag_pt)
    .mark_point(size=220, shape="circle", filled=True, color=CLR_MAG, stroke="white", strokeWidth=2.5)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("magnitude_db:Q", scale=y_mag_scale))
)

mag_pc_point = (
    alt.Chart(pc_mag_pt)
    .mark_point(size=220, shape="diamond", filled=True, color=CLR_GM, stroke="white", strokeWidth=2.5)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("magnitude_db:Q", scale=y_mag_scale))
)

magnitude_chart = (
    mag_line + mag_ref + mag_gm_line + mag_gm_label + mag_gc_point + mag_pc_point + mag_selectable + mag_crosshair
).properties(
    width=1600,
    height=420,
    title=alt.Title(
        "bode-basic · altair · pyplots.ai",
        fontSize=28,
        fontWeight="bold",
        color=CLR_TITLE,
        subtitle="G(s) = 10 / (s+1)(s/10+1)(s/50+1)  ·  Open-Loop Frequency Response",
        subtitleFontSize=18,
        subtitleColor=CLR_SUBTITLE,
        subtitlePadding=10,
        anchor="start",
        offset=12,
    ),
)

# Phase plot
phase_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color=CLR_PHASE, interpolate="monotone")
    .encode(
        x=alt.X("frequency:Q", scale=freq_scale, title="Frequency (rad/s)", axis=alt.Axis(**axis_config_x)),
        y=alt.Y("phase_deg:Q", title="Phase (degrees)", scale=y_phase_scale, axis=alt.Axis(**axis_config_y)),
        tooltip=[
            alt.Tooltip("frequency:Q", title="ω (rad/s)", format=".2f"),
            alt.Tooltip("phase_deg:Q", title="Phase (°)", format=".1f"),
        ],
    )
)

phase_ref = (
    alt.Chart(ref_180)
    .mark_line(strokeWidth=1.5, strokeDash=[8, 6], color=CLR_REF, opacity=0.5)
    .encode(x=alt.X("x:Q", scale=freq_scale), y=alt.Y("y:Q", scale=y_phase_scale))
)

phase_pm_line = (
    alt.Chart(pm_line)
    .mark_line(strokeWidth=2.5, color=CLR_PM, strokeDash=[5, 3])
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("phase_deg:Q", scale=y_phase_scale))
)

phase_pm_label = (
    alt.Chart(pm_label)
    .mark_text(fontSize=15, fontWeight="bold", color=CLR_PM, align="left", dx=14, font="monospace")
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("phase_deg:Q", scale=y_phase_scale), text="label:N")
)

phase_gc_point = (
    alt.Chart(gc_phase_pt)
    .mark_point(size=220, shape="circle", filled=True, color=CLR_PHASE, stroke="white", strokeWidth=2.5)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("phase_deg:Q", scale=y_phase_scale))
)

phase_pc_point = (
    alt.Chart(pc_phase_pt)
    .mark_point(size=220, shape="diamond", filled=True, color=CLR_PM, stroke="white", strokeWidth=2.5)
    .encode(x=alt.X("frequency:Q", scale=freq_scale), y=alt.Y("phase_deg:Q", scale=y_phase_scale))
)

phase_chart = (phase_line + phase_ref + phase_pm_line + phase_pm_label + phase_gc_point + phase_pc_point).properties(
    width=1600, height=420
)

# Combine vertically with refined global config
chart = (
    alt.vconcat(magnitude_chart, phase_chart, spacing=16)
    .configure_view(strokeWidth=0, fill=CLR_BG, cornerRadius=4)
    .configure_concat(spacing=16)
    .configure(background="#FFFFFF", padding={"left": 20, "right": 30, "top": 10, "bottom": 10})
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
