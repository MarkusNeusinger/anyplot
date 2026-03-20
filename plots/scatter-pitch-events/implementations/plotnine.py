"""pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: plotnine 0.15.3 | Python 3.14.3
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    arrow,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_alpha_manual,
    scale_color_manual,
    scale_shape_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Data
np.random.seed(42)

n_events = 120
event_types = np.random.choice(["Pass", "Shot", "Tackle", "Interception"], size=n_events, p=[0.50, 0.15, 0.20, 0.15])

# Vectorized position generation with event-specific distributions
x_ranges = {"Pass": (10, 95), "Shot": (65, 100), "Tackle": (15, 80), "Interception": (20, 75)}
y_ranges = {"Pass": (5, 63), "Shot": (15, 53), "Tackle": (5, 63), "Interception": (5, 63)}
success_p = {"Pass": 0.75, "Shot": 0.30, "Tackle": 0.65, "Interception": 0.70}

x_positions = np.array([np.random.uniform(*x_ranges[e]) for e in event_types])
y_positions = np.array([np.random.uniform(*y_ranges[e]) for e in event_types])
outcomes = [np.random.choice(["Successful", "Unsuccessful"], p=[success_p[e], 1 - success_p[e]]) for e in event_types]

# Arrow endpoints: passes forward-biased, shots toward goal, others stay in place
x_end = x_positions.copy()
y_end = y_positions.copy()
for i, evt in enumerate(event_types):
    if evt == "Pass":
        dx = np.random.uniform(5, 20) * np.random.choice([-1, 1], p=[0.15, 0.85])
        dy = np.random.uniform(-12, 12)
        x_end[i] = np.clip(x_positions[i] + dx, 0, 105)
        y_end[i] = np.clip(y_positions[i] + dy, 0, 68)
    elif evt == "Shot":
        x_end[i] = 105
        y_end[i] = np.random.uniform(28, 40)

df = pd.DataFrame(
    {
        "x": x_positions,
        "y": y_positions,
        "x_end": x_end,
        "y_end": y_end,
        "event_type": pd.Categorical(event_types, categories=["Pass", "Shot", "Tackle", "Interception"]),
        "outcome": pd.Categorical(outcomes, categories=["Successful", "Unsuccessful"]),
    }
)

# Separate layers for visual hierarchy
df_shots = df[df["event_type"] == "Shot"].copy()
df_other = df[df["event_type"] != "Shot"].copy()
df_pass_arrows = df[df["event_type"] == "Pass"].copy()
df_shot_arrows = df[df["event_type"] == "Shot"].copy()

# Pitch styling — deep green with cream white lines for a premium look
pitch_color = "#1a6b30"
line_color = "#ffffffcc"
lw = 0.7

# Center circle
theta = np.linspace(0, 2 * np.pi, 100)
center_circle = pd.DataFrame({"cx": 52.5 + 9.15 * np.cos(theta), "cy": 34 + 9.15 * np.sin(theta), "grp": 1})

# Penalty arcs
theta_left = np.linspace(-0.65, 0.65, 50)
left_arc = pd.DataFrame({"cx": 11 + 9.15 * np.cos(theta_left), "cy": 34 + 9.15 * np.sin(theta_left), "grp": 2})
theta_right = np.linspace(np.pi - 0.65, np.pi + 0.65, 50)
right_arc = pd.DataFrame({"cx": 94 + 9.15 * np.cos(theta_right), "cy": 34 + 9.15 * np.sin(theta_right), "grp": 3})

# Corner arcs
ca_r = 1.0
corner_arcs = pd.concat(
    [
        pd.DataFrame(
            {
                "cx": ca_r * np.cos(np.linspace(0, np.pi / 2, 20)),
                "cy": ca_r * np.sin(np.linspace(0, np.pi / 2, 20)),
                "grp": 4,
            }
        ),
        pd.DataFrame(
            {
                "cx": ca_r * np.cos(np.linspace(np.pi / 2, np.pi, 20)),
                "cy": 68 + ca_r * np.sin(np.linspace(np.pi / 2, np.pi, 20)),
                "grp": 5,
            }
        ),
        pd.DataFrame(
            {
                "cx": 105 + ca_r * np.cos(np.linspace(-np.pi / 2, 0, 20)),
                "cy": ca_r * np.sin(np.linspace(-np.pi / 2, 0, 20)),
                "grp": 6,
            }
        ),
        pd.DataFrame(
            {
                "cx": 105 + ca_r * np.cos(np.linspace(np.pi, 3 * np.pi / 2, 20)),
                "cy": 68 + ca_r * np.sin(np.linspace(np.pi, 3 * np.pi / 2, 20)),
                "grp": 7,
            }
        ),
    ],
    ignore_index=True,
)

all_curves = pd.concat([center_circle, left_arc, right_arc, corner_arcs], ignore_index=True)

# Colorblind-safe palette: blue, red, orange, teal — all perceptually distinct
event_colors = {"Pass": "#4a90d9", "Shot": "#d94452", "Tackle": "#e8913a", "Interception": "#17a589"}
event_shapes = {"Pass": "o", "Shot": "*", "Tackle": "^", "Interception": "D"}
# Plot
plot = (
    ggplot(df, aes(x="x", y="y", color="event_type", shape="event_type", alpha="outcome"))
    # Pitch background — extended to fill canvas edges
    + annotate("rect", xmin=-5, xmax=110, ymin=-5, ymax=73, fill=pitch_color, color=pitch_color)
    # Subtle pitch grass stripe effect (lighter bands)
    + annotate("rect", xmin=0, xmax=105, ymin=0, ymax=68, fill="#1e7535", alpha=0.3, color="none")
    # Pitch outline
    + annotate("rect", xmin=0, xmax=105, ymin=0, ymax=68, fill="none", color=line_color, size=lw)
    # Halfway line
    + annotate("segment", x=52.5, xend=52.5, y=0, yend=68, color=line_color, size=lw)
    # Center spot
    + annotate("point", x=52.5, y=34, color=line_color, size=1.8, shape="o", fill=line_color)
    # Left penalty area
    + annotate("rect", xmin=0, xmax=16.5, ymin=13.84, ymax=54.16, fill="none", color=line_color, size=lw)
    # Right penalty area
    + annotate("rect", xmin=88.5, xmax=105, ymin=13.84, ymax=54.16, fill="none", color=line_color, size=lw)
    # Left goal area
    + annotate("rect", xmin=0, xmax=5.5, ymin=24.84, ymax=43.16, fill="none", color=line_color, size=lw)
    # Right goal area
    + annotate("rect", xmin=99.5, xmax=105, ymin=24.84, ymax=43.16, fill="none", color=line_color, size=lw)
    # Penalty spots
    + annotate("point", x=11, y=34, color=line_color, size=1.2, shape="o", fill=line_color)
    + annotate("point", x=94, y=34, color=line_color, size=1.2, shape="o", fill=line_color)
    # Left goal
    + annotate("segment", x=-2, xend=-2, y=30.34, yend=37.66, color="#ffffff", size=1.5)
    + annotate("segment", x=-2, xend=0, y=30.34, yend=30.34, color="#ffffff", size=0.5)
    + annotate("segment", x=-2, xend=0, y=37.66, yend=37.66, color="#ffffff", size=0.5)
    # Right goal
    + annotate("segment", x=107, xend=107, y=30.34, yend=37.66, color="#ffffff", size=1.5)
    + annotate("segment", x=105, xend=107, y=30.34, yend=30.34, color="#ffffff", size=0.5)
    + annotate("segment", x=105, xend=107, y=37.66, yend=37.66, color="#ffffff", size=0.5)
    # Curves: center circle, penalty arcs, corner arcs
    + geom_path(data=all_curves, mapping=aes(x="cx", y="cy", group="grp"), color=line_color, size=lw, inherit_aes=False)
    # Pass arrows — thin and subtle to avoid midfield clutter
    + geom_segment(
        data=df_pass_arrows,
        mapping=aes(x="x", y="y", xend="x_end", yend="y_end", alpha="outcome"),
        color=event_colors["Pass"],
        size=0.4,
        arrow=arrow(length=0.10, type="open"),
        inherit_aes=False,
    )
    # Shot arrows — bolder to emphasize attacking intent
    + geom_segment(
        data=df_shot_arrows,
        mapping=aes(x="x", y="y", xend="x_end", yend="y_end", alpha="outcome"),
        color=event_colors["Shot"],
        size=0.9,
        arrow=arrow(length=0.18, type="open"),
        inherit_aes=False,
    )
    # Non-shot markers
    + geom_point(data=df_other, size=4.5, stroke=0.4)
    # Shot markers — larger for focal emphasis
    + geom_point(data=df_shots, size=8, stroke=0.4)
    # Scales
    + scale_color_manual(values=event_colors, name="Event Type")
    + scale_shape_manual(values=event_shapes, name="Event Type")
    + scale_alpha_manual(values={"Successful": 0.92, "Unsuccessful": 0.40}, name="Outcome")
    + scale_x_continuous(limits=(-5, 110), breaks=[])
    + scale_y_continuous(limits=(-5, 73), breaks=[])
    + coord_fixed(ratio=1)
    + labs(
        title="scatter-pitch-events · plotnine · pyplots.ai",
        subtitle="Match events: 120 actions across passes, shots, tackles & interceptions",
    )
    + guides(
        color=guide_legend(override_aes={"size": 5}),
        alpha=guide_legend(override_aes={"size": 5, "alpha": [0.92, 0.40]}),
    )
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a", margin={"b": 4}),
        plot_subtitle=element_text(size=16, color="#555555", style="italic", margin={"b": 12}),
        panel_background=element_rect(fill=pitch_color, color="none"),
        plot_background=element_rect(fill="#f5f5f0", color="none"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        legend_title=element_text(size=16, weight="bold", color="#2a2a2a"),
        legend_text=element_text(size=14, color="#3a3a3a"),
        legend_position="right",
        legend_background=element_rect(fill="#f5f5f0", color="none"),
        legend_key=element_rect(fill="#f5f5f0", color="none"),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
