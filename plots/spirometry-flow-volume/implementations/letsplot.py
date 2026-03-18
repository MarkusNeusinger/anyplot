""" pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-18
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Simulated spirometry flow-volume loop
np.random.seed(42)

# Measured patient data (mild obstructive pattern)
fvc = 4.2  # Forced Vital Capacity in liters
pef = 8.5  # Peak Expiratory Flow in L/s
fev1 = 3.1  # FEV1 in liters

# Expiratory limb: sharp rise to PEF then roughly linear decline
n_exp = 150
volume_exp = np.linspace(0, fvc, n_exp)
t_peak = 0.08  # PEF occurs early (~8% of FVC)
peak_idx = int(t_peak * n_exp)

flow_rise = np.linspace(0, pef, peak_idx + 1)
volume_remaining = volume_exp[peak_idx:]
flow_decline = pef * (1 - ((volume_remaining - volume_remaining[0]) / (fvc - volume_remaining[0])) ** 0.85)
flow_exp = np.concatenate([flow_rise, flow_decline[1:]])

# Inspiratory limb: symmetric U-shaped curve below zero
n_insp = 150
volume_insp = np.linspace(fvc, 0, n_insp)
pif = -6.0  # Peak Inspiratory Flow
t_norm = np.linspace(0, np.pi, n_insp)
flow_insp = pif * np.sin(t_norm)

# Predicted normal values (healthy reference)
fvc_pred = 4.8
pef_pred = 10.2

n_pred_exp = 150
volume_pred_exp = np.linspace(0, fvc_pred, n_pred_exp)
peak_idx_pred = int(0.08 * n_pred_exp)
flow_pred_rise = np.linspace(0, pef_pred, peak_idx_pred + 1)
volume_pred_remaining = volume_pred_exp[peak_idx_pred:]
flow_pred_decline = pef_pred * (
    1 - ((volume_pred_remaining - volume_pred_remaining[0]) / (fvc_pred - volume_pred_remaining[0])) ** 0.95
)
flow_pred_exp = np.concatenate([flow_pred_rise, flow_pred_decline[1:]])

n_pred_insp = 150
volume_pred_insp = np.linspace(fvc_pred, 0, n_pred_insp)
pif_pred = -7.0
flow_pred_insp = pif_pred * np.sin(np.linspace(0, np.pi, n_pred_insp))

# Combine measured loop into single DataFrame with group for legend
df_measured = pd.DataFrame(
    {
        "volume": np.concatenate([volume_exp, volume_insp]),
        "flow": np.concatenate([flow_exp, flow_insp]),
        "curve": "Measured",
    }
)

df_predicted = pd.DataFrame(
    {
        "volume": np.concatenate([volume_pred_exp, volume_pred_insp]),
        "flow": np.concatenate([flow_pred_exp, flow_pred_insp]),
        "curve": "Predicted Normal",
    }
)

# Ribbon data for filled measured loop area
df_ribbon_measured = pd.DataFrame(
    {"volume": volume_exp, "ymin": np.interp(volume_exp, volume_insp[::-1], flow_insp[::-1]), "ymax": flow_exp}
)

# Ribbon data for filled predicted loop area
df_ribbon_predicted = pd.DataFrame(
    {
        "volume": volume_pred_exp,
        "ymin": np.interp(volume_pred_exp, volume_pred_insp[::-1], flow_pred_insp[::-1]),
        "ymax": flow_pred_exp,
    }
)

# PEF annotation point
pef_volume = volume_exp[np.argmax(flow_exp)]
df_pef = pd.DataFrame({"volume": [pef_volume], "flow": [pef]})

# FEV1 volume marker on measured curve
fev1_flow = np.interp(fev1, volume_exp, flow_exp)
df_fev1 = pd.DataFrame({"volume": [fev1], "flow": [fev1_flow]})

# Clinical values annotation
clinical_text = f"FEV\u2081: {fev1:.1f} L  |  FVC: {fvc:.1f} L  |  PEF: {pef:.1f} L/s"
df_clinical = pd.DataFrame({"volume": [fvc * 0.52], "flow": [pef * 1.15], "label": [clinical_text]})

# Combined line data for legend
df_lines = pd.concat([df_measured, df_predicted], ignore_index=True)

# Tooltip data for measured expiratory limb
df_measured_exp_tt = pd.DataFrame(
    {
        "volume": volume_exp,
        "flow": flow_exp,
        "curve": "Measured",
        "vol_label": [f"{v:.2f} L" for v in volume_exp],
        "flow_label": [f"{f:.1f} L/s" for f in flow_exp],
    }
)

# Tooltip data for measured inspiratory limb
df_measured_insp_tt = pd.DataFrame(
    {
        "volume": volume_insp,
        "flow": flow_insp,
        "curve": "Measured",
        "vol_label": [f"{v:.2f} L" for v in volume_insp],
        "flow_label": [f"{f:.1f} L/s" for f in flow_insp],
    }
)

# Plot
plot = (
    ggplot()
    # Filled predicted normal range (subtle background)
    + geom_ribbon(aes(x="volume", ymin="ymin", ymax="ymax"), data=df_ribbon_predicted, fill="#D4D4D4", alpha=0.3)
    # Filled measured loop area
    + geom_ribbon(aes(x="volume", ymin="ymin", ymax="ymax"), data=df_ribbon_measured, fill="#306998", alpha=0.15)
    # Predicted loop lines (dashed) - use color aes for natural legend
    + geom_line(
        aes(x="volume", y="flow", color="curve"),
        data=df_predicted[df_predicted["curve"] == "Predicted Normal"].iloc[:n_pred_exp],
        size=1.2,
        linetype="dashed",
        show_legend=True,
    )
    + geom_line(
        aes(x="volume", y="flow", color="curve"),
        data=df_predicted[df_predicted["curve"] == "Predicted Normal"].iloc[n_pred_exp:],
        size=1.2,
        linetype="dashed",
        show_legend=False,
    )
    # Measured loop lines with tooltips - use color aes for natural legend
    + geom_line(
        aes(x="volume", y="flow", color="curve"),
        data=df_measured_exp_tt,
        size=2.0,
        show_legend=True,
        tooltips=layer_tooltips().title("Expiratory Limb").line("Volume|@vol_label").line("Flow|@flow_label"),
    )
    + geom_line(
        aes(x="volume", y="flow", color="curve"),
        data=df_measured_insp_tt,
        size=2.0,
        show_legend=False,
        tooltips=layer_tooltips().title("Inspiratory Limb").line("Volume|@vol_label").line("Flow|@flow_label"),
    )
    # FEV1 marker on curve (purple - colorblind-safe)
    + geom_point(aes(x="volume", y="flow"), data=df_fev1, color="#7C3AED", size=7, shape=18)
    + geom_label(
        aes(x="volume", y="flow", label="label"),
        data=pd.DataFrame(
            {"volume": [fev1 + 0.15], "flow": [fev1_flow + 0.6], "label": [f"FEV\u2081 at {fev1:.1f} L"]}
        ),
        size=11,
        color="#7C3AED",
        fill="#F5F3FF",
        label_padding=0.3,
        hjust=0,
    )
    # PEF marker (amber - colorblind-safe)
    + geom_point(
        aes(x="volume", y="flow"),
        data=df_pef,
        color="#D97706",
        size=8,
        shape=16,
        tooltips=layer_tooltips()
        .title("Peak Expiratory Flow")
        .line(f"PEF|{pef} L/s")
        .line(f"Volume|{pef_volume:.2f} L"),
    )
    + geom_label(
        aes(x="volume", y="flow", label="label"),
        data=pd.DataFrame({"volume": [pef_volume + 0.2], "flow": [pef + 0.5], "label": [f"PEF: {pef} L/s"]}),
        size=12,
        color="#D97706",
        fill="#FFFBEB",
        label_padding=0.3,
        hjust=0,
    )
    # Clinical values bar at top
    + geom_label(
        aes(x="volume", y="flow", label="label"),
        data=df_clinical,
        size=12,
        color="#1F2937",
        fill="#F3F4F6",
        label_padding=0.5,
        hjust=0.5,
    )
    # Zero flow reference line
    + geom_hline(yintercept=0, color="#6B7280", size=0.6, linetype="solid")
    + scale_color_manual(values={"Measured": "#306998", "Predicted Normal": "#9CA3AF"}, name="")
    + guides(color=guide_legend(override_aes={"size": 5}))
    # Labels and sizing
    + labs(x="Volume (L)", y="Flow (L/s)", title="spirometry-flow-volume \u00b7 letsplot \u00b7 pyplots.ai")
    + ggsize(1600, 900)
    + coord_cartesian(ylim=[-8, 11])
    + scale_x_continuous(expand=[0.02, 0])
    + scale_y_continuous(breaks=list(range(-8, 12, 2)))
    + theme(
        plot_title=element_text(size=24, face="bold", color="#1F2937"),
        axis_title=element_text(size=20, color="#374151"),
        axis_text=element_text(size=16, color="#6B7280"),
        panel_grid_major_y=element_line(color="#E5E7EB", size=0.4),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position=[0.85, 0.92],
        legend_justification=[0.5, 1.0],
        legend_text=element_text(size=15),
        legend_background=element_rect(fill="#FFFFFF", color="#E5E7EB", size=0.5),
        plot_background=element_rect(fill="#FAFAFA"),
        panel_background=element_rect(fill="#FAFAFA"),
        plot_margin=[40, 20, 20, 20],
    )
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")
