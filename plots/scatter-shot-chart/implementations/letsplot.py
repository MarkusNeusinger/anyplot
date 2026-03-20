""" pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_identity,
    scale_fill_identity,
    scale_size_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Data
np.random.seed(42)

n_shots = 350
shot_x = np.concatenate(
    [
        np.random.normal(0, 3, 60),
        np.random.normal(0, 8, 80),
        np.random.uniform(-22, 22, 70),
        np.random.normal(-18, 3, 35),
        np.random.normal(18, 3, 35),
        np.random.normal(0, 10, 70),
    ]
)
shot_y = np.concatenate(
    [
        np.random.uniform(0, 6, 60),
        np.random.uniform(5, 15, 80),
        np.random.uniform(14, 24, 70),
        np.random.uniform(0, 8, 35),
        np.random.uniform(0, 8, 35),
        np.random.uniform(20, 30, 70),
    ]
)

shot_x = np.clip(shot_x, -25, 25)
shot_y = np.clip(shot_y, 0, 40)

three_pt_dist = np.sqrt(shot_x**2 + shot_y**2)
is_corner_three = (np.abs(shot_x) > 22) & (shot_y < 14)
is_three = (three_pt_dist > 23.75) | is_corner_three
is_free_throw = (np.abs(shot_x) < 1) & (np.abs(shot_y - 15) < 1)

shot_type = np.where(is_free_throw, "free-throw", np.where(is_three, "3-pointer", "2-pointer"))

base_pct = np.where(shot_type == "free-throw", 0.75, np.where(shot_type == "2-pointer", 0.48, 0.36))
dist = np.sqrt(shot_x**2 + shot_y**2)
fg_pct = np.clip(base_pct - dist * 0.005, 0.15, 0.85)
made = np.random.random(n_shots) < fg_pct

made_color = "#2E8B57"
missed_color = "#DC3545"

df = pd.DataFrame(
    {
        "x": shot_x,
        "y": shot_y,
        "made": made,
        "shot_type": shot_type,
        "color": np.where(made, made_color, missed_color),
        "fill": np.where(made, made_color, missed_color),
        "point_size": np.where(made, 4.5, 3.5),
        "alpha": np.where(made, 0.85, 0.55),
    }
)

# Court geometry (NBA half-court: 50 ft wide x 47 ft deep)
court_color = "#E8DCC8"
line_color = "#555555"

df_court = pd.DataFrame({"xmin": [-25], "ymin": [-2], "xmax": [25], "ymax": [47]})

df_paint = pd.DataFrame({"xmin": [-8], "ymin": [0], "xmax": [8], "ymax": [19]})

theta_3pt = np.linspace(-np.pi / 2 + 0.38, np.pi / 2 - 0.38, 100)
arc_3pt_x = 23.75 * np.cos(theta_3pt)
arc_3pt_y = 23.75 * np.sin(theta_3pt)
df_three_arc = pd.DataFrame({"x": arc_3pt_x, "y": arc_3pt_y})

theta_ft = np.linspace(0, np.pi, 60)
ft_arc_x = 6 * np.cos(theta_ft)
ft_arc_y = 15 + 6 * np.sin(theta_ft)
df_ft_arc = pd.DataFrame({"x": ft_arc_x, "y": ft_arc_y})

theta_ft_dash = np.linspace(np.pi, 2 * np.pi, 60)
ft_dash_x = 6 * np.cos(theta_ft_dash)
ft_dash_y = 15 + 6 * np.sin(theta_ft_dash)
df_ft_dash = pd.DataFrame({"x": ft_dash_x, "y": ft_dash_y})

theta_restricted = np.linspace(0, np.pi, 40)
restricted_x = 4 * np.cos(theta_restricted)
restricted_y = 4 * np.sin(theta_restricted)
df_restricted = pd.DataFrame({"x": restricted_x, "y": restricted_y})

df_backboard = pd.DataFrame({"x": [-3], "y": [-0.5], "xend": [3], "yend": [-0.5]})
df_rim = pd.DataFrame({"x": [0], "y": [1.25]})

n_made = int(made.sum())
n_missed = int((~made).sum())
fg_percent = n_made / n_shots * 100

legend_y = -8
df_legend_made = pd.DataFrame({"x": [-12], "y": [legend_y]})
df_legend_missed = pd.DataFrame({"x": [2], "y": [legend_y]})
df_legend_text = pd.DataFrame(
    {"x": [-9.5, 4.5], "y": [legend_y, legend_y], "label": [f"Made ({n_made})", f"Missed ({n_missed})"]}
)

# Plot
plot = (
    ggplot()
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=pd.DataFrame({"xmin": [-28], "ymin": [-14], "xmax": [28], "ymax": [49]}),
        fill=court_color,
        color=court_color,
    )
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=df_court,
        fill=court_color,
        color=line_color,
        size=1.2,
    )
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=df_paint,
        fill="rgba(0,0,0,0)",
        color=line_color,
        size=1.0,
    )
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pd.DataFrame({"x": [-22], "y": [0], "xend": [-22], "yend": [14]}),
        color=line_color,
        size=1.0,
    )
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pd.DataFrame({"x": [22], "y": [0], "xend": [22], "yend": [14]}),
        color=line_color,
        size=1.0,
    )
    + geom_path(data=df_three_arc, mapping=aes(x="x", y="y"), color=line_color, size=1.0)
    + geom_path(data=df_ft_arc, mapping=aes(x="x", y="y"), color=line_color, size=1.0)
    + geom_path(data=df_ft_dash, mapping=aes(x="x", y="y"), color=line_color, size=0.6, linetype="dashed")
    + geom_path(data=df_restricted, mapping=aes(x="x", y="y"), color=line_color, size=1.0)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_backboard, color=line_color, size=2.0)
    + geom_point(aes(x="x", y="y"), data=df_rim, color=line_color, size=3, shape=1)
    + geom_point(
        data=df,
        mapping=aes(x="x", y="y", color="color", fill="fill", size="point_size"),
        shape=21,
        stroke=0.5,
        alpha=0.7,
    )
    + geom_point(
        aes(x="x", y="y"), data=df_legend_made, color=made_color, fill=made_color, size=5, shape=21, stroke=0.5
    )
    + geom_point(
        aes(x="x", y="y"), data=df_legend_missed, color=missed_color, fill=missed_color, size=5, shape=21, stroke=0.5
    )
    + geom_text(data=df_legend_text, mapping=aes(x="x", y="y", label="label"), size=13, color="#333333", hjust=0)
    + geom_text(
        data=pd.DataFrame({"x": [0], "y": [44], "label": [f"FG: {fg_percent:.1f}%  \u00b7  {n_made}/{n_shots}"]}),
        mapping=aes(x="x", y="y", label="label"),
        size=14,
        color="#444444",
    )
    + scale_color_identity()
    + scale_fill_identity()
    + scale_size_identity()
    + coord_fixed(ratio=1)
    + xlim(-29, 29)
    + ylim(-14, 49)
    + labs(title="scatter-shot-chart \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5, color="#222222", face="bold"),
        plot_background=element_rect(fill="#F5F5F0", color="#F5F5F0"),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(900, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=4)
ggsave(plot, "plot.html", path=".")
