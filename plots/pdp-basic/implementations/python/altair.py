"""anyplot.ai
pdp-basic: Partial Dependence Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 100/100 | Updated: 2026-05-15
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

# Column constants
FEATURE = "Temperature (standardized units)"  # role: feature_values
PARTIAL_DEP = "Partial dependence (predicted outcome)"  # role: partial_dependence
CI_LOWER = "95% CI lower"  # role: confidence_interval
CI_UPPER = "95% CI upper"  # role: extra
IS_RUG = "Observed sample"  # role: extra

# Data: replace this block with your own table, one row per grid point (rug rows carry only the feature value)
np.random.seed(42)
X, y = make_regression(n_samples=500, n_features=5, noise=10, random_state=42)
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Partial dependence of the first feature (Temperature) on an 80-point grid
pd_result = partial_dependence(model, X, features=[0], grid_resolution=80, kind="average")
grid = pd_result["grid_values"][0]
average = pd_result["average"][0]

# Bootstrap the training rows for a 95% band
bootstrap_pds = []
for _ in range(50):
    indices = np.random.choice(len(X), size=len(X), replace=True)
    pd_boot = partial_dependence(model, X[indices], features=[0], grid_resolution=80, kind="average")
    bootstrap_pds.append(pd_boot["average"][0])
bootstrap_pds = np.array(bootstrap_pds)

# Rug: a sample of the observed feature values
rug_sample = np.random.choice(X[:, 0], size=100, replace=False)

df = pd.concat(
    [
        pd.DataFrame(
            {
                FEATURE: grid,
                PARTIAL_DEP: average,
                CI_LOWER: np.percentile(bootstrap_pds, 2.5, axis=0),
                CI_UPPER: np.percentile(bootstrap_pds, 97.5, axis=0),
                IS_RUG: False,
            }
        ),
        pd.DataFrame({FEATURE: rug_sample, IS_RUG: True}),
    ],
    ignore_index=True,
)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
F, P, LO, HI, RUG = (c.translate(ESCAPE) for c in (FEATURE, PARTIAL_DEP, CI_LOWER, CI_UPPER, IS_RUG))
HEIGHT = 320
curve_rows = f"!datum['{IS_RUG}']"

x_enc = alt.X(F, type="quantitative", title=FEATURE)

band = (
    alt.Chart(df)
    .transform_filter(curve_rows)
    .mark_area(opacity=0.2, color=BRAND)
    .encode(x=x_enc, y=alt.Y(LO, type="quantitative", title=PARTIAL_DEP), y2=alt.Y2(HI))
)

line = (
    alt.Chart(df)
    .transform_filter(curve_rows)
    .mark_line(strokeWidth=3, color=BRAND)
    .encode(
        x=x_enc,
        y=alt.Y(P, type="quantitative", title=PARTIAL_DEP),
        tooltip=[
            alt.Tooltip(F, type="quantitative", title=FEATURE, format=".2f"),
            alt.Tooltip(P, type="quantitative", title=PARTIAL_DEP, format=".2f"),
        ],
    )
)

rug = (
    alt.Chart(df)
    .transform_filter(f"datum['{IS_RUG}']")
    .mark_tick(thickness=1.5, size=14, color=BRAND, opacity=0.4)
    .encode(x=x_enc, y=alt.value(HEIGHT - 8))
)

chart = (
    alt.layer(band, line, rug)
    .properties(
        width=620,
        height=HEIGHT,
        title=alt.Title(text="pdp-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_title(color=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the 3200 x 1800 canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
