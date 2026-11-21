"""anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: altair 6.1.0 | Python 3.13.13
Quality: 83/100 | Created: 2026-05-13
"""

import os
import sys


# Workaround for import conflict: remove script directory from path
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.stats import norm  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 1 for the points, position 2 for the smoothers
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
COOK_LEVELS = [0.5, 1.0]  # Cook's distance contours named by the spec
COOK_DASHES = [[6, 3], [2, 2]]  # one dash pattern per contour level
N_LABELLED = 3  # most influential observations that get an index label

# Columns: set these to your table's column names
OBS = "Observation"  # role: extra
FITTED = "Fitted values"  # role: fitted
RESIDUAL = "Residuals"  # role: residuals
STD_RESID = "Standardized residuals"  # role: std_residuals
LEVERAGE = "Leverage"  # role: leverage
COOKS_D = "Cook's distance"  # role: cooks_d

# Data: replace this block with your own table, for example df = pd.read_csv("model_diagnostics.csv")
# Housing price model (sqft, bedrooms, age) with three planted outliers, fitted by OLS
np.random.seed(42)
n_obs = 150
sqft = np.random.uniform(800, 3500, n_obs)
bedrooms = np.random.randint(1, 6, n_obs).astype(float)
age_yr = np.random.uniform(0, 50, n_obs)
X = sm.add_constant(np.column_stack([sqft, bedrooms, age_yr]))
price = X @ np.array([50000.0, 120.0, 8000.0, -800.0]) + np.random.normal(0, 25000, n_obs)
price[12] += 180000
price[47] -= 150000
price[88] += 120000
fit = sm.OLS(price, X).fit()
influence = fit.get_influence()
df = pd.DataFrame(
    {
        OBS: np.arange(n_obs),
        FITTED: np.asarray(fit.fittedvalues),
        RESIDUAL: np.asarray(fit.resid),
        STD_RESID: np.asarray(influence.resid_studentized_internal),
        LEVERAGE: np.asarray(influence.hat_matrix_diag),
        COOKS_D: np.asarray(influence.cooks_distance[0]),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
SQRT_ABS = "√|Standardized residuals|"
THEORETICAL = "Theoretical quantiles"
SMOOTH = "LOWESS"
LEVEL = "Contour level"
BRANCH = "Contour branch"
LABEL = "Label"

n = len(df)
p_params = df[LEVERAGE].sum()  # the trace of the hat matrix equals the number of model parameters
df[SQRT_ABS] = np.sqrt(np.abs(df[STD_RESID]))
df[THEORETICAL] = norm.ppf((df[STD_RESID].rank(method="first") - 0.5) / n)
df[LABEL] = ""
top = df[COOKS_D].nlargest(N_LABELLED).index
df.loc[top, LABEL] = df.loc[top, OBS].astype(str)
labelled = df.loc[top]

W, H = 329, 127
POINT_SIZE, POINT_OPACITY = 70, 0.75
TICK_FONT, AXIS_FONT, PANEL_FONT, LABEL_FONT = 10, 12, 14, 10


def ref(frame, x, y, **mark):
    return (
        alt.Chart(frame)
        .mark_line(**mark)
        .encode(x=alt.X(x.translate(ESCAPE), type="quantitative"), y=alt.Y(y.translate(ESCAPE), type="quantitative"))
    )


def smoother(x, y):
    smooth = sm.nonparametric.lowess(df[y], df[x], frac=0.4)
    frame = pd.DataFrame({x: smooth[:, 0], y: smooth[:, 1]})
    return ref(frame, x, y, color=IMPRINT_PALETTE[1], strokeWidth=2)


def panel(x, y, title, x_title, y_title, extras=()):
    pts = (
        alt.Chart(df)
        .mark_circle(color=IMPRINT_PALETTE[0], opacity=POINT_OPACITY, size=POINT_SIZE)
        .encode(
            x=alt.X(x.translate(ESCAPE), type="quantitative", title=x_title, scale=alt.Scale(zero=False)),
            y=alt.Y(y.translate(ESCAPE), type="quantitative", title=y_title, scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip(OBS.translate(ESCAPE), type="quantitative", title=OBS),
                alt.Tooltip(y.translate(ESCAPE), type="quantitative", title=y_title, format=".3f"),
            ],
        )
    )
    lbl = (
        alt.Chart(labelled)
        .mark_text(color=INK, fontSize=LABEL_FONT, fontWeight="bold", dx=9, dy=-7)
        .encode(
            x=alt.X(x.translate(ESCAPE), type="quantitative"),
            y=alt.Y(y.translate(ESCAPE), type="quantitative"),
            text=alt.Text(LABEL.translate(ESCAPE), type="nominal"),
        )
    )
    layered = alt.layer(pts, *extras, lbl)
    return layered.properties(
        width=W, height=H, title=alt.TitleParams(text=title, fontSize=PANEL_FONT, color=INK, anchor="start")
    )


def zero_rule():
    return (
        alt.Chart(pd.DataFrame({"zero": [0.0]}))
        .mark_rule(color=INK_SOFT, strokeDash=[6, 3], strokeWidth=1)
        .encode(y="zero:Q")
    )


# Panel 1: residuals vs fitted, zero line and LOWESS smoother
chart1 = panel(FITTED, RESIDUAL, "Residuals vs Fitted", FITTED, RESIDUAL, [zero_rule(), smoother(FITTED, RESIDUAL)])

# Panel 2: normal Q-Q against the 45-degree line (standardized residuals are ~ N(0, 1))
span = [df[THEORETICAL].min(), df[THEORETICAL].max()]
qq_line = ref(
    pd.DataFrame({THEORETICAL: span, STD_RESID: span}),
    THEORETICAL,
    STD_RESID,
    color=INK_SOFT,
    strokeDash=[6, 3],
    strokeWidth=1,
)
chart2 = panel(THEORETICAL, STD_RESID, "Normal Q–Q", THEORETICAL, STD_RESID, [qq_line])

# Panel 3: scale-location with LOWESS smoother
chart3 = panel(FITTED, SQRT_ABS, "Scale–Location", FITTED, SQRT_ABS, [smoother(FITTED, SQRT_ABS)])

# Panel 4: residuals vs leverage with Cook's distance contours at both signs
sr_max = df[STD_RESID].abs().max() * 1.15
# Extend leverage far enough that every contour comes into view of the residual range
h_reach = max(level * p_params / (sr_max**2 + level * p_params) for level in COOK_LEVELS)
h = np.linspace(df[LEVERAGE].min() * 0.5, max(df[LEVERAGE].max() * 1.5, h_reach * 1.05), 400)
contours, contour_ends = [], []
for level, dash in zip(COOK_LEVELS, COOK_DASHES, strict=False):
    curve = np.sqrt(level * p_params * (1 - h) / h)
    keep = curve <= sr_max
    if not keep.any():
        continue
    for sign in (1, -1):
        frame = pd.DataFrame({LEVERAGE: h[keep], STD_RESID: sign * curve[keep], BRANCH: f"{level}_{sign}"})
        contours.append(
            ref(frame, LEVERAGE, STD_RESID, color=INK_SOFT, strokeWidth=1.25, strokeDash=dash).encode(
                detail=alt.Detail(BRANCH.translate(ESCAPE), type="nominal")
            )
        )
    contour_ends.append({LEVERAGE: h[keep][-1], STD_RESID: curve[keep][-1], LEVEL: f"D = {level}"})
contour_tags = (
    alt.Chart(pd.DataFrame(contour_ends))
    .mark_text(color=INK_SOFT, fontSize=LABEL_FONT, align="right", dx=-2, dy=-7)
    .encode(
        x=alt.X(LEVERAGE.translate(ESCAPE), type="quantitative"),
        y=alt.Y(STD_RESID.translate(ESCAPE), type="quantitative"),
        text=alt.Text(LEVEL.translate(ESCAPE), type="nominal"),
    )
)
chart4 = panel(
    LEVERAGE, STD_RESID, "Residuals vs Leverage", LEVERAGE, STD_RESID, [zero_rule(), *contours, contour_tags]
)

# Style
title = "diagnostic-regression-panel · python · altair · anyplot.ai"
fig = (
    alt.concat(chart1, chart2, chart3, chart4, columns=2)
    .properties(
        title=alt.TitleParams(text=title, fontSize=18, color=INK, anchor="middle", offset=10), background=PAGE_BG
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_concat(spacing=28)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=TICK_FONT,
        titleFontSize=AXIS_FONT,
    )
)

fig.save(f"plot-{THEME}.png", scale_factor=4.0)
fig.save(f"plot-{THEME}.html")

# Pad (never crop) to the exact 3200 x 1800 landscape canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    # Wide tick labels (other data) grow the figure: re-render smaller instead of cropping
    shrink = min(TW / img.width, TH / img.height) * 0.995
    fig.save(f"plot-{THEME}.png", scale_factor=4.0 * shrink)
    img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
