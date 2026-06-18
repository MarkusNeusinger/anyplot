"""anyplot.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: altair 6.2.1 | Python 3.13.14
Quality: 87/100 | Updated: 2026-06-18
"""

import os
import sys


# Prevent self-import: remove the script's own directory from sys.path
# so that `import altair` resolves to the installed package, not this file.
_thisdir = os.path.dirname(os.path.realpath(__file__))
sys.path[:] = [p for p in sys.path if p not in ("", ".") and os.path.realpath(p) != _thisdir]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential colormap — low error (green) → high error (blue)
SEQ_LOW = "#009E73"  # Imprint position 1
SEQ_HIGH = "#4467A3"  # Imprint position 3

# Ideal point color — semantic matte red (Imprint position 5: reference/error anchor)
IDEAL_COLOR = "#AE3030"

# Data
np.random.seed(42)
ideal_vals = [-3, -1, 1, 3]
ideal_i, ideal_q = np.meshgrid(ideal_vals, ideal_vals)
ideal_i = ideal_i.flatten()
ideal_q = ideal_q.flatten()

n_symbols = 1000
symbol_indices = np.random.randint(0, 16, size=n_symbols)

snr_db = 20
snr_linear = 10 ** (snr_db / 10)
signal_power = np.mean(ideal_i**2 + ideal_q**2)
noise_std = np.sqrt(signal_power / snr_linear)

received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

error_vectors = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
rms_signal = np.sqrt(signal_power)
evm_pct = np.sqrt(np.mean(error_vectors**2)) / rms_signal * 100

df_received = pd.DataFrame(
    {
        "I": received_i,
        "Q": received_q,
        "Error Magnitude": error_vectors,
        "Nearest I": ideal_i[symbol_indices],
        "Nearest Q": ideal_q[symbol_indices],
    }
)
df_ideal = pd.DataFrame({"I": ideal_i, "Q": ideal_q})

# Decision boundaries at midpoints separating the 16-QAM symbol regions
boundary_vals = [-4, -2, 0, 2, 4]
boundary_h = pd.DataFrame([{"x": -5.2, "x2": 5.2, "y": v} for v in boundary_vals])
boundary_v = pd.DataFrame([{"y": -5.2, "y2": 5.2, "x": v} for v in boundary_vals])

df_evm = pd.DataFrame({"I": [4.0], "Q": [4.5], "label": [f"EVM = {evm_pct:.1f}%"]})

# Interactive selection — highlights nearest symbol on hover
nearest = alt.selection_point(on="pointerover", nearest=True, fields=["I", "Q"], empty=False)

# Equal symmetric domains for accurate constellation geometry (equal aspect ratio)
scale_x = alt.Scale(domain=[-5.5, 5.5], nice=False)
scale_y = alt.Scale(domain=[-5.5, 5.5], nice=False)

# Layer: dashed decision boundary grid lines
h_rules = (
    alt.Chart(boundary_h)
    .mark_rule(strokeDash=[8, 5], strokeWidth=1, opacity=0.45)
    .encode(x=alt.X("x:Q", scale=scale_x), x2="x2:Q", y=alt.Y("y:Q", scale=scale_y), color=alt.value(INK_MUTED))
)

v_rules = (
    alt.Chart(boundary_v)
    .mark_rule(strokeDash=[8, 5], strokeWidth=1, opacity=0.45)
    .encode(y=alt.Y("y:Q", scale=scale_y), y2="y2:Q", x=alt.X("x:Q", scale=scale_x), color=alt.value(INK_MUTED))
)

# Layer: received symbols, color-coded by error magnitude (imprint_seq)
received_layer = (
    alt.Chart(df_received)
    .mark_circle(size=40)
    .encode(
        x=alt.X("I:Q", title="In-Phase (I)", scale=scale_x),
        y=alt.Y("Q:Q", title="Quadrature (Q)", scale=scale_y),
        color=alt.Color(
            "Error Magnitude:Q",
            scale=alt.Scale(range=[SEQ_LOW, SEQ_HIGH]),
            legend=alt.Legend(
                title="Error Mag.", titleFontSize=10, labelFontSize=10, orient="right", gradientLength=100
            ),
        ),
        opacity=alt.condition(nearest, alt.value(0.9), alt.value(0.35)),
        size=alt.condition(nearest, alt.value(120), alt.value(40)),
        tooltip=[
            alt.Tooltip("I:Q", format=".3f"),
            alt.Tooltip("Q:Q", format=".3f"),
            alt.Tooltip("Error Magnitude:Q", format=".3f", title="Error"),
            alt.Tooltip("Nearest I:Q", format=".0f", title="Ideal I"),
            alt.Tooltip("Nearest Q:Q", format=".0f", title="Ideal Q"),
        ],
    )
    .add_params(nearest)
)

# Layer: ideal constellation points (cross markers, Imprint matte red semantic anchor)
ideal_layer = (
    alt.Chart(df_ideal)
    .mark_point(size=300, filled=False, strokeWidth=3.0)
    .encode(
        x="I:Q",
        y="Q:Q",
        color=alt.value(IDEAL_COLOR),
        shape=alt.value("cross"),
        tooltip=[alt.Tooltip("I:Q", format=".0f", title="Ideal I"), alt.Tooltip("Q:Q", format=".0f", title="Ideal Q")],
    )
)

# Layer: EVM annotation
evm_label = (
    alt.Chart(df_evm)
    .mark_text(fontSize=13, fontWeight="bold", align="right", font="monospace")
    .encode(x="I:Q", y="Q:Q", text="label:N", color=alt.value(INK))
)

chart = (
    alt.layer(h_rules, v_rules, received_layer, ideal_layer, evm_label)
    .properties(
        width=460,
        height=460,
        background=PAGE_BG,
        title=alt.Title(
            "scatter-constellation-diagram · python · altair · anyplot.ai",
            fontSize=17,
            fontWeight="bold",
            anchor="middle",
            offset=10,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        tickSize=4,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        grid=False,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG then pad to exact 2400×2400 square canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 2400, 2400
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
