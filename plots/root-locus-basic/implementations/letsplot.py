""" pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Root locus for G(s) = (s + 3) / [s(s + 1)(s + 2)(s + 4)]
# Open-loop poles: 0, -1, -2, -4 | Open-loop zero: -3
num_coeffs = np.array([1, 3])  # s + 3
den_coeffs = np.polymul(np.polymul([1, 0], [1, 1]), np.polymul([1, 2], [1, 4]))  # s(s+1)(s+2)(s+4)

open_loop_poles = np.array([0.0, -1.0, -2.0, -4.0])
open_loop_zeros = np.array([-3.0])

# Compute closed-loop poles for varying gain K
k_values = np.concatenate(
    [np.linspace(0, 0.5, 200), np.linspace(0.5, 5, 400), np.linspace(5, 30, 400), np.linspace(30, 120, 400)]
)

all_real = []
all_imag = []
all_gain = []
all_branch = []

for k in k_values:
    char_poly = np.polyadd(den_coeffs, k * np.array([0, 0, 0, 1, 3]))
    roots = np.roots(char_poly)
    roots = np.sort_complex(roots)
    for b, root in enumerate(roots):
        all_real.append(root.real)
        all_imag.append(root.imag)
        all_gain.append(k)
        all_branch.append(f"Branch {b + 1}")

df = pd.DataFrame({"real": all_real, "imaginary": all_imag, "gain": all_gain, "branch": all_branch})

# Open-loop poles and zeros for markers
poles_df = pd.DataFrame(
    {
        "real": open_loop_poles,
        "imaginary": [0.0] * len(open_loop_poles),
        "type": ["Open-loop pole"] * len(open_loop_poles),
    }
)
zeros_df = pd.DataFrame(
    {
        "real": open_loop_zeros,
        "imaginary": [0.0] * len(open_loop_zeros),
        "type": ["Open-loop zero"] * len(open_loop_zeros),
    }
)

# Find imaginary axis crossings (where real part ≈ 0 and imag ≠ 0)
crossing_mask = (np.abs(df["real"]) < 0.08) & (np.abs(df["imaginary"]) > 0.3)
crossings = df[crossing_mask].copy()
if len(crossings) > 0:
    crossings = crossings.sort_values("imaginary")
    pos_cross = crossings[crossings["imaginary"] > 0].head(1)
    neg_cross = crossings[crossings["imaginary"] < 0].head(1)
    crossing_pts = pd.concat([pos_cross, neg_cross])
else:
    crossing_pts = pd.DataFrame(columns=df.columns)

# Direction arrows - sample points at specific gain values for each branch
arrow_gains = [8, 25, 60]
arrow_rows = []
for ag in arrow_gains:
    idx = np.argmin(np.abs(k_values - ag))
    subset = df[(df["gain"] >= k_values[max(0, idx - 1)]) & (df["gain"] <= k_values[min(len(k_values) - 1, idx + 1)])]
    for _, row in subset.drop_duplicates(subset="branch").iterrows():
        k_next = k_values[min(len(k_values) - 1, idx + 3)]
        next_pts = df[(np.abs(df["gain"] - k_next) < 0.5) & (df["branch"] == row["branch"])]
        if len(next_pts) > 0:
            npt = next_pts.iloc[0]
            arrow_rows.append({"x": row["real"], "y": row["imaginary"], "xend": npt["real"], "yend": npt["imaginary"]})

arrows_df = pd.DataFrame(arrow_rows) if arrow_rows else pd.DataFrame(columns=["x", "y", "xend", "yend"])

# Damping ratio lines (constant zeta)
zeta_values = [0.2, 0.4, 0.6, 0.8]
zeta_lines = []
for zeta in zeta_values:
    theta = np.arccos(zeta)
    r_max = 5.0
    zeta_lines.append(
        {"x": 0, "y": 0, "xend": -r_max * np.cos(theta), "yend": r_max * np.sin(theta), "label": f"ζ={zeta}"}
    )
    zeta_lines.append(
        {"x": 0, "y": 0, "xend": -r_max * np.cos(theta), "yend": -r_max * np.sin(theta), "label": f"ζ={zeta}"}
    )
zeta_df = pd.DataFrame(zeta_lines)

# Zeta labels (upper half only)
zeta_label_df = pd.DataFrame(
    [
        {"x": -r_max * 0.55 * np.cos(np.arccos(z)), "y": r_max * 0.55 * np.sin(np.arccos(z)), "label": f"ζ={z}"}
        for z in zeta_values
    ]
)

# Natural frequency circles (constant ωn)
wn_values = [1, 2, 3, 4]
wn_rows = []
for wn in wn_values:
    theta = np.linspace(np.pi / 2, 3 * np.pi / 2, 100)
    wn_rows.extend([{"real": wn * np.cos(t), "imaginary": wn * np.sin(t), "wn": f"ωn={wn}"} for t in theta])
wn_df = pd.DataFrame(wn_rows)

# Branch colors
branch_colors = ["#306998", "#E05D44", "#44A867", "#9467BD"]

# Plot
plot = (
    ggplot()  # noqa: F405
    # Natural frequency arcs
    + geom_path(  # noqa: F405
        aes(x="real", y="imaginary", group="wn"),  # noqa: F405
        data=wn_df,
        color="#E0E0E0",
        size=0.4,
        linetype="dashed",
        tooltips="none",
    )
    # Damping ratio lines
    + geom_segment(  # noqa: F405
        aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        data=zeta_df,
        color="#E0E0E0",
        size=0.4,
        linetype="dashed",
        tooltips="none",
    )
    # Damping ratio labels
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=zeta_label_df,
        size=10,
        color="#BBBBBB",
        inherit_aes=False,
    )
    # Imaginary axis (stability boundary)
    + geom_vline(xintercept=0, color="#CCCCCC", size=0.5)  # noqa: F405
    + geom_hline(yintercept=0, color="#CCCCCC", size=0.5)  # noqa: F405
    # Root locus branches
    + geom_path(  # noqa: F405
        aes(x="real", y="imaginary", color="branch"),  # noqa: F405
        data=df,
        size=1.5,
        alpha=0.85,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Branch: @branch")
        .line("Gain K: @gain")
        .line("Re: @real")
        .line("Im: @imaginary"),
    )
    + scale_color_manual(  # noqa: F405
        values=branch_colors, name="Locus Branch"
    )
    # Direction arrows
    + geom_segment(  # noqa: F405
        aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        data=arrows_df,
        color="#555555",
        size=0.8,
        arrow=arrow(length=8, type="open"),  # noqa: F405
        inherit_aes=False,
        tooltips="none",
    )
    # Open-loop poles (× markers)
    + geom_point(  # noqa: F405
        aes(x="real", y="imaginary"),  # noqa: F405
        data=poles_df,
        shape=4,  # cross/x marker
        size=8,
        color="#222222",
        stroke=2.5,
        inherit_aes=False,
        tooltips=layer_tooltips().line("Open-loop pole").line("s = @real"),  # noqa: F405
    )
    # Open-loop zeros (○ markers)
    + geom_point(  # noqa: F405
        aes(x="real", y="imaginary"),  # noqa: F405
        data=zeros_df,
        shape=1,  # open circle
        size=8,
        color="#222222",
        stroke=2.5,
        inherit_aes=False,
        tooltips=layer_tooltips().line("Open-loop zero").line("s = @real"),  # noqa: F405
    )
    # Imaginary axis crossings
    + geom_point(  # noqa: F405
        aes(x="real", y="imaginary"),  # noqa: F405
        data=crossing_pts,
        shape=18,  # diamond
        size=7,
        color="#E05D44",
        inherit_aes=False,
        tooltips=layer_tooltips().line("Stability boundary crossing").line("Im: @imaginary"),  # noqa: F405
    )
    # Labels and styling
    + labs(  # noqa: F405
        x="Real Axis",
        y="Imaginary Axis",
        title="root-locus-basic · letsplot · pyplots.ai",
        caption="G(s) = (s + 3) / [s(s + 1)(s + 2)(s + 4)]  ·  × = poles  ·  ○ = zeros",
    )
    + coord_fixed(ratio=1, xlim=[-5.5, 1.5], ylim=[-4, 4])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        plot_title=element_text(size=24, color="#222222", face="bold"),  # noqa: F405
        plot_caption=element_text(size=13, color="#888888", face="italic"),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_title=element_text(size=16),  # noqa: F405
        legend_position="right",
        panel_grid_major=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        panel_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        axis_ticks=element_line(color="#CCCCCC", size=0.3),  # noqa: F405
        axis_line=element_line(color="#CCCCCC", size=0.4),  # noqa: F405
        plot_margin=[30, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
