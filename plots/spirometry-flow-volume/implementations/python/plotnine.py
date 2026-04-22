""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_path,
    geom_point,
    geom_ribbon,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_linetype_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Clinical parameters
fvc, fev1, pef = 4.8, 3.6, 9.5
fvc_pred, pef_pred = 5.2, 10.5
n = 150

# Measured loop data (inlined for KISS structure)
vol_exp_m = np.linspace(0, fvc, n)
t_m = vol_exp_m / fvc
k = 2.5
flow_exp_m = pef * (4 * t_m * np.exp(-k * t_m) / (4 * (1 / k) * np.exp(-1))) * (1 - t_m**1.5)
flow_exp_m[0] = 0
peak_idx_m = np.argmax(flow_exp_m)
flow_exp_m[:peak_idx_m] = np.linspace(0, flow_exp_m[peak_idx_m], peak_idx_m)
flow_exp_m = flow_exp_m / flow_exp_m.max() * pef

vol_insp_m = np.linspace(fvc, 0, n)
flow_insp_m = -6.0 * np.sin(np.pi * np.linspace(0, 1, n))
flow_insp_m[0] = 0
flow_insp_m[-1] = 0

vol_m = np.concatenate([vol_exp_m, vol_insp_m])
flow_m = np.concatenate([flow_exp_m, flow_insp_m])

# Predicted loop data (inlined)
vol_exp_p = np.linspace(0, fvc_pred, n)
t_p = vol_exp_p / fvc_pred
flow_exp_p = pef_pred * (4 * t_p * np.exp(-k * t_p) / (4 * (1 / k) * np.exp(-1))) * (1 - t_p**1.5)
flow_exp_p[0] = 0
peak_idx_p = np.argmax(flow_exp_p)
flow_exp_p[:peak_idx_p] = np.linspace(0, flow_exp_p[peak_idx_p], peak_idx_p)
flow_exp_p = flow_exp_p / flow_exp_p.max() * pef_pred

vol_insp_p = np.linspace(fvc_pred, 0, n)
flow_insp_p = -6.8 * np.sin(np.pi * np.linspace(0, 1, n))
flow_insp_p[0] = 0
flow_insp_p[-1] = 0

vol_p = np.concatenate([vol_exp_p, vol_insp_p])
flow_p = np.concatenate([flow_exp_p, flow_insp_p])

# Ribbon data: shaded area between measured and predicted expiratory limbs
# Interpolate predicted onto measured volume grid for ribbon
flow_pred_interp = np.interp(vol_exp_m, vol_exp_p, flow_exp_p)
df_ribbon = pd.DataFrame(
    {
        "volume": vol_exp_m,
        "flow_measured": flow_exp_m,
        "flow_predicted": flow_pred_interp,
        "fill_label": "Deficit vs Predicted",
    }
)

# Main loop data
df = pd.concat(
    [
        pd.DataFrame({"volume": vol_m, "flow": flow_m, "type": "Measured"}),
        pd.DataFrame({"volume": vol_p, "flow": flow_p, "type": "Predicted"}),
    ],
    ignore_index=True,
)

# PEF annotation
pef_vol = vol_m[peak_idx_m]
pef_flow = flow_m[peak_idx_m]
df_pef = pd.DataFrame({"volume": [pef_vol], "flow": [pef_flow], "label": [f"PEF = {pef:.1f} L/s"]})

clinical_text = f"FVC = {fvc:.1f} L\nFEV\u2081 = {fev1:.1f} L\nPEF = {pef:.1f} L/s\nFEV\u2081/FVC = {fev1 / fvc:.0%}"

# Plot
plot = (
    ggplot(df, aes(x="volume", y="flow", color="type", linetype="type"))
    + geom_ribbon(
        data=df_ribbon,
        mapping=aes(x="volume", ymin="flow_measured", ymax="flow_predicted", fill="fill_label"),
        inherit_aes=False,
        alpha=0.15,
        color="none",
    )
    + geom_path(size=2, alpha=0.95, show_legend=True)
    + geom_hline(yintercept=0, color="#555555", size=0.3, alpha=0.4)
    + geom_point(data=df_pef, mapping=aes(x="volume", y="flow"), color="#C0392B", size=6, alpha=0.9, inherit_aes=False)
    + geom_text(
        data=df_pef,
        mapping=aes(x="volume", y="flow", label="label"),
        color="#C0392B",
        size=15,
        ha="left",
        va="bottom",
        nudge_x=0.25,
        nudge_y=0.6,
        fontweight="bold",
        inherit_aes=False,
    )
    + annotate("text", x=0.3, y=-4.2, label=clinical_text, size=15, color="#2C3E50", ha="left", va="top")
    + scale_color_manual(name="Curve", values={"Measured": "#306998", "Predicted": "#8C8C8C"})
    + scale_linetype_manual(name="Curve", values={"Measured": "solid", "Predicted": "dashed"})
    + scale_fill_manual(name=" ", values={"Deficit vs Predicted": "#306998"})
    + guides(
        color=guide_legend(order=1),
        linetype=guide_legend(order=1),
        fill=guide_legend(order=2, override_aes={"alpha": 0.3}),
    )
    + scale_x_continuous(name="Volume (L)", breaks=np.arange(0, 6, 1), minor_breaks=[])
    + scale_y_continuous(name="Flow (L/s)", breaks=np.arange(-8, 12, 2), minor_breaks=[])
    + coord_cartesian(xlim=(-0.3, 6.0), ylim=(-8, 11.5))
    + labs(title="spirometry-flow-volume \u00b7 plotnine \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#1A1A2E"),
        axis_title=element_text(size=20, color="#2C3E50"),
        axis_text=element_text(size=16, color="#34495E"),
        panel_grid_major=element_line(color="#E0E0E0", size=0.4, alpha=0.5),
        panel_grid_minor=element_blank(),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position=(0.85, 0.80),
        legend_background=element_rect(fill="white", alpha=0.85, color="#CCCCCC", size=0.5),
        legend_key_width=30,
        plot_background=element_rect(fill="#FAFBFC", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
