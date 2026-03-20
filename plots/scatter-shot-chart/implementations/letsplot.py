"""pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
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
    layer_tooltips,
    scale_color_identity,
    scale_fill_identity,
    scale_shape_identity,
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
        np.random.uniform(-22, 22, 50),
        np.random.normal(-22, 1.5, 28),
        np.random.normal(22, 1.5, 28),
        np.random.normal(-18, 3, 20),
        np.random.normal(18, 3, 20),
        np.random.normal(0, 10, 64),
    ]
)
shot_y = np.concatenate(
    [
        np.random.uniform(0, 6, 60),
        np.random.uniform(5, 15, 80),
        np.random.uniform(14, 24, 50),
        np.random.uniform(0, 12, 28),
        np.random.uniform(0, 12, 28),
        np.random.uniform(0, 8, 20),
        np.random.uniform(0, 8, 20),
        np.random.uniform(20, 30, 64),
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

# Colorblind-safe palette: blue for made, orange for missed
made_color = "#1F77B4"
missed_color = "#E87D2F"

# Zone classification for storytelling
zone = np.full(n_shots, "Mid-Range", dtype=object)
zone[dist < 6] = "Paint"
zone[(np.abs(shot_x) < 8) & (shot_y >= 6) & (shot_y <= 19)] = "Mid-Range"
zone[is_three & ~is_corner_three] = "Above Break 3"
zone[is_corner_three] = "Corner 3"
zone[is_free_throw] = "Free Throw"

df = pd.DataFrame(
    {
        "x": shot_x,
        "y": shot_y,
        "made": made,
        "shot_type": shot_type,
        "zone": zone,
        "result": np.where(made, "Made", "Missed"),
        "color": np.where(made, made_color, missed_color),
        "fill": np.where(made, made_color, missed_color),
        "point_size": np.where(made, 3.0, 2.5),
        "point_shape": np.where(made, 21, 4),  # circle vs X
    }
)

# Zone FG% for annotations
zone_stats = {}
for z in ["Paint", "Mid-Range", "Above Break 3", "Corner 3"]:
    mask = zone == z
    if mask.sum() > 0:
        zone_stats[z] = (made[mask].sum() / mask.sum() * 100, int(mask.sum()))

# Court geometry (NBA half-court: 50 ft wide x 47 ft deep)
court_color = "#E8DCC8"
line_color = "#555555"

# Three-point arc
theta_3pt = np.linspace(-np.pi / 2 + 0.38, np.pi / 2 - 0.38, 100)
df_three_arc = pd.DataFrame({"x": 23.75 * np.cos(theta_3pt), "y": 23.75 * np.sin(theta_3pt)})

# Free-throw circle (solid upper, dashed lower)
theta_ft_upper = np.linspace(0, np.pi, 60)
df_ft_arc = pd.DataFrame({"x": 6 * np.cos(theta_ft_upper), "y": 15 + 6 * np.sin(theta_ft_upper)})
theta_ft_lower = np.linspace(np.pi, 2 * np.pi, 60)
df_ft_dash = pd.DataFrame({"x": 6 * np.cos(theta_ft_lower), "y": 15 + 6 * np.sin(theta_ft_lower)})

# Restricted area arc
theta_ra = np.linspace(0, np.pi, 40)
df_restricted = pd.DataFrame({"x": 4 * np.cos(theta_ra), "y": 4 * np.sin(theta_ra)})

n_made = int(made.sum())
n_missed = int((~made).sum())
fg_percent = n_made / n_shots * 100

# Zone annotation positions and labels
zone_annotations = pd.DataFrame(
    {
        "x": [0, 13, 0, -14],
        "y": [1.5, 10, 29, 14],
        "label": [
            f"Paint: {zone_stats['Paint'][0]:.0f}% ({zone_stats['Paint'][1]})",
            f"Mid-Range: {zone_stats['Mid-Range'][0]:.0f}% ({zone_stats['Mid-Range'][1]})",
            f"3PT: {zone_stats['Above Break 3'][0]:.0f}% ({zone_stats['Above Break 3'][1]})",
            f"Corner 3: {zone_stats['Corner 3'][0]:.0f}% ({zone_stats['Corner 3'][1]})",
        ],
    }
)

legend_y = -8
df_legend = pd.DataFrame(
    {
        "x": [-15, 3],
        "y": [legend_y, legend_y],
        "color": [made_color, missed_color],
        "fill": [made_color, missed_color],
        "shape": [21, 4],
    }
)
df_legend_text = pd.DataFrame(
    {"x": [-12.5, 5.5], "y": [legend_y, legend_y], "label": [f"Made ({n_made})", f"Missed ({n_missed})"]}
)

# Plot
plot = (
    ggplot()
    # Court background
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=pd.DataFrame({"xmin": [-28], "ymin": [-14], "xmax": [28], "ymax": [49]}),
        fill=court_color,
        color=court_color,
    )
    # Court boundary
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=pd.DataFrame({"xmin": [-25], "ymin": [-2], "xmax": [25], "ymax": [47]}),
        fill=court_color,
        color=line_color,
        size=1.2,
    )
    # Paint
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=pd.DataFrame({"xmin": [-8], "ymin": [0], "xmax": [8], "ymax": [19]}),
        fill="rgba(0,0,0,0)",
        color=line_color,
        size=1.0,
    )
    # Corner three-point lines
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pd.DataFrame({"x": [-22, 22], "y": [0, 0], "xend": [-22, 22], "yend": [14, 14]}),
        color=line_color,
        size=1.0,
    )
    # Three-point arc
    + geom_path(data=df_three_arc, mapping=aes(x="x", y="y"), color=line_color, size=1.0)
    # Free-throw circle
    + geom_path(data=df_ft_arc, mapping=aes(x="x", y="y"), color=line_color, size=1.0)
    + geom_path(data=df_ft_dash, mapping=aes(x="x", y="y"), color=line_color, size=0.6, linetype="dashed")
    # Restricted area
    + geom_path(data=df_restricted, mapping=aes(x="x", y="y"), color=line_color, size=1.0)
    # Backboard and rim
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pd.DataFrame({"x": [-3], "y": [-0.5], "xend": [3], "yend": [-0.5]}),
        color=line_color,
        size=2.0,
    )
    + geom_point(aes(x="x", y="y"), data=pd.DataFrame({"x": [0], "y": [1.25]}), color=line_color, size=3, shape=1)
    # Shot data with lets-plot tooltips (distinctive feature)
    + geom_point(
        data=df,
        mapping=aes(x="x", y="y", color="color", fill="fill", size="point_size", shape="point_shape"),
        stroke=0.3,
        alpha=0.45,
        tooltips=layer_tooltips().line("@result | @shot_type").line("Zone: @zone").line("Position: (@x, @y)"),
    )
    # Zone FG% annotations with semi-transparent background for readability
    + geom_text(
        data=zone_annotations,
        mapping=aes(x="x", y="y", label="label"),
        size=16,
        color="#1A1A1A",
        fontface="bold",
        label_padding=0.4,
        fill="rgba(232,220,200,0.85)",
        label_size=0,
    )
    # Overall FG% header
    + geom_text(
        data=pd.DataFrame({"x": [0], "y": [44], "label": [f"FG: {fg_percent:.1f}%  \u00b7  {n_made}/{n_shots}"]}),
        mapping=aes(x="x", y="y", label="label"),
        size=16,
        color="#333333",
        fontface="bold",
    )
    # Legend
    + geom_point(aes(x="x", y="y", color="color", fill="fill", shape="shape"), data=df_legend, size=5, stroke=0.5)
    + geom_text(data=df_legend_text, mapping=aes(x="x", y="y", label="label"), size=15, color="#333333", hjust=0)
    + scale_color_identity()
    + scale_fill_identity()
    + scale_size_identity()
    + scale_shape_identity()
    + coord_fixed(ratio=1)
    + xlim(-29, 29)
    + ylim(-14, 49)
    + labs(title="scatter-shot-chart \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=26, hjust=0.5, color="#1A1A1A", face="bold"),
        plot_background=element_rect(fill="#F5F0E8", color="#F5F0E8"),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(900, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=4)
ggsave(plot, "plot.html", path=".")
