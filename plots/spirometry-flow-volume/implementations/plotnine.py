"""pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_text,
    geom_hline,
    geom_path,
    geom_point,
    geom_text,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Data
fvc = 4.8
fev1 = 3.6
pef = 9.5

n_points = 150
volume_exp = np.linspace(0, fvc, n_points)
t_exp = volume_exp / fvc
flow_exp = pef * (4 * t_exp * np.exp(-2.5 * t_exp) / (4 * (1 / 2.5) * np.exp(-1)))
flow_exp = flow_exp * (1 - t_exp**1.5)
flow_exp[0] = 0
peak_idx = np.argmax(flow_exp)
flow_exp[:peak_idx] = np.linspace(0, flow_exp[peak_idx], peak_idx)
flow_exp = flow_exp / flow_exp.max() * pef

volume_insp = np.linspace(fvc, 0, n_points)
t_insp = np.linspace(0, 1, n_points)
flow_insp = -6.0 * np.sin(np.pi * t_insp)
flow_insp[0] = 0
flow_insp[-1] = 0

fvc_pred = 5.2
pef_pred = 10.5
volume_pred_exp = np.linspace(0, fvc_pred, n_points)
t_pred = volume_pred_exp / fvc_pred
flow_pred_exp = pef_pred * (4 * t_pred * np.exp(-2.5 * t_pred) / (4 * (1 / 2.5) * np.exp(-1)))
flow_pred_exp = flow_pred_exp * (1 - t_pred**1.5)
flow_pred_exp[0] = 0
peak_pred_idx = np.argmax(flow_pred_exp)
flow_pred_exp[:peak_pred_idx] = np.linspace(0, flow_pred_exp[peak_pred_idx], peak_pred_idx)
flow_pred_exp = flow_pred_exp / flow_pred_exp.max() * pef_pred

volume_pred_insp = np.linspace(fvc_pred, 0, n_points)
t_pred_insp = np.linspace(0, 1, n_points)
flow_pred_insp = -6.8 * np.sin(np.pi * t_pred_insp)
flow_pred_insp[0] = 0
flow_pred_insp[-1] = 0

df_measured = pd.DataFrame(
    {"volume": np.concatenate([volume_exp, volume_insp]), "flow": np.concatenate([flow_exp, flow_insp])}
)

df_predicted = pd.DataFrame(
    {
        "volume": np.concatenate([volume_pred_exp, volume_pred_insp]),
        "flow": np.concatenate([flow_pred_exp, flow_pred_insp]),
    }
)

pef_volume = volume_exp[np.argmax(flow_exp)]
pef_value = flow_exp.max()
df_pef = pd.DataFrame({"volume": [pef_volume], "flow": [pef_value], "label": [f"PEF = {pef_value:.1f} L/s"]})

clinical_text = f"FVC = {fvc:.1f} L\nFEV1 = {fev1:.1f} L\nPEF = {pef_value:.1f} L/s\nFEV1/FVC = {fev1 / fvc:.0%}"

# Plot
plot = (
    ggplot()
    + geom_path(data=df_measured, mapping=aes(x="volume", y="flow"), color="#306998", size=2, alpha=0.95)
    + geom_path(
        data=df_predicted, mapping=aes(x="volume", y="flow"), color="#999999", size=1.2, linetype="dashed", alpha=0.8
    )
    + geom_hline(yintercept=0, color="#333333", size=0.4, alpha=0.5)
    + geom_point(data=df_pef, mapping=aes(x="volume", y="flow"), color="#D4513D", size=5, alpha=0.9)
    + geom_text(
        data=df_pef,
        mapping=aes(x="volume", y="flow", label="label"),
        color="#D4513D",
        size=12,
        ha="left",
        va="bottom",
        nudge_x=0.2,
        nudge_y=0.3,
        fontweight="bold",
    )
    + annotate("text", x=3.8, y=-3.5, label=clinical_text, size=11, color="#333333", ha="left", va="top")
    + annotate(
        "text", x=3.8, y=7.5, label="\u2014 Measured\n--- Predicted", size=11, color="#555555", ha="left", va="top"
    )
    + labs(x="Volume (L)", y="Flow (L/s)", title="spirometry-flow-volume \u00b7 plotnine \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(alpha=0.2, size=0.5),
        panel_grid_minor=element_blank(),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
