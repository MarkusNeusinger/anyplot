""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: altair 6.0.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Nyquist plot for G(s) = 5 / ((s+1)(0.5s+1)(0.1s+1))
# A stable third-order system with DC gain = 5
omega = np.concatenate(
    [np.logspace(-2, -0.5, 100), np.logspace(-0.5, 0.5, 250), np.logspace(0.5, 1.5, 200), np.logspace(1.5, 3, 100)]
)

K = 5.0
s = 1j * omega
G = K / ((s + 1.0) * (0.5 * s + 1.0) * (0.1 * s + 1.0))

real_part = G.real
imag_part = G.imag

# Positive frequency branch
pos_df = pd.DataFrame(
    {"real": real_part, "imaginary": imag_part, "frequency": omega, "branch": "ω ≥ 0", "idx": np.arange(len(omega))}
)

# Negative frequency branch (mirror about real axis)
neg_df = pd.DataFrame(
    {
        "real": real_part,
        "imaginary": -imag_part,
        "frequency": -omega[::-1],
        "branch": "ω ≤ 0",
        "idx": np.arange(len(omega)),
    }
)

nyquist_df = pd.concat([pos_df, neg_df], ignore_index=True)

# Unit circle for reference
theta = np.linspace(0, 2 * np.pi, 200)
unit_circle_df = pd.DataFrame({"ux": np.cos(theta), "uy": np.sin(theta), "idx": np.arange(len(theta))})

# Critical point (-1, 0)
critical_df = pd.DataFrame({"real": [-1.0], "imaginary": [0.0], "label": ["(−1, 0)"]})

# Find gain crossover (|G(jω)| = 1)
magnitude = np.abs(G)
gain_cross_idx = np.argmin(np.abs(magnitude - 1.0))
gain_cross_omega = omega[gain_cross_idx]

# Phase crossover: where imaginary part crosses zero (excluding near DC)
sign_changes = np.where(np.diff(np.sign(imag_part[30:])))[0] + 30
phase_cross_idx = sign_changes[0] if len(sign_changes) > 0 else None
phase_cross_omega = omega[phase_cross_idx] if phase_cross_idx is not None else None

# Frequency markers along curve (selected key frequencies)
freq_annotations = []
for w_mark, dy_offset in [(0.5, -16), (1.0, -16), (2.0, 12), (5.0, 12)]:
    idx = np.argmin(np.abs(omega - w_mark))
    freq_annotations.append(
        {"real": real_part[idx], "imaginary": imag_part[idx], "label": f"ω = {w_mark}", "dy": dy_offset}
    )

# Add gain crossover annotation
freq_annotations.append(
    {
        "real": real_part[gain_cross_idx],
        "imaginary": imag_part[gain_cross_idx],
        "label": f"ω ≈ {gain_cross_omega:.1f} (|G|=1)",
        "dy": 16,
    }
)

freq_df = pd.DataFrame(freq_annotations)

# Arrow indicators for direction of increasing frequency
arrow_rows = []
for target_w in [0.8, 3.0]:
    idx = np.argmin(np.abs(omega - target_w))
    im_val = imag_part[idx]
    if abs(im_val) > 0.05:
        shape = "down" if im_val < 0 else "up"
        arrow_rows.append({"ax": real_part[idx], "ay": imag_part[idx], "branch": "ω ≥ 0", "shape": shape})
        arrow_rows.append(
            {
                "ax": real_part[idx],
                "ay": -imag_part[idx],
                "branch": "ω ≤ 0",
                "shape": "up" if shape == "down" else "down",
            }
        )
arrow_df = pd.DataFrame(arrow_rows)

# Axis scales - 1:1 aspect ratio, focus on interesting region
plot_range = 6.5
x_scale = alt.Scale(domain=[-plot_range, plot_range], nice=False)
y_scale = alt.Scale(domain=[-plot_range, plot_range], nice=False)

branch_palette = ["#306998", "#e07b39"]
branch_domain = ["ω ≥ 0", "ω ≤ 0"]

# Layer: Nyquist curve
nyquist_layer = (
    alt.Chart(nyquist_df)
    .mark_line(strokeWidth=2.8, opacity=0.9)
    .encode(
        x=alt.X(
            "real:Q",
            scale=x_scale,
            title="Real",
            axis=alt.Axis(
                labelFontSize=16,
                titleFontSize=21,
                titleFontWeight="bold",
                titleColor="#2a2a2a",
                labelColor="#444444",
                grid=False,
                titlePadding=14,
                domainColor="#888888",
                tickColor="#888888",
            ),
        ),
        y=alt.Y(
            "imaginary:Q",
            scale=y_scale,
            title="Imaginary",
            axis=alt.Axis(
                labelFontSize=16,
                titleFontSize=21,
                titleFontWeight="bold",
                titleColor="#2a2a2a",
                labelColor="#444444",
                grid=False,
                titlePadding=14,
                domainColor="#888888",
                tickColor="#888888",
            ),
        ),
        color=alt.Color(
            "branch:N",
            scale=alt.Scale(domain=branch_domain, range=branch_palette),
            legend=alt.Legend(
                title="Branch",
                titleFontSize=16,
                labelFontSize=14,
                symbolSize=180,
                symbolStrokeWidth=3,
                orient="top-right",
                offset=5,
            ),
        ),
        order="idx:Q",
        tooltip=[
            alt.Tooltip("branch:N", title="Branch"),
            alt.Tooltip("real:Q", title="Re(G)", format=".3f"),
            alt.Tooltip("imaginary:Q", title="Im(G)", format=".3f"),
            alt.Tooltip("frequency:Q", title="ω (rad/s)", format=".3f"),
        ],
    )
)

# Layer: Unit circle
unit_circle_layer = (
    alt.Chart(unit_circle_df)
    .mark_line(strokeWidth=1.5, strokeDash=[6, 4], color="#bbbbbb", opacity=0.7)
    .encode(x=alt.X("ux:Q", scale=x_scale), y=alt.Y("uy:Q", scale=y_scale), order="idx:Q")
)

# Layer: Critical point (-1, 0)
critical_layer = (
    alt.Chart(critical_df)
    .mark_point(shape="cross", size=500, strokeWidth=4, color="#d62728", filled=False)
    .encode(
        x=alt.X("real:Q", scale=x_scale),
        y=alt.Y("imaginary:Q", scale=y_scale),
        tooltip=[alt.Tooltip("label:N", title="Critical Point")],
    )
)

critical_text = (
    alt.Chart(critical_df)
    .mark_text(fontSize=17, fontWeight="bold", color="#c5211e", align="left", dx=18, dy=-14)
    .encode(x=alt.X("real:Q", scale=x_scale), y=alt.Y("imaginary:Q", scale=y_scale), text="label:N")
)

# Layer: Frequency annotation points
freq_points = (
    alt.Chart(freq_df)
    .mark_point(shape="circle", size=200, color="#306998", filled=True, opacity=0.85)
    .encode(
        x=alt.X("real:Q", scale=x_scale),
        y=alt.Y("imaginary:Q", scale=y_scale),
        tooltip=[alt.Tooltip("label:N", title="Frequency")],
    )
)

freq_labels = (
    alt.Chart(freq_df)
    .mark_text(fontSize=13, color="#444444", align="left", dx=12)
    .encode(x=alt.X("real:Q", scale=x_scale), y=alt.Y("imaginary:Q", scale=y_scale), text="label:N")
)

# Layer: Direction arrows
arrow_up_df = arrow_df[arrow_df["shape"] == "up"].copy()
arrow_down_df = arrow_df[arrow_df["shape"] == "down"].copy()

arrow_up_layer = (
    alt.Chart(arrow_up_df)
    .mark_point(shape="triangle-up", size=280, filled=True, opacity=0.85)
    .encode(
        x=alt.X("ax:Q", scale=x_scale),
        y=alt.Y("ay:Q", scale=y_scale),
        color=alt.Color("branch:N", scale=alt.Scale(domain=branch_domain, range=branch_palette), legend=None),
    )
)

arrow_down_layer = (
    alt.Chart(arrow_down_df)
    .mark_point(shape="triangle-down", size=280, filled=True, opacity=0.85)
    .encode(
        x=alt.X("ax:Q", scale=x_scale),
        y=alt.Y("ay:Q", scale=y_scale),
        color=alt.Color("branch:N", scale=alt.Scale(domain=branch_domain, range=branch_palette), legend=None),
    )
)

# Compose
chart = (
    (
        unit_circle_layer
        + nyquist_layer
        + critical_layer
        + critical_text
        + freq_points
        + freq_labels
        + arrow_up_layer
        + arrow_down_layer
    )
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(
            "nyquist-basic · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            color="#1a1a1a",
            subtitle="G(s) = 5 / (s+1)(0.5s+1)(0.1s+1)  ·  Open-Loop Frequency Response",
            subtitleFontSize=18,
            subtitleColor="#555555",
            subtitlePadding=10,
            anchor="start",
            offset=10,
        ),
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
