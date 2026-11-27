"""anyplot.ai
campbell-basic: Campbell Diagram
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID_COLOR = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"  # INK at 15 %

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
# Modes take every palette position except #AE3030 (pos 5), reserved for critical markers
CRIT_COLOR = IMPRINT_PALETTE[4]  # #AE3030 — semantic: danger/resonance risk
MODE_COLORS = [c for c in IMPRINT_PALETTE if c != CRIT_COLOR]

# Constants
ENGINE_ORDERS = [1, 2, 3]  # excitation orders drawn as 1x, 2x, 3x
EO_LINESTYLES = ["dashed", "longdash", "dotdash"]
RPM_PER_HZ = 60  # one revolution per second is 60 RPM

# Columns: set these to your table's column names
SPEED = "Rotational Speed (RPM)"  # role: speed
MODES = ["1st Bending", "1st Torsional", "2nd Bending", "2nd Torsional", "Axial"]  # role: frequency_mode_
ORDER = "Engine Order"  # role: engine_order
CRITICAL = "Critical speed"  # role: critical_speeds
MODE = "Natural Frequency"  # role: extra
FREQUENCY = "Frequency (Hz)"  # role: extra
LABEL = "Label"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("modes.csv")
np.random.seed(42)
speed_rpm = np.linspace(0, 6000, 80)
# Natural frequencies with speed-dependent variation (gyroscopic effects): base, slope, noise
mode_curves = [(25, 0.0035, 0.15), (48, -0.0030, 0.12), (72, 0.0045, 0.18), (88, 0.0012, 0.14), (105, -0.0025, 0.10)]
df = pd.DataFrame(
    {SPEED: speed_rpm}
    | {
        name: base + slope * speed_rpm + np.random.normal(0, noise, len(speed_rpm))
        for name, (base, slope, noise) in zip(MODES, mode_curves, strict=True)
    }
)

# Plot
long_df = df.melt(id_vars=SPEED, value_vars=MODES, var_name=MODE, value_name=FREQUENCY)
speeds = df[SPEED].to_numpy()
speed_max = df[SPEED].max()
freq_top = long_df[FREQUENCY].max() * 1.15
order_labels = [f"{o}×" for o in ENGINE_ORDERS]

# Engine order lines (freq = order × RPM / 60), clipped where they leave the top of the plot
eo_df = pd.concat(
    [
        pd.DataFrame({SPEED: s, FREQUENCY: o * s / RPM_PER_HZ, ORDER: lbl})
        for o, lbl in zip(ENGINE_ORDERS, order_labels, strict=True)
        for s in [np.linspace(0, min(speed_max, freq_top * RPM_PER_HZ / o), len(speeds))]
    ],
    ignore_index=True,
)

# Critical speeds: intersections of engine order lines with mode curves
critical_rows = []
for order, olabel in zip(ENGINE_ORDERS, order_labels, strict=True):
    eo_at = order * speeds / RPM_PER_HZ
    for mname in MODES:
        diff = eo_at - df[mname].to_numpy()
        for idx in np.where(np.diff(np.sign(diff)))[0]:
            t = abs(diff[idx]) / (abs(diff[idx]) + abs(diff[idx + 1]))
            cs = speeds[idx] + t * (speeds[idx + 1] - speeds[idx])
            cf = order * cs / RPM_PER_HZ
            if cf <= freq_top:
                critical_rows.append({SPEED: cs, FREQUENCY: cf, CRITICAL: f"{mname} × {olabel}"})
crit_df = pd.DataFrame(critical_rows, columns=[SPEED, FREQUENCY, CRITICAL]).astype({SPEED: float, FREQUENCY: float})

# Resonance risk zones around critical speeds: 2.5 % of each axis range either side
zone_df = pd.DataFrame(
    {
        "xmin": crit_df[SPEED] - 0.025 * speed_max,
        "xmax": crit_df[SPEED] + 0.025 * speed_max,
        "ymin": crit_df[FREQUENCY] - 0.025 * freq_top,
        "ymax": crit_df[FREQUENCY] + 0.025 * freq_top,
    }
)

# Engine order labels sit just above each line, below the lowest mode curve
# (each higher order sits lower on its steeper line so neighbouring labels keep apart)
label_freq = np.array([0.14 * freq_top * 0.5 ** max(0, o - 2) for o in ENGINE_ORDERS])
eo_label_df = pd.DataFrame(
    {
        SPEED: label_freq * RPM_PER_HZ / np.array(ENGINE_ORDERS),
        FREQUENCY: label_freq + 0.03 * freq_top,
        LABEL: order_labels,
    }
)

# Annotation for the highest-frequency critical speed
danger_df = crit_df.nlargest(1, FREQUENCY)
annot_df = pd.DataFrame(
    {
        SPEED: danger_df[SPEED],
        FREQUENCY: danger_df[FREQUENCY] + 0.08 * freq_top,
        LABEL: danger_df[CRITICAL] + "\n(" + danger_df[SPEED].astype(int).astype(str) + " RPM)",
    }
)

plot = (
    ggplot()
    + geom_rect(
        data=zone_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=CRIT_COLOR,
        alpha=0.14,
        color="transparent",
    )
    + geom_line(data=eo_df, mapping=aes(x=SPEED, y=FREQUENCY, linetype=ORDER), color=INK_MUTED, size=0.9)
    + geom_line(
        data=long_df,
        mapping=aes(x=SPEED, y=FREQUENCY, color=MODE),
        size=2.5,
        tooltips=layer_tooltips()
        .line(f"@{{{MODE}}}")
        .line(f"Speed|@{{{SPEED}}} RPM")
        .line(f"Freq|@{{{FREQUENCY}}} Hz"),
    )
    + geom_point(
        data=crit_df,
        mapping=aes(x=SPEED, y=FREQUENCY),
        color=CRIT_COLOR,
        fill=CRIT_COLOR,
        size=8,
        shape=18,
        tooltips=layer_tooltips()
        .title("Critical Speed")
        .line(f"@{{{CRITICAL}}}")
        .line(f"Speed|@{{{SPEED}}} RPM")
        .line(f"Freq|@{{{FREQUENCY}}} Hz"),
    )
    + geom_text(
        data=eo_label_df, mapping=aes(x=SPEED, y=FREQUENCY, label=LABEL), color=INK_MUTED, size=5, fontface="bold"
    )
    + geom_text(
        data=annot_df,
        mapping=aes(x=SPEED, y=FREQUENCY, label=LABEL),
        color=CRIT_COLOR,
        size=5,
        fontface="italic",
        hjust=0.5,
    )
    + scale_color_manual(name=MODE, values=MODE_COLORS, limits=MODES)
    + scale_linetype_manual(name=ORDER, values=EO_LINESTYLES, limits=order_labels)
    + scale_y_continuous(limits=[0, freq_top], expand=[0.01, 0])
    + scale_x_continuous(limits=[0, speed_max], expand=[0.01, 0], format=",d")
    + guides(linetype=guide_legend(override_aes={"color": INK_MUTED}))
    + labs(
        title="campbell-basic · python · letsplot · anyplot.ai",
        subtitle="Red diamonds mark critical speeds where engine order lines cross natural frequency modes",
        x=SPEED,
        y=FREQUENCY,
        caption="Data: synthetic rotordynamic model | Shaded zones indicate resonance risk regions",
    )
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID_COLOR, size=0.4),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_title=element_text(color=INK, size=12),
        axis_text=element_text(color=INK_SOFT, size=10),
        plot_title=element_text(color=INK, size=16, face="bold", hjust=0.5),
        plot_subtitle=element_text(color=INK_MUTED, size=11, hjust=0.5),
        plot_caption=element_text(color=INK_MUTED, size=10, face="italic"),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=10),
        legend_title=element_text(color=INK, size=11, face="bold"),
        plot_margin=[20, 20, 20, 20],
    )
    + ggsize(800, 450)
)


# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
