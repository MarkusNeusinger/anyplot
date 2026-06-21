"""anyplot.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: pygal | Python 3.13
Quality: pending | Created: 2026-06-21
"""

import os
import sys


# Prevent this file (pygal.py) from shadowing the installed pygal package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _this_dir]

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data — engineering stress-strain curves for two classic materials
np.random.seed(42)

# ── ASTM A36 Mild Steel: distinct Lüders plateau and ductile failure ──
E_MILD = 200_000.0  # Young's modulus, MPa
SY_MILD = 250.0  # Yield strength, MPa
eps_y_mild = SY_MILD / E_MILD  # elastic-limit strain ~0.00125

# Elastic region (linear)
s_e_mild = np.linspace(0.0, eps_y_mild, 30)
sig_e_mild = E_MILD * s_e_mild

# Lüders plateau (slight hardening before macroscopic work hardening)
s_pl_mild = np.linspace(eps_y_mild, 0.013, 18)
sig_pl_mild = SY_MILD + 22.0 * ((s_pl_mild - eps_y_mild) / (0.013 - eps_y_mild)) ** 2

# Strain hardening (power-law)
s_sh_mild = np.linspace(0.013, 0.210, 88)
sig_sh_mild = 272.0 + 178.0 * ((s_sh_mild - 0.013) / (0.210 - 0.013)) ** 0.52

# Necking to fracture (engineering stress drops as cross-section shrinks)
SU_MILD = float(sig_sh_mild[-1])  # UTS ≈ 450 MPa
s_nk_mild = np.linspace(0.210, 0.270, 22)
sig_nk_mild = SU_MILD * (1.0 - 0.27 * ((s_nk_mild - 0.210) / 0.060) ** 0.45)

strain_mild = np.concatenate([s_e_mild, s_pl_mild[1:], s_sh_mild[1:], s_nk_mild[1:]])
stress_mild = np.concatenate([sig_e_mild, sig_pl_mild[1:], sig_sh_mild[1:], sig_nk_mild[1:]])
stress_mild += np.random.normal(0, 1.2, len(stress_mild))
stress_mild = np.clip(stress_mild, 0.0, None)

n_e_mild = len(s_e_mild)  # elastic region length
uts_idx_mild = int(np.argmax(stress_mild))

# ── 6061-T6 Aluminum Alloy: smooth curve, no yield plateau ──────────
E_AL = 68_500.0  # Young's modulus, MPa
SY_AL = 276.0  # 0.2% offset yield strength, MPa
SU_AL = 310.0  # UTS, MPa
eps_y_al = SY_AL / E_AL  # ~0.00403

# Elastic region
s_e_al = np.linspace(0.0, eps_y_al, 25)
sig_e_al = E_AL * s_e_al

# Continuous strain hardening (saturating exponential — no Lüders band)
s_p_al = np.linspace(eps_y_al, 0.115, 130)
t_al = (s_p_al - eps_y_al) / (0.115 - eps_y_al)
sig_p_al = SY_AL + (SU_AL - SY_AL) * (1.0 - np.exp(-5.5 * t_al))

# Necking onset at ~0.095 strain
nk_start = int(np.argmin(np.abs(s_p_al - 0.095)))
sig_p_al[nk_start:] = sig_p_al[nk_start] * (1.0 - 0.21 * np.linspace(0.0, 1.0, len(sig_p_al) - nk_start) ** 0.5)

strain_al = np.concatenate([s_e_al, s_p_al[1:]])
stress_al = np.concatenate([sig_e_al, sig_p_al[1:]])
stress_al += np.random.normal(0, 0.7, len(strain_al))
stress_al = np.clip(stress_al, 0.0, None)

n_e_al = len(s_e_al)
uts_idx_al = int(np.argmax(stress_al))

# ── 0.2% Offset Line — illustrates yield determination for aluminum ──
OFFSET_STRAIN = 0.002  # 0.2% = 0.002 in strain units
s_off = np.linspace(OFFSET_STRAIN, eps_y_al + 0.003, 30)
sig_off = E_AL * (s_off - OFFSET_STRAIN)  # parallel to elastic, shifted right

# ── Convert to pygal XY format (key points get tooltip labels) ──────
mild_key_labels = {
    n_e_mild - 1: f"Yield Point — {stress_mild[n_e_mild - 1]:.0f} MPa",
    uts_idx_mild: f"UTS — {stress_mild[uts_idx_mild]:.0f} MPa",
    len(strain_mild) - 1: f"Fracture — {stress_mild[-1]:.0f} MPa",
}
mild_data = []
for i, (s, sig) in enumerate(zip(strain_mild, stress_mild, strict=True)):
    pt = (round(float(s), 6), round(float(sig), 2))
    if i in mild_key_labels:
        mild_data.append({"value": pt, "label": mild_key_labels[i]})
    else:
        mild_data.append(pt)

al_key_labels = {
    n_e_al - 1: f"0.2% Offset Yield — {stress_al[n_e_al - 1]:.0f} MPa",
    uts_idx_al: f"UTS — {stress_al[uts_idx_al]:.0f} MPa",
    len(strain_al) - 1: f"Fracture — {stress_al[-1]:.0f} MPa",
}
al_data = []
for i, (s, sig) in enumerate(zip(strain_al, stress_al, strict=True)):
    pt = (round(float(s), 6), round(float(sig), 2))
    if i in al_key_labels:
        al_data.append({"value": pt, "label": al_key_labels[i]})
    else:
        al_data.append(pt)

offset_data = [(round(float(s), 6), round(float(sig), 2)) for s, sig in zip(s_off, sig_off, strict=True)]

# ── Chart style ──────────────────────────────────────────────────────
title = "line-stress-strain · python · pygal · anyplot.ai"
n_chars = len(title)
title_fs = round(66 * (67 / n_chars)) if n_chars > 67 else 66

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_fs,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3.5,
)

# ── Build chart ──────────────────────────────────────────────────────
chart = pygal.XY(
    style=custom_style,
    width=3200,
    height=1800,
    title=title,
    x_title="Engineering Strain (dimensionless)",
    y_title="Engineering Stress (MPa)",
    stroke=True,
    show_dots=False,
    fill=False,
    show_x_guides=False,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    truncate_legend=40,
)

chart.add("ASTM A36 Mild Steel", mild_data)
chart.add("6061-T6 Aluminum", al_data)
chart.add("0.2% Offset Line (Al)", offset_data, stroke_style={"width": 2, "dasharray": "8, 6", "linecap": "round"})

# Save PNG and HTML (pygal is interactive)
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
