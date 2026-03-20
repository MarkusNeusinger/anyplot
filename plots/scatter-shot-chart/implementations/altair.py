""" pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Realistic basketball shot attempts
np.random.seed(42)

close_angles = np.random.uniform(0.15, np.pi - 0.15, 100)
close_dist = np.random.uniform(1.5, 8, 100)

mid_angles = np.random.uniform(0.2, np.pi - 0.2, 100)
mid_dist = np.random.uniform(8, 22, 100)

three_angles = np.random.uniform(0.35, np.pi - 0.35, 80)
three_dist = np.random.uniform(23.5, 27, 80)

ft_angles = np.random.uniform(np.pi / 2 - 0.08, np.pi / 2 + 0.08, 20)
ft_dist = np.full(20, 13.75) + np.random.normal(0, 0.3, 20)

x = np.concatenate(
    [
        close_dist * np.cos(close_angles),
        mid_dist * np.cos(mid_angles),
        three_dist * np.cos(three_angles),
        ft_dist * np.cos(ft_angles),
    ]
)
y = np.concatenate(
    [
        close_dist * np.sin(close_angles),
        mid_dist * np.sin(mid_angles),
        three_dist * np.sin(three_angles),
        ft_dist * np.sin(ft_angles),
    ]
)

shot_type = ["2-pointer"] * 200 + ["3-pointer"] * 80 + ["free-throw"] * 20
make_probs = np.concatenate([np.full(100, 0.55), np.full(100, 0.40), np.full(80, 0.35), np.full(20, 0.80)])
made = np.random.binomial(1, make_probs).astype(bool)

shots_df = pd.DataFrame(
    {
        "x": np.clip(x, -24.5, 24.5),
        "y": np.clip(y, -4, 40),
        "result": np.where(made, "Made", "Missed"),
        "shot_type": shot_type,
    }
)

# Court geometry (NBA half-court, basket at origin)
court_lines = []


def add_seg(xs, ys, seg_id):
    for i, (xi, yi) in enumerate(zip(xs, ys, strict=True)):
        court_lines.append({"cx": float(xi), "cy": float(yi), "seg": seg_id, "ord": i})


# Outer boundary
add_seg([-25, -25], [-5.25, 41.75], "sideline_l")
add_seg([25, 25], [-5.25, 41.75], "sideline_r")
add_seg([-25, 25], [-5.25, -5.25], "baseline")
add_seg([-25, 25], [41.75, 41.75], "halfcourt")

# Paint / key (16 ft wide, baseline to free-throw line)
add_seg([-8, -8], [-5.25, 13.75], "paint_l")
add_seg([8, 8], [-5.25, 13.75], "paint_r")
add_seg([-8, 8], [13.75, 13.75], "ft_line")

# Free-throw circle top half (radius 6 ft)
theta_ft = np.linspace(0, np.pi, 60)
add_seg(6 * np.cos(theta_ft), 13.75 + 6 * np.sin(theta_ft), "ft_circle")

# Three-point line
corner_y = np.sqrt(23.75**2 - 22**2)
add_seg([-22, -22], [-5.25, corner_y], "corner3_l")
add_seg([22, 22], [-5.25, corner_y], "corner3_r")
theta_3 = np.linspace(np.arccos(22 / 23.75), np.pi - np.arccos(22 / 23.75), 100)
add_seg(23.75 * np.cos(theta_3), 23.75 * np.sin(theta_3), "three_arc")

# Restricted area (4 ft radius)
theta_ra = np.linspace(0, np.pi, 40)
add_seg(4 * np.cos(theta_ra), 4 * np.sin(theta_ra), "restricted")

# Basket ring and backboard
theta_b = np.linspace(0, 2 * np.pi + 0.1, 40)
add_seg(0.75 * np.cos(theta_b), 0.75 * np.sin(theta_b), "basket")
add_seg([-3, 3], [-1.0, -1.0], "backboard")

# Center court semi-circle (bottom half)
theta_cc = np.linspace(np.pi, 2 * np.pi, 40)
add_seg(6 * np.cos(theta_cc), 41.75 + 6 * np.sin(theta_cc), "center_circle")

court_df = pd.DataFrame(court_lines)

# Scales (equal domain range for 1:1 aspect ratio)
x_scale = alt.Scale(domain=[-26, 26], nice=False)
y_scale = alt.Scale(domain=[-7, 45], nice=False)

# Court lines layer
court = (
    alt.Chart(court_df)
    .mark_line(strokeWidth=1.8, color="#888888")
    .encode(
        x=alt.X("cx:Q", scale=x_scale, axis=None),
        y=alt.Y("cy:Q", scale=y_scale, axis=None),
        detail="seg:N",
        order="ord:Q",
    )
)

# Shot markers layer
shots = (
    alt.Chart(shots_df)
    .mark_point(filled=True, size=100, opacity=0.8, strokeWidth=0.6, stroke="white")
    .encode(
        x=alt.X("x:Q", scale=x_scale),
        y=alt.Y("y:Q", scale=y_scale),
        color=alt.Color(
            "result:N",
            scale=alt.Scale(domain=["Made", "Missed"], range=["#27ae60", "#c0392b"]),
            legend=alt.Legend(
                title="Shot Result", titleFontSize=18, labelFontSize=16, symbolSize=150, orient="top-right", offset=10
            ),
        ),
        shape=alt.Shape("result:N", scale=alt.Scale(domain=["Made", "Missed"], range=["circle", "cross"]), legend=None),
        tooltip=[
            alt.Tooltip("shot_type:N", title="Shot Type"),
            alt.Tooltip("result:N", title="Result"),
            alt.Tooltip("x:Q", title="X (ft)", format=".1f"),
            alt.Tooltip("y:Q", title="Y (ft)", format=".1f"),
        ],
    )
)

# Compose
chart = (
    (court + shots)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(
            "scatter-shot-chart · altair · pyplots.ai",
            fontSize=28,
            color="#222222",
            subtitle="NBA Player Shot Chart — 300 Attempts (FG 44%)",
            subtitleFontSize=16,
            subtitleColor="#777777",
            subtitlePadding=6,
        ),
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
