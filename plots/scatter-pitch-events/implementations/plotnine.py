""" pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
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

x_positions = np.zeros(n_events)
y_positions = np.zeros(n_events)
outcomes = []
x_end = np.zeros(n_events)
y_end = np.zeros(n_events)

for i, evt in enumerate(event_types):
    if evt == "Pass":
        x_positions[i] = np.random.uniform(10, 95)
        y_positions[i] = np.random.uniform(5, 63)
        dx = np.random.uniform(5, 25) * np.random.choice([-1, 1], p=[0.15, 0.85])
        dy = np.random.uniform(-15, 15)
        x_end[i] = np.clip(x_positions[i] + dx, 0, 105)
        y_end[i] = np.clip(y_positions[i] + dy, 0, 68)
        outcomes.append(np.random.choice(["Successful", "Unsuccessful"], p=[0.75, 0.25]))
    elif evt == "Shot":
        x_positions[i] = np.random.uniform(65, 100)
        y_positions[i] = np.random.uniform(15, 53)
        x_end[i] = 105
        y_end[i] = np.random.uniform(28, 40)
        outcomes.append(np.random.choice(["Successful", "Unsuccessful"], p=[0.30, 0.70]))
    elif evt == "Tackle":
        x_positions[i] = np.random.uniform(15, 80)
        y_positions[i] = np.random.uniform(5, 63)
        x_end[i] = x_positions[i]
        y_end[i] = y_positions[i]
        outcomes.append(np.random.choice(["Successful", "Unsuccessful"], p=[0.65, 0.35]))
    else:
        x_positions[i] = np.random.uniform(20, 75)
        y_positions[i] = np.random.uniform(5, 63)
        x_end[i] = x_positions[i]
        y_end[i] = y_positions[i]
        outcomes.append(np.random.choice(["Successful", "Unsuccessful"], p=[0.70, 0.30]))

df = pd.DataFrame(
    {
        "x": x_positions,
        "y": y_positions,
        "x_end": x_end,
        "y_end": y_end,
        "event_type": pd.Categorical(event_types, categories=["Pass", "Shot", "Tackle", "Interception"]),
        "outcome": outcomes,
    }
)

# Split data for visual hierarchy: shots rendered larger as focal point
df_shots = df[df["event_type"] == "Shot"].copy()
df_other = df[df["event_type"] != "Shot"].copy()
arrows_df = df[df["event_type"].isin(["Pass", "Shot"])].copy()

# Pitch markings
pitch_color = "#2d8c3c"
line_color = "white"
lw = 0.8

# Center circle path
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

# Event colors and shapes — colorblind-friendly (orange replaces teal for tackles)
event_colors = {"Pass": "#306998", "Shot": "#e74c3c", "Tackle": "#e67e22", "Interception": "#9b59b6"}
event_shapes = {"Pass": "o", "Shot": "*", "Tackle": "^", "Interception": "D"}

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", color="event_type", shape="event_type", alpha="outcome"))
    # Pitch background
    + annotate("rect", xmin=-2, xmax=107, ymin=-2, ymax=70, fill=pitch_color, color=pitch_color)
    # Pitch outline
    + annotate("rect", xmin=0, xmax=105, ymin=0, ymax=68, fill="none", color=line_color, size=lw)
    # Halfway line
    + annotate("segment", x=52.5, xend=52.5, y=0, yend=68, color=line_color, size=lw)
    # Center spot
    + annotate("point", x=52.5, y=34, color=line_color, size=2, shape="o", fill=line_color)
    # Left penalty area
    + annotate("rect", xmin=0, xmax=16.5, ymin=13.84, ymax=54.16, fill="none", color=line_color, size=lw)
    # Right penalty area
    + annotate("rect", xmin=88.5, xmax=105, ymin=13.84, ymax=54.16, fill="none", color=line_color, size=lw)
    # Left goal area
    + annotate("rect", xmin=0, xmax=5.5, ymin=24.84, ymax=43.16, fill="none", color=line_color, size=lw)
    # Right goal area
    + annotate("rect", xmin=99.5, xmax=105, ymin=24.84, ymax=43.16, fill="none", color=line_color, size=lw)
    # Penalty spots
    + annotate("point", x=11, y=34, color=line_color, size=1.5, shape="o", fill=line_color)
    + annotate("point", x=94, y=34, color=line_color, size=1.5, shape="o", fill=line_color)
    # Left goal
    + annotate("segment", x=-2, xend=-2, y=30.34, yend=37.66, color=line_color, size=1.5)
    + annotate("segment", x=-2, xend=0, y=30.34, yend=30.34, color=line_color, size=0.5)
    + annotate("segment", x=-2, xend=0, y=37.66, yend=37.66, color=line_color, size=0.5)
    # Right goal
    + annotate("segment", x=107, xend=107, y=30.34, yend=37.66, color=line_color, size=1.5)
    + annotate("segment", x=105, xend=107, y=30.34, yend=30.34, color=line_color, size=0.5)
    + annotate("segment", x=105, xend=107, y=37.66, yend=37.66, color=line_color, size=0.5)
    # Center circle, penalty arcs, and corner arcs
    + geom_path(data=all_curves, mapping=aes(x="cx", y="cy", group="grp"), color=line_color, size=lw, inherit_aes=False)
    # Directional arrows for passes and shots
    + geom_segment(
        data=arrows_df,
        mapping=aes(x="x", y="y", xend="x_end", yend="y_end", color="event_type", alpha="outcome"),
        size=0.8,
        arrow=arrow(length=0.15, type="open"),
        inherit_aes=False,
    )
    # Non-shot markers (standard size)
    + geom_point(data=df_other, size=4.5, stroke=0.5)
    # Shot markers (larger for visual emphasis)
    + geom_point(data=df_shots, size=7, stroke=0.5)
    + scale_color_manual(values=event_colors, name="Event Type")
    + scale_shape_manual(values=event_shapes, name="Event Type")
    + scale_alpha_manual(values={"Successful": 0.9, "Unsuccessful": 0.5}, name="Outcome")
    + scale_x_continuous(limits=(-4, 109), breaks=[])
    + scale_y_continuous(limits=(-4, 72), breaks=[])
    + coord_fixed(ratio=1)
    + labs(title="scatter-pitch-events · plotnine · pyplots.ai")
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a"),
        panel_background=element_rect(fill=pitch_color, color="none"),
        plot_background=element_rect(fill="#f0f0f0", color="none"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_background=element_rect(fill="#f0f0f0", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
