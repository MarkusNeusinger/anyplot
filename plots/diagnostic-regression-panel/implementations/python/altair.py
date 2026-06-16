""" anyplot.ai
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
from scipy.stats import probplot  # noqa: E402
from statsmodels.nonparametric.smoothers_lowess import lowess  # noqa: E402
from statsmodels.regression.linear_model import OLS  # noqa: E402
from statsmodels.stats.outliers_influence import OLSInfluence  # noqa: E402
from statsmodels.tools import add_constant  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"
ACCENT = "#C475FD"

# Data — housing price prediction scenario
np.random.seed(42)
n = 150
sqft = np.random.uniform(800, 3500, n)
bedrooms = np.random.randint(1, 6, n).astype(float)
age_yr = np.random.uniform(0, 50, n)
X = add_constant(np.column_stack([sqft, bedrooms, age_yr]))
price = X @ np.array([50000.0, 120.0, 8000.0, -800.0]) + np.random.normal(0, 25000, n)

# Introduce a few influential outliers
price[12] += 180000
price[47] -= 150000
price[88] += 120000

model = OLS(price, X).fit()
influence = OLSInfluence(model)

fitted = np.asarray(model.fittedvalues)
residuals = np.asarray(model.resid)
std_resid = np.asarray(influence.resid_studentized_internal)
leverage_vals = np.asarray(influence.hat_matrix_diag)
cooks_d_vals = np.asarray(influence.cooks_distance[0])
p_params = X.shape[1]

top3 = set(np.argsort(cooks_d_vals)[-3:])

# LOWESS smoothers for subplot 1 and 3
smooth1 = lowess(residuals, fitted, frac=0.4)
smooth3 = lowess(np.sqrt(np.abs(std_resid)), fitted, frac=0.4)

# Main DataFrame
df_main = pd.DataFrame(
    {
        "fitted": fitted,
        "residuals": residuals,
        "std_resid": std_resid,
        "sqrt_abs_sr": np.sqrt(np.abs(std_resid)),
        "leverage": leverage_vals,
        "cooks_d": cooks_d_vals,
        "obs": np.arange(n),
        "label": [str(i) if i in top3 else "" for i in range(n)],
    }
)

# Q-Q plot data
sort_order = np.argsort(std_resid)
(theoretical_q, sample_q), (slope, intercept, _) = probplot(std_resid, fit=True)
extreme_qq_pos = set(np.argsort(np.abs(sample_q))[-3:])
qq_df = pd.DataFrame(
    {
        "theoretical": theoretical_q,
        "sample": sample_q,
        "label": [str(sort_order[i]) if i in extreme_qq_pos else "" for i in range(n)],
    }
)
qq_ref_df = pd.DataFrame(
    {
        "theoretical": [theoretical_q[0], theoretical_q[-1]],
        "sample": [intercept + slope * theoretical_q[0], intercept + slope * theoretical_q[-1]],
    }
)

# LOWESS DataFrames
loess1_df = pd.DataFrame({"fitted": smooth1[:, 0], "smoothed": smooth1[:, 1]})
loess3_df = pd.DataFrame({"fitted": smooth3[:, 0], "smoothed": smooth3[:, 1]})

# Cook's distance contour data for subplot 4
h_vals = np.linspace(0.002, max(leverage_vals) * 1.5, 500)
sr_max = max(np.abs(std_resid)) * 1.15
contour_rows = []
for D in [0.5, 1.0]:
    sr_curve = np.sqrt(D * p_params * (1 - h_vals) / h_vals)
    for branch, sr_vals in [("pos", sr_curve), ("neg", -sr_curve)]:
        for h, sr in zip(h_vals, sr_vals, strict=True):
            if abs(sr) <= sr_max:
                contour_rows.append({"leverage": h, "std_resid": sr, "level": f"D={D}", "branch": f"{D}_{branch}"})
contour_df = (
    pd.DataFrame(contour_rows) if contour_rows else pd.DataFrame(columns=["leverage", "std_resid", "level", "branch"])
)

zero_df = pd.DataFrame({"y": [0.0]})
W, H = 740, 395

# ── Chart 1: Residuals vs Fitted ──
c1_pts = (
    alt.Chart(df_main)
    .mark_circle(color=BRAND, opacity=0.6, size=70)
    .encode(
        x=alt.X("fitted:Q", title="Fitted Values"),
        y=alt.Y("residuals:Q", title="Residuals"),
        tooltip=["obs:Q", alt.Tooltip("residuals:Q", format=".0f")],
    )
)
c1_ref = alt.Chart(zero_df).mark_rule(color=INK_SOFT, strokeDash=[6, 3], strokeWidth=1.5).encode(y="y:Q")
c1_loess = alt.Chart(loess1_df).mark_line(color=ACCENT, strokeWidth=2.5).encode(x="fitted:Q", y="smoothed:Q")
c1_lbl = (
    alt.Chart(df_main[df_main["label"] != ""])
    .mark_text(color=INK_MUTED, fontSize=14, dx=8, dy=-8)
    .encode(x="fitted:Q", y="residuals:Q", text="label:N")
)
chart1 = (c1_pts + c1_ref + c1_loess + c1_lbl).properties(
    width=W, height=H, title=alt.TitleParams(text="Residuals vs Fitted", fontSize=20, color=INK, anchor="start")
)

# ── Chart 2: Normal Q-Q ──
c2_pts = (
    alt.Chart(qq_df)
    .mark_circle(color=BRAND, opacity=0.6, size=70)
    .encode(
        x=alt.X("theoretical:Q", title="Theoretical Quantiles"), y=alt.Y("sample:Q", title="Standardized Residuals")
    )
)
c2_ref = (
    alt.Chart(qq_ref_df)
    .mark_line(color=INK_SOFT, strokeDash=[6, 3], strokeWidth=1.5)
    .encode(x="theoretical:Q", y="sample:Q")
)
c2_lbl = (
    alt.Chart(qq_df[qq_df["label"] != ""])
    .mark_text(color=INK_MUTED, fontSize=14, dx=8, dy=-8)
    .encode(x="theoretical:Q", y="sample:Q", text="label:N")
)
chart2 = (c2_pts + c2_ref + c2_lbl).properties(
    width=W, height=H, title=alt.TitleParams(text="Normal Q–Q", fontSize=20, color=INK, anchor="start")
)

# ── Chart 3: Scale-Location ──
c3_pts = (
    alt.Chart(df_main)
    .mark_circle(color=BRAND, opacity=0.6, size=70)
    .encode(
        x=alt.X("fitted:Q", title="Fitted Values"),
        y=alt.Y("sqrt_abs_sr:Q", title="√|Standardized Residuals|"),
        tooltip=["obs:Q", alt.Tooltip("sqrt_abs_sr:Q", format=".3f")],
    )
)
c3_loess = alt.Chart(loess3_df).mark_line(color=ACCENT, strokeWidth=2.5).encode(x="fitted:Q", y="smoothed:Q")
c3_lbl = (
    alt.Chart(df_main[df_main["label"] != ""])
    .mark_text(color=INK_MUTED, fontSize=14, dx=8, dy=-8)
    .encode(x="fitted:Q", y="sqrt_abs_sr:Q", text="label:N")
)
chart3 = (c3_pts + c3_loess + c3_lbl).properties(
    width=W, height=H, title=alt.TitleParams(text="Scale–Location", fontSize=20, color=INK, anchor="start")
)

# ── Chart 4: Residuals vs Leverage ──
c4_pts = (
    alt.Chart(df_main)
    .mark_circle(color=BRAND, opacity=0.6, size=70)
    .encode(
        x=alt.X("leverage:Q", title="Leverage"),
        y=alt.Y("std_resid:Q", title="Standardized Residuals"),
        tooltip=[
            "obs:Q",
            alt.Tooltip("leverage:Q", format=".3f"),
            alt.Tooltip("cooks_d:Q", format=".3f", title="Cook's D"),
        ],
    )
)
c4_ref = alt.Chart(zero_df).mark_rule(color=INK_SOFT, strokeDash=[6, 3], strokeWidth=1.5).encode(y="y:Q")
c4_lbl = (
    alt.Chart(df_main[df_main["label"] != ""])
    .mark_text(color=INK_MUTED, fontSize=14, dx=8, dy=-8)
    .encode(x="leverage:Q", y="std_resid:Q", text="label:N")
)

if len(contour_df) > 0:
    contour_05_df = contour_df[contour_df["level"] == "D=0.5"]
    contour_10_df = contour_df[contour_df["level"] == "D=1.0"]
    c4_c05 = (
        alt.Chart(contour_05_df)
        .mark_line(color=INK_SOFT, strokeWidth=1.5, strokeDash=[6, 3], opacity=0.8)
        .encode(x="leverage:Q", y="std_resid:Q", detail="branch:N")
    )
    c4_c10 = (
        alt.Chart(contour_10_df)
        .mark_line(color=INK_MUTED, strokeWidth=1.5, strokeDash=[3, 2], opacity=0.8)
        .encode(x="leverage:Q", y="std_resid:Q", detail="branch:N")
    )
    # Text labels at the end of positive contour branches
    contour_label_rows = []
    for D, df_c in [(0.5, contour_05_df), (1.0, contour_10_df)]:
        pos = df_c[df_c["branch"] == f"{D}_pos"]
        if len(pos) > 0:
            row = pos.iloc[-1]
            contour_label_rows.append({"leverage": row["leverage"], "std_resid": row["std_resid"], "label": f"D={D}"})
    if contour_label_rows:
        c4_clabels = (
            alt.Chart(pd.DataFrame(contour_label_rows))
            .mark_text(color=INK_SOFT, fontSize=13, dx=4, dy=-6)
            .encode(x="leverage:Q", y="std_resid:Q", text="label:N")
        )
        chart4_layers = c4_pts + c4_ref + c4_c05 + c4_c10 + c4_clabels + c4_lbl
    else:
        chart4_layers = c4_pts + c4_ref + c4_c05 + c4_c10 + c4_lbl
else:
    chart4_layers = c4_pts + c4_ref + c4_lbl

chart4 = chart4_layers.properties(
    width=W, height=H, title=alt.TitleParams(text="Residuals vs Leverage", fontSize=20, color=INK, anchor="start")
)

# ── Compose 2×2 panel ──
panel = (
    alt.concat(chart1, chart2, chart3, chart4, columns=2)
    .properties(
        title=alt.TitleParams(
            text="diagnostic-regression-panel · altair · anyplot.ai", fontSize=26, color=INK, anchor="middle", offset=14
        ),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0.5)
    .configure_concat(spacing=50)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=16,
        titleFontSize=18,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=14,
        titleFontSize=15,
    )
)

panel.save(f"plot-{THEME}.png", scale_factor=3.0)
panel.save(f"plot-{THEME}.html")
