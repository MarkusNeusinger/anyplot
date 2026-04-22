""" pyplots.ai
campbell-basic: Campbell Diagram
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-02-15
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data
np.random.seed(42)
speed_rpm = np.linspace(0, 6000, 80)
max_freq = 120

# Natural frequency modes (Hz) with realistic speed-dependent variation
# Gyroscopic effects: forward whirl modes increase, backward whirl modes decrease
modes = {
    "1st Bending": 25 + 0.0008 * speed_rpm + np.random.normal(0, 0.15, 80),
    "1st Torsional": 48 - 0.0005 * speed_rpm + np.random.normal(0, 0.12, 80),
    "2nd Bending": 72 + 0.0025 * speed_rpm + np.random.normal(0, 0.18, 80),
    "2nd Torsional": 88 + 0.0006 * speed_rpm + np.random.normal(0, 0.14, 80),
    "Axial": 105 - 0.0004 * speed_rpm + np.random.normal(0, 0.10, 80),
}

# Build long-format DataFrame for natural frequency modes
modes_df = pd.concat(
    [pd.DataFrame({"Speed": speed_rpm, "Frequency": freq, "Mode": name}) for name, freq in modes.items()],
    ignore_index=True,
)

# Engine order lines: frequency = order * speed_rpm / 60
orders = [1, 2, 3]
order_labels = ["1\u00d7", "2\u00d7", "3\u00d7"]

eo_df = pd.concat(
    [
        pd.DataFrame(
            {
                "Speed": np.linspace(0, min(6000, max_freq * 60 / o), 80),
                "Frequency": o * np.linspace(0, min(6000, max_freq * 60 / o), 80) / 60,
                "Order": lbl,
            }
        )
        for o, lbl in zip(orders, order_labels)
    ],
    ignore_index=True,
)

# Find critical speed intersections (EO lines crossing mode curves)
critical_rows = []
for order, olabel in zip(orders, order_labels):
    eo_at = order * speed_rpm / 60
    for mname, mfreq in modes.items():
        diff = eo_at - mfreq
        for idx in np.where(np.diff(np.sign(diff)))[0]:
            t = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            cs = speed_rpm[idx] + t * (speed_rpm[idx + 1] - speed_rpm[idx])
            cf = order * cs / 60
            if cf <= max_freq:
                critical_rows.append({"Speed": cs, "Frequency": cf, "Intersection": f"{mname} \u00d7 {olabel}"})

crit_df = pd.DataFrame(critical_rows)

# Highlight zones around critical speeds
zone_df = pd.DataFrame(
    [
        {"xmin": r["Speed"] - 150, "xmax": r["Speed"] + 150, "ymin": r["Frequency"] - 3.5, "ymax": r["Frequency"] + 3.5}
        for _, r in crit_df.iterrows()
    ]
)

# EO label positions along each line
eo_label_df = pd.DataFrame(
    [
        {"Speed": spd, "Frequency": eo * spd / 60 + 2.5, "Label": lbl}
        for eo, lbl, spd in zip(orders, order_labels, [5200, 3400, 2200])
    ]
)

# Colorblind-safe palette (blue-teal-amber-purple-gray) — avoids red-green confusion
mode_colors = ["#306998", "#17A589", "#D4A017", "#8E44AD", "#5D6D7E"]
mode_order = list(modes.keys())
eo_color = "#AAAAAA"
crit_color = "#C0392B"

# Annotate the most dangerous critical speed (highest frequency intersection)
danger_idx = crit_df["Frequency"].idxmax()
danger_row = crit_df.loc[danger_idx]
annot_df = pd.DataFrame(
    [
        {
            "Speed": danger_row["Speed"] + 250,
            "Frequency": danger_row["Frequency"] + 5,
            "Label": f"\u2190 {danger_row['Intersection']}\n    ({int(danger_row['Speed'])} RPM)",
        }
    ]
)

# Plot
plot = (
    ggplot()
    + geom_rect(
        data=zone_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=crit_color,
        alpha=0.08,
        color="transparent",
    )
    + geom_line(data=eo_df, mapping=aes(x="Speed", y="Frequency", linetype="Order"), color=eo_color, size=0.9)
    + geom_line(
        data=modes_df,
        mapping=aes(x="Speed", y="Frequency", color="Mode"),
        size=2.5,
        tooltips=layer_tooltips()
        .line("@{Mode}")
        .line("Speed|@{Speed} RPM")
        .line("Freq|@{Frequency} Hz")
        .format("Speed", ",.0f")
        .format("Frequency", ".1f"),
    )
    + geom_point(
        data=crit_df,
        mapping=aes(x="Speed", y="Frequency"),
        color=crit_color,
        fill=crit_color,
        size=8,
        shape=18,
        tooltips=layer_tooltips()
        .title("Critical Speed")
        .line("@{Intersection}")
        .line("Speed|@{Speed} RPM")
        .line("Freq|@{Frequency} Hz")
        .format("Speed", ",.0f")
        .format("Frequency", ".1f"),
    )
    + geom_text(
        data=eo_label_df,
        mapping=aes(x="Speed", y="Frequency", label="Label"),
        color="#777777",
        size=14,
        fontface="bold",
    )
    + geom_text(
        data=annot_df,
        mapping=aes(x="Speed", y="Frequency", label="Label"),
        color=crit_color,
        size=12,
        fontface="italic",
        hjust=0,
    )
    + scale_color_manual(name="Natural Frequency", values=mode_colors, limits=mode_order)
    + scale_linetype_manual(name="Engine Order", values=["dashed", "dashed", "dashed"])
    + scale_y_continuous(limits=[0, max_freq], expand=[0, 2])
    + scale_x_continuous(limits=[0, 6200], format=",d")
    + guides(linetype=guide_legend(override_aes={"color": eo_color}))
    + labs(
        title="campbell-basic \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Red diamonds mark critical speeds where engine order excitations cross natural frequency modes",
        x="Rotational Speed (RPM)",
        y="Frequency (Hz)",
        caption="Data: synthetic rotordynamic model | Highlight zones indicate resonance risk regions",
    )
    + flavor_high_contrast_light()
    + theme(
        plot_title=element_text(size=28, hjust=0.5, face="bold"),
        plot_subtitle=element_text(size=16, hjust=0.5, color="#555555"),
        plot_caption=element_text(size=13, color="#888888", face="italic"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_text(size=18, face="bold"),
        legend_text=element_text(size=16),
        legend_position=[0.02, 0.98],
        legend_justification=[0, 1],
        legend_background=element_rect(fill="white", color="#CCCCCC", size=0.5),
        panel_grid_major=element_line(color="#E5E5E5", size=0.3),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color="#BBBBBB", size=0.5),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
