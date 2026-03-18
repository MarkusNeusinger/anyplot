"""pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-18
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
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data generation helper
def _flow_volume_loop(fvc, pef, insp_peak, n=150):
    volume_exp = np.linspace(0, fvc, n)
    t = volume_exp / fvc
    k = 2.5
    flow_exp = pef * (4 * t * np.exp(-k * t) / (4 * (1 / k) * np.exp(-1))) * (1 - t**1.5)
    flow_exp[0] = 0
    peak_idx = np.argmax(flow_exp)
    flow_exp[:peak_idx] = np.linspace(0, flow_exp[peak_idx], peak_idx)
    flow_exp = flow_exp / flow_exp.max() * pef

    volume_insp = np.linspace(fvc, 0, n)
    flow_insp = -insp_peak * np.sin(np.pi * np.linspace(0, 1, n))
    flow_insp[0] = 0
    flow_insp[-1] = 0

    return (np.concatenate([volume_exp, volume_insp]), np.concatenate([flow_exp, flow_insp]))


# Clinical parameters
fvc, fev1, pef = 4.8, 3.6, 9.5
fvc_pred, pef_pred = 5.2, 10.5

vol_m, flow_m = _flow_volume_loop(fvc, pef, 6.0)
vol_p, flow_p = _flow_volume_loop(fvc_pred, pef_pred, 6.8)

df = pd.concat(
    [
        pd.DataFrame({"volume": vol_m, "flow": flow_m, "type": "Measured"}),
        pd.DataFrame({"volume": vol_p, "flow": flow_p, "type": "Predicted"}),
    ],
    ignore_index=True,
)

pef_idx = np.argmax(flow_m[:150])
df_pef = pd.DataFrame({"volume": [vol_m[pef_idx]], "flow": [flow_m[pef_idx]], "label": [f"PEF = {pef:.1f} L/s"]})

clinical_text = f"FVC = {fvc:.1f} L\nFEV\u2081 = {fev1:.1f} L\nPEF = {pef:.1f} L/s\nFEV\u2081/FVC = {fev1 / fvc:.0%}"

# Plot
plot = (
    ggplot(df, aes(x="volume", y="flow", color="type", linetype="type"))
    + geom_path(size=2, alpha=0.95, show_legend=True)
    + scale_color_manual(name="Curve", values={"Measured": "#306998", "Predicted": "#8C8C8C"})
    + scale_linetype_manual(name="Curve", values={"Measured": "solid", "Predicted": "dashed"})
    + geom_hline(yintercept=0, color="#555555", size=0.3, alpha=0.4)
    + geom_point(data=df_pef, mapping=aes(x="volume", y="flow"), color="#C0392B", size=5, alpha=0.9, inherit_aes=False)
    + geom_text(
        data=df_pef,
        mapping=aes(x="volume", y="flow", label="label"),
        color="#C0392B",
        size=13,
        ha="left",
        va="bottom",
        nudge_x=0.2,
        nudge_y=0.3,
        fontweight="bold",
        inherit_aes=False,
    )
    + annotate("text", x=0.3, y=-4.2, label=clinical_text, size=13, color="#2C3E50", ha="left", va="top")
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
        legend_position=(0.85, 0.82),
        legend_background=element_rect(fill="white", alpha=0.8, color="#CCCCCC", size=0.5),
        legend_key_width=30,
        plot_background=element_rect(fill="#FAFBFC", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
