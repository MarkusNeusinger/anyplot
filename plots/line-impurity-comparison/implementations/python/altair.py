""" anyplot.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: altair 6.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-29
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette positions 1 and 2
GINI_COLOR = "#009E73"  # position 1 — always first series
ENTROPY_COLOR = "#C475FD"  # position 2

# Data: probability range [0, 1], 200 points for smooth curves
p = np.linspace(0, 1, 200)
gini = 2 * p * (1 - p)

# Entropy with safe log (0 at boundaries as required by spec)
with np.errstate(divide="ignore", invalid="ignore"):
    entropy_raw = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
entropy_raw = np.nan_to_num(entropy_raw, nan=0.0)
entropy = entropy_raw / np.max(entropy_raw)

GINI_LABEL = "Gini: 2p(1−p)"
ENTROPY_LABEL = "Entropy: −p·log₂(p) (scaled)"

df = pd.DataFrame(
    {
        "p": np.tile(p, 2),
        "Impurity": np.concatenate([gini, entropy]),
        "Measure": [GINI_LABEL] * len(p) + [ENTROPY_LABEL] * len(p),
    }
)

annotation_df = pd.DataFrame(
    {"p": [0.5, 0.5], "Impurity": [0.5, 1.0], "label": ["Gini max = 0.5", "Entropy max = 1.0"]}
)

# Title with scaled font size (67-char baseline)
title_text = "line-impurity-comparison · python · altair · anyplot.ai"
n = len(title_text)
title_fontsize = max(11, round(16 * (67 / n if n > 67 else 1.0)))

# Color + dash scales for distinguishable lines (solid Gini, dashed Entropy)
color_scale = alt.Scale(domain=[GINI_LABEL, ENTROPY_LABEL], range=[GINI_COLOR, ENTROPY_COLOR])
dash_scale = alt.Scale(domain=[GINI_LABEL, ENTROPY_LABEL], range=[[1, 0], [8, 4]])

# Lines with color and dash differentiation
lines = (
    alt.Chart(df)
    .mark_line(strokeWidth=4)
    .encode(
        x=alt.X(
            "p:Q",
            title="Probability p",
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(labelFontSize=10, titleFontSize=12),
        ),
        y=alt.Y(
            "Impurity:Q",
            title="Impurity Measure (normalized)",
            scale=alt.Scale(domain=[0, 1.1]),
            axis=alt.Axis(labelFontSize=10, titleFontSize=12),
        ),
        color=alt.Color(
            "Measure:N",
            scale=color_scale,
            legend=alt.Legend(
                title=None, labelFontSize=10, orient="top-right", offset=10, symbolStrokeWidth=4, symbolSize=300
            ),
        ),
        strokeDash=alt.StrokeDash("Measure:N", scale=dash_scale, legend=None),
    )
)

# Dots at maxima (p=0.5 for both curves)
annotation_point = (
    alt.Chart(annotation_df).mark_point(size=150, filled=True, color=INK, opacity=0.75).encode(x="p:Q", y="Impurity:Q")
)

# Text labels at maxima
annotation_text = (
    alt.Chart(annotation_df)
    .mark_text(fontSize=10, dx=65, fontWeight="bold", align="left", color=INK)
    .encode(x="p:Q", y="Impurity:Q", text="label:N")
)

# Vertical rule at p=0.5 where both measures peak
rule_df = pd.DataFrame({"p": [0.5]})
vertical_rule = alt.Chart(rule_df).mark_rule(strokeDash=[6, 4], strokeWidth=1.5, color=INK_MUTED).encode(x="p:Q")

# Compose
chart = (
    (lines + vertical_rule + annotation_point + annotation_text)
    .properties(
        width=620, height=320, background=PAGE_BG, title=alt.Title(title_text, fontSize=title_fontsize, color=INK)
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.13, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, labelFontSize=10
    )
    .configure_title(color=INK, fontSize=title_fontsize)
)

# Save PNG + HTML
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad PNG to exact target dimensions (PAD only — never crop)
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
