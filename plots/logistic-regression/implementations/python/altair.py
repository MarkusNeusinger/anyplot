"""anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per class in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
THRESHOLD = 0.5  # default decision threshold of a binary classifier
Z_95 = 1.96  # normal quantile for a 95 % confidence interval

# Columns: set these to your table's column names
STUDY_HOURS = "Study hours (hrs)"  # role: x
PASSED = "Passed exam (0 = no, 1 = yes)"  # role: y
PROBABILITY = "Probability"  # role: probability
LOWER = "Lower 95 % bound"  # role: ci_lower
UPPER = "Upper 95 % bound"  # role: ci_upper

# Data: replace this block with your own table, for example df = pd.read_csv("exams.csv")
np.random.seed(42)
hours_fail = np.random.normal(3, 1.5, 60)
hours_pass = np.random.normal(7, 1.5, 90)
df = pd.DataFrame(
    {
        STUDY_HOURS: np.clip(np.concatenate([hours_fail, hours_pass]), 0.5, 10),
        PASSED: np.concatenate([np.zeros(60), np.ones(90)]),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
OUTCOME = "Outcome class"
Y_JITTERED = "Probability (jittered)"

data = df.dropna(subset=[STUDY_HOURS, PASSED])
hours = data[STUDY_HOURS].to_numpy(dtype=float)
raw = data[PASSED].to_numpy(dtype=float)
passed = (raw > (raw.min() + raw.max()) / 2).astype(float)  # two classes: upper and lower half of the range

# Fit the logistic regression by Newton-Raphson (IRLS) on the standardized predictor;
# a small ridge keeps the step finite when the classes separate perfectly
centre, spread = hours.mean(), hours.std() or 1.0
design = np.column_stack([np.ones(len(hours)), (hours - centre) / spread])
beta = np.zeros(2)
for _ in range(25):
    p_hat = 1 / (1 + np.exp(-design @ beta))
    information = design.T @ (design * (p_hat * (1 - p_hat))[:, None]) + 1e-6 * np.eye(2)
    beta += np.linalg.solve(information, design.T @ (passed - p_hat))
covariance = np.linalg.inv(information)

# Fitted curve with a 95 % band from the delta method on the logit scale
pad = 0.05 * (hours.max() - hours.min())
x_curve = np.linspace(hours.min() - pad, hours.max() + pad, 200)
curve_design = np.column_stack([np.ones(len(x_curve)), (x_curve - centre) / spread])
logit = curve_design @ beta
logit_se = np.sqrt(np.einsum("ij,jk,ik->i", curve_design, covariance, curve_design))
curve_df = pd.DataFrame(
    {
        STUDY_HOURS: x_curve,
        PROBABILITY: 1 / (1 + np.exp(-logit)),
        LOWER: 1 / (1 + np.exp(-(logit - Z_95 * logit_se))),
        UPPER: 1 / (1 + np.exp(-(logit + Z_95 * logit_se))),
    }
)

# Observations: jittered along y only, one color per class
rng = np.random.default_rng(7)
class_names = {0.0: "No", 1.0: "Yes"}
points_df = pd.DataFrame(
    {
        STUDY_HOURS: hours,
        Y_JITTERED: passed + rng.uniform(-0.03, 0.03, len(passed)),
        OUTCOME: [class_names.get(v, str(v)) for v in passed],
    }
)
classes = list(dict.fromkeys(points_df.sort_values(Y_JITTERED)[OUTCOME]))
x_domain = [curve_df[STUDY_HOURS].min(), curve_df[STUDY_HOURS].max()]


x_enc = alt.X(
    STUDY_HOURS.translate(ESCAPE), type="quantitative", title=STUDY_HOURS, scale=alt.Scale(domain=x_domain, nice=False)
)
y_scale = alt.Scale(domain=[-0.06, 1.06])

ci_band = (
    alt.Chart(curve_df)
    .mark_area(opacity=0.25, color=INK_SOFT)
    .encode(
        x=x_enc,
        y=alt.Y(LOWER.translate(ESCAPE), type="quantitative", title=PROBABILITY, scale=y_scale),
        y2=alt.Y2(UPPER.translate(ESCAPE)),
    )
)

curve = (
    alt.Chart(curve_df)
    .mark_line(strokeWidth=2.5, color=INK)
    .encode(x=x_enc, y=alt.Y(PROBABILITY.translate(ESCAPE), type="quantitative", title=PROBABILITY, scale=y_scale))
)

threshold_df = pd.DataFrame({PROBABILITY: [THRESHOLD]})
threshold = (
    alt.Chart(threshold_df)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.5, color=INK_SOFT)
    .encode(y=alt.Y(PROBABILITY.translate(ESCAPE), type="quantitative", scale=y_scale))
)
threshold_label = (
    alt.Chart(
        pd.DataFrame({STUDY_HOURS: [x_domain[1]], PROBABILITY: [THRESHOLD], "label": [f"Threshold p = {THRESHOLD}"]})
    )
    .mark_text(align="right", baseline="bottom", dx=-4, dy=-4, fontSize=10, color=INK_SOFT)
    .encode(x=x_enc, y=alt.Y(PROBABILITY.translate(ESCAPE), type="quantitative", scale=y_scale), text="label:N")
)

points = (
    alt.Chart(points_df)
    .mark_circle(size=45, opacity=0.6, stroke=PAGE_BG, strokeWidth=0.5)
    .encode(
        x=x_enc,
        y=alt.Y(Y_JITTERED.translate(ESCAPE), type="quantitative", title=PROBABILITY, scale=y_scale),
        color=alt.Color(
            OUTCOME.translate(ESCAPE),
            type="nominal",
            title=PASSED,
            sort=classes,
            scale=alt.Scale(domain=classes, range=IMPRINT_PALETTE[: len(classes)]),
        ),
        tooltip=[
            alt.Tooltip(STUDY_HOURS.translate(ESCAPE), title=STUDY_HOURS),
            alt.Tooltip(OUTCOME.translate(ESCAPE), title=PASSED),
        ],
    )
)

chart = (
    alt.layer(ci_band, curve, threshold, threshold_label, points)
    .properties(
        width=570,
        height=370,
        background=PAGE_BG,
        title=alt.Title("logistic-regression · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        gridOpacity=0.15,
        gridColor=INK_SOFT,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(
        labelFontSize=10,
        titleFontSize=10,
        symbolSize=80,
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        padding=6,
    )
)

# Save: PNG padded (never cropped) to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds target {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
