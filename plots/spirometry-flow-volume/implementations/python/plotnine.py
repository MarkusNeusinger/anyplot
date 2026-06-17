""" anyplot.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-17
"""

import os

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


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: measured loop is the brand green (first series); the predicted
# normal loop is the violet second-series anchor; the deficit ribbon uses the amber
# caution anchor; PEF focal point uses the matte-red semantic anchor.
BRAND = "#009E73"  # Imprint position 1 — measured loop
PREDICTED = "#C475FD"  # Imprint position 2 (violet) — predicted normal reference
DEFICIT = "#DDCC77"  # amber anchor — caution / deficit
PEF_RED = "#AE3030"  # Imprint position 5 (matte red) — PEF emphasis

# Clinical parameters
fvc, fev1, pef = 4.8, 3.6, 9.5
fvc_pred, pef_pred = 5.2, 10.5
n = 150

# Measured loop data
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

# Predicted normal loop data
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

# Ribbon: shaded deficit between measured and predicted expiratory limbs
flow_pred_interp = np.interp(vol_exp_m, vol_exp_p, flow_exp_p)
df_ribbon = pd.DataFrame(
    {
        "volume": vol_exp_m,
        "flow_measured": flow_exp_m,
        "flow_predicted": flow_pred_interp,
        "fill_label": "Deficit vs predicted",
    }
)

# Main loop data
df = pd.concat(
    [
        pd.DataFrame({"volume": vol_m, "flow": flow_m, "type": "Measured"}),
        pd.DataFrame({"volume": vol_p, "flow": flow_p, "type": "Predicted normal"}),
    ],
    ignore_index=True,
)

# PEF marker
pef_vol = vol_m[peak_idx_m]
pef_flow = flow_m[peak_idx_m]
df_pef = pd.DataFrame({"volume": [pef_vol], "flow": [pef_flow], "label": [f"PEF = {pef:.1f} L/s"]})

clinical_text = f"FVC = {fvc:.1f} L\nFEV₁ = {fev1:.1f} L\nPEF = {pef:.1f} L/s\nFEV₁/FVC = {fev1 / fvc:.0%}"

# Plot
plot = (
    ggplot(df, aes(x="volume", y="flow", color="type", linetype="type"))
    + geom_ribbon(
        data=df_ribbon,
        mapping=aes(x="volume", ymin="flow_measured", ymax="flow_predicted", fill="fill_label"),
        inherit_aes=False,
        alpha=0.30,
        color="none",
    )
    + geom_hline(yintercept=0, color=INK, size=0.5, alpha=0.55)
    + geom_path(size=1.4, alpha=0.95, show_legend=True)
    + geom_point(data=df_pef, mapping=aes(x="volume", y="flow"), color=PEF_RED, size=5, alpha=0.95, inherit_aes=False)
    + geom_text(
        data=df_pef,
        mapping=aes(x="volume", y="flow", label="label"),
        color=PEF_RED,
        size=5.2,
        ha="left",
        va="bottom",
        nudge_x=0.35,
        nudge_y=1.4,
        fontweight="bold",
        inherit_aes=False,
    )
    + annotate(
        "label",
        x=0.25,
        y=-3.6,
        label=clinical_text,
        size=5.0,
        color=INK,
        fill=ELEVATED_BG,
        ha="left",
        va="top",
        label_size=0.3,
        label_padding=0.4,
    )
    + scale_color_manual(name="Curve", values={"Measured": BRAND, "Predicted normal": PREDICTED})
    + scale_linetype_manual(name="Curve", values={"Measured": "solid", "Predicted normal": "dashed"})
    + scale_fill_manual(name=" ", values={"Deficit vs predicted": DEFICIT})
    + guides(
        color=guide_legend(order=1),
        linetype=guide_legend(order=1),
        fill=guide_legend(order=2, override_aes={"alpha": 0.5}),
    )
    + scale_x_continuous(name="Volume (L)", breaks=np.arange(0, 6, 1), minor_breaks=[])
    + scale_y_continuous(name="Flow (L/s)", breaks=np.arange(-8, 12, 2), minor_breaks=[])
    + coord_cartesian(xlim=(-0.3, 6.0), ylim=(-8, 11.5))
    + labs(title="spirometry-flow-volume · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=13, weight="bold", color=INK),
        axis_title=element_text(size=11, color=INK),
        axis_text=element_text(size=9, color=INK_SOFT),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        legend_title=element_text(size=10, weight="bold", color=INK),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_position=(0.82, 0.76),
        legend_box="vertical",
        legend_background=element_rect(fill=ELEVATED_BG + "CC", color=INK_SOFT, size=0.4),
        legend_key=element_rect(fill="none", color="none"),
        legend_key_width=26,
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
