""" anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import pygal
import statsmodels.api as sm
from pygal.style import Style
from scipy.special import expit


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: fit and band take position 1, the classes follow in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
THRESHOLD = 0.5  # default decision threshold of a binary classifier
JITTER = 0.025  # half-width of the vertical jitter around 0 and 1

# Columns: set these to your table's column names
BIOMARKER = "Biomarker Level"  # role: x
DISEASE = "Disease (0 = negative, 1 = positive)"  # role: y
PROBABILITY = "Probability of Disease"  # role: probability
CI_LOWER = "95% CI lower"  # role: ci_lower
CI_UPPER = "95% CI upper"  # role: ci_upper

# Data: medical diagnosis by biomarker level; replace with your own table, e.g. df = pd.read_csv("model.csv")
np.random.seed(42)
n_samples = 150
biomarker_levels = np.concatenate([np.random.normal(30, 15, n_samples // 2), np.random.normal(70, 15, n_samples // 2)])
biomarker_levels = np.clip(biomarker_levels, 0, 100)
true_probs = 1 / (1 + np.exp(-0.08 * (biomarker_levels - 50)))
outcome = (np.random.random(n_samples) < true_probs).astype(int)

# Logistic regression; the 95% CI comes from the coefficient covariance on the logit scale
design = sm.add_constant(biomarker_levels)
model = sm.Logit(outcome, design).fit(disp=0)
logit = design @ model.params
logit_se = np.sqrt(np.einsum("ij,jk,ik->i", design, model.cov_params(), design))
df = pd.DataFrame(
    {
        BIOMARKER: biomarker_levels,
        DISEASE: outcome,
        PROBABILITY: expit(logit),
        CI_LOWER: expit(logit - 1.96 * logit_se),
        CI_UPPER: expit(logit + 1.96 * logit_se),
    }
)

# Plot: pygal takes plain (x, y) lists, built from df
curve = df.dropna(subset=[BIOMARKER, PROBABILITY]).sort_values(BIOMARKER)
band = curve.dropna(subset=[CI_LOWER, CI_UPPER])
band_pts = list(zip(band[BIOMARKER], band[CI_UPPER], strict=True)) + list(
    zip(band[BIOMARKER][::-1], band[CI_LOWER][::-1], strict=True)
)
x_min, x_max = curve[BIOMARKER].min(), curve[BIOMARKER].max()
x_pad = (x_max - x_min) * 0.04

obs_all = df.dropna(subset=[BIOMARKER, DISEASE])
outcome_row = obs_all[DISEASE].astype(float).round().clip(0, 1)  # the outcome is binary: one row per class
classes = sorted(outcome_row.unique())
rng = np.random.default_rng(7)

# Series colors in add order: band, fit, threshold, then one palette position per class
series_colors = (IMPRINT_PALETTE[0], IMPRINT_PALETTE[0], INK_MUTED) + tuple(
    IMPRINT_PALETTE[1 + i] for i in range(len(classes))
)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=series_colors,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
    opacity=0.6,
    opacity_hover=0.9,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="logistic-regression · python · pygal · anyplot.ai",
    x_title=BIOMARKER,
    y_title=PROBABILITY,
    show_x_guides=True,
    show_y_guides=True,
    range=(0, 1.05),
    xrange=(x_min - x_pad, x_max + x_pad),
    explicit_size=True,
    legend_at_bottom=True,
    legend_box_size=36,
    truncate_legend=-1,
    print_values=False,
    # Per-series widths go in CSS because the style's .reactive rule outranks stroke_style;
    # the band is one closed polygon with a light fill so points and grid show through
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.serie-0 .reactive{fill-opacity:0.18 !important;stroke-width:1.5 !important}"
        " .serie-1 .reactive{stroke-width:7 !important} .serie-2 .reactive{stroke-width:3.5 !important}",
        # graph.css pins .dot to full opacity; class dots get 0.6 so piled-up stretches read darker
        "inline:" + ", ".join(f".serie-{3 + i} .dot" for i in range(len(classes))) + "{fill-opacity:0.6 !important}",
    ],
)

chart.add("95% CI", band_pts, fill=True, show_dots=False)
chart.add("Logistic fit", list(zip(curve[BIOMARKER], curve[PROBABILITY], strict=True)), show_dots=False)
chart.add(
    f"Threshold (p = {THRESHOLD:g})",
    [(x_min, THRESHOLD), (x_max, THRESHOLD)],
    show_dots=False,
    stroke_style={"dasharray": "18,10"},
)
for cls in classes:
    obs = obs_all[outcome_row == cls]
    y_jit = cls + rng.uniform(-JITTER, JITTER, len(obs))
    chart.add(
        f"{'Positive' if cls else 'Negative'} ({cls:g})",
        list(zip(obs[BIOMARKER], y_jit, strict=True)),
        stroke=False,
        dots_size=11,
    )

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
