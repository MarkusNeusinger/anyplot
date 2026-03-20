""" pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-20
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

# Court geometry (NBA half-court, basket at origin) — flat data construction
theta_ft = np.linspace(0, np.pi, 60)
theta_3 = np.linspace(np.arccos(22 / 23.75), np.pi - np.arccos(22 / 23.75), 100)
theta_ra = np.linspace(0, np.pi, 40)
theta_b = np.linspace(0, 2 * np.pi + 0.1, 40)
theta_cc = np.linspace(np.pi, 2 * np.pi, 40)
corner_y = np.sqrt(23.75**2 - 22**2)

# Build all court segments as (xs_array, ys_array, segment_name)
segments = [
    ([-25, -25], [-5.25, 41.75], "sideline_l"),
    ([25, 25], [-5.25, 41.75], "sideline_r"),
    ([-25, 25], [-5.25, -5.25], "baseline"),
    ([-25, 25], [41.75, 41.75], "halfcourt"),
    ([-8, -8], [-5.25, 13.75], "paint_l"),
    ([8, 8], [-5.25, 13.75], "paint_r"),
    ([-8, 8], [13.75, 13.75], "ft_line"),
    (6 * np.cos(theta_ft), 13.75 + 6 * np.sin(theta_ft), "ft_circle"),
    ([-22, -22], [-5.25, corner_y], "corner3_l"),
    ([22, 22], [-5.25, corner_y], "corner3_r"),
    (23.75 * np.cos(theta_3), 23.75 * np.sin(theta_3), "three_arc"),
    (4 * np.cos(theta_ra), 4 * np.sin(theta_ra), "restricted"),
    (0.75 * np.cos(theta_b), 0.75 * np.sin(theta_b), "basket"),
    ([-3, 3], [-1.0, -1.0], "backboard"),
    (6 * np.cos(theta_cc), 41.75 + 6 * np.sin(theta_cc), "center_circle"),
]

court_lines = []
for xs, ys, seg_name in segments:
    for i, (xi, yi) in enumerate(zip(xs, ys, strict=True)):
        court_lines.append({"cx": float(xi), "cy": float(yi), "seg": seg_name, "ord": i})

court_df = pd.DataFrame(court_lines)

# Zone annotations with shooting percentages
paint_mask = (shots_df["y"] < 13.75) & (shots_df["x"].abs() < 8) & (shots_df["shot_type"] != "free-throw")
mid_mask = (shots_df["shot_type"] == "2-pointer") & ~((shots_df["y"] < 13.75) & (shots_df["x"].abs() < 8))
three_mask = shots_df["shot_type"] == "3-pointer"

paint_pct = int(100 * shots_df.loc[paint_mask, "result"].eq("Made").mean())
mid_pct = int(100 * shots_df.loc[mid_mask, "result"].eq("Made").mean())
three_pct = int(100 * shots_df.loc[three_mask, "result"].eq("Made").mean())
total_fg = int(100 * shots_df["result"].eq("Made").mean())

zone_df = pd.DataFrame(
    [
        {"label": f"Paint: {paint_pct}%", "zx": 0, "zy": 6},
        {"label": f"Mid-Range: {mid_pct}%", "zx": 0, "zy": 20},
        {"label": f"3PT: {three_pct}%", "zx": 0, "zy": 30},
    ]
)

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

# Shot markers layer — size and opacity tuned for 300 points
shots = (
    alt.Chart(shots_df)
    .mark_point(filled=True, size=50, opacity=0.55, strokeWidth=0.5, stroke="white")
    .encode(
        x=alt.X("x:Q", scale=x_scale),
        y=alt.Y("y:Q", scale=y_scale),
        color=alt.Color(
            "result:N",
            scale=alt.Scale(domain=["Made", "Missed"], range=["#306998", "#e67e22"]),
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

# Zone annotation layer
zones = (
    alt.Chart(zone_df)
    .mark_text(fontSize=15, fontWeight="bold", color="#555555", opacity=0.7)
    .encode(x=alt.X("zx:Q", scale=x_scale), y=alt.Y("zy:Q", scale=y_scale), text="label:N")
)

# Compose
chart = (
    (court + shots + zones)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(
            "scatter-shot-chart · altair · pyplots.ai",
            fontSize=28,
            color="#222222",
            subtitle=f"NBA Player Shot Chart — 300 Attempts (FG {total_fg}%)",
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
