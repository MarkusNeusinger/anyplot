""" anyplot.ai
qq-basic: Basic Q-Q Plot
Library: altair 6.1.0 | Python 3.14.4
Quality: 83/100 | Updated: 2026-04-27
"""

import os

import altair as alt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"


def norm_ppf(p):
    """Rational approximation to the inverse normal CDF (Abramowitz & Stegun)."""
    p, out = np.asarray(p, float), np.empty(len(p))
    lo, hi = p < 0.02425, p > 0.97575
    c = [
        -7.784894002430293e-3,
        -3.223964580411365e-1,
        -2.400758277161838e0,
        -2.549732539343734e0,
        4.374664141464968e0,
        2.938163982698783e0,
    ]
    d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996e0, 3.754408661907416e0, 1.0]
    for mask, sign in [(lo, 1), (hi, -1)]:
        t = np.sqrt(-2 * np.log(p[mask] if sign == 1 else 1 - p[mask]))
        out[mask] = sign * np.polyval(c, t) / np.polyval(d, t)
    m = ~lo & ~hi
    q = p[m] - 0.5
    r = q * q
    a = [
        -3.969683028665376e1,
        2.209460984245205e2,
        -2.759285104469687e2,
        1.383577518672690e2,
        -3.066479806614716e1,
        2.506628277459239e0,
    ]
    b = [
        -5.447609879822406e1,
        1.615858368580409e2,
        -1.556989798598866e2,
        6.680131188771972e1,
        -1.328068155288572e1,
        1.0,
    ]
    out[m] = q * np.polyval(a, r) / np.polyval(b, r)
    return out


np.random.seed(42)
sample = np.concatenate([np.random.normal(50, 10, 80), np.random.normal(75, 5, 20)])

n = len(sample)
sorted_sample = np.sort(sample)
p = (np.arange(1, n + 1) - 0.5) / n
sample_mean, sample_std = np.mean(sample), np.std(sample, ddof=1)
theoretical_scaled = norm_ppf(p) * sample_std + sample_mean

df = pd.DataFrame({"Theoretical Quantiles": theoretical_scaled, "Sample Quantiles": sorted_sample})

line_min = min(theoretical_scaled.min(), sorted_sample.min())
line_max = max(theoretical_scaled.max(), sorted_sample.max())
line_df = pd.DataFrame({"x": [line_min, line_max], "y": [line_min, line_max]})

points = (
    alt.Chart(df)
    .mark_point(size=200, color=BRAND, filled=True, opacity=0.7)
    .encode(
        x=alt.X("Theoretical Quantiles:Q", title="Theoretical Quantiles", scale=alt.Scale(zero=False)),
        y=alt.Y("Sample Quantiles:Q", title="Sample Quantiles", scale=alt.Scale(zero=False)),
        tooltip=["Theoretical Quantiles:Q", "Sample Quantiles:Q"],
    )
)

reference_line = (
    alt.Chart(line_df)
    .mark_line(color=INK_SOFT, strokeWidth=3, strokeDash=[8, 4])
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"))
)

chart = (
    (reference_line + points)
    .properties(
        background=PAGE_BG, width=1600, height=900, title=alt.Title("qq-basic · altair · anyplot.ai", fontSize=28)
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        gridDash=[4, 4],
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
    )
    .configure_title(color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
