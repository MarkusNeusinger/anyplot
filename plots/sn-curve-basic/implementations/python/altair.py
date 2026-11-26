"""anyplot.ai
sn-curve-basic: S-N Curve (Wöhler Curve)
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-20
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

# Imprint palette: data and fit take position 1, the three reference lines positions 2-4
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: material properties of the medium-carbon steel, true for any test series
REFERENCE_STRESS = {"UTS: 520 MPa": 520, "YS: 380 MPa": 380, "EL: 150 MPa": 150}
ENDURANCE_LIMIT = REFERENCE_STRESS["EL: 150 MPa"]
REGIONS = ["Low-Cycle Fatigue", "High-Cycle Fatigue", "Infinite Life"]

# Columns: set these to your table's column names
CYCLES = "Cycles to Failure (N)"  # role: cycles
STRESS = "Stress Amplitude (MPa)"  # role: stress

# Data: replace this block with your own table, for example df = pd.read_csv("fatigue_tests.csv")
rng = np.random.default_rng(42)
basquin_a, basquin_b = 800, -0.12
stress_levels = [450, 400, 350, 300, 275, 250, 225, 200, 180, 160]
rows = []
for level in stress_levels:
    life = (level / basquin_a) ** (1 / basquin_b)
    n_specimens = rng.integers(3, 6)
    for cycles in life * np.exp(rng.normal(0, 0.3, n_specimens)):
        rows.append((cycles, level))
df = pd.DataFrame(rows, columns=[CYCLES, STRESS])

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
CYC, STR = CYCLES.translate(ESCAPE), STRESS.translate(ESCAPE)

# Axis domains from the data: cycles with a margin, stress from the endurance band to above the strength line
x_domain = [df[CYCLES].min() * 0.6, df[CYCLES].max() * 3]
y_domain = [min(df[STRESS].min(), ENDURANCE_LIMIT) * 0.75, max(df[STRESS].max(), *REFERENCE_STRESS.values()) * 1.45]
x_scale = alt.Scale(type="log", domain=x_domain)
y_scale = alt.Scale(type="log", domain=y_domain)

# Basquin fit: a straight line in log-log space through the specimens
valid = df[[CYCLES, STRESS]].dropna().astype(float)
slope, intercept = np.polyfit(np.log10(valid[CYCLES]), np.log10(valid[STRESS]), 1)
fit_cycles = np.logspace(np.log10(df[CYCLES].min()), np.log10(df[CYCLES].max()), 100)
fit_df = pd.DataFrame({CYCLES: fit_cycles, STRESS: 10**intercept * fit_cycles**slope})

ref_df = pd.DataFrame({"Property": list(REFERENCE_STRESS), STRESS: list(REFERENCE_STRESS.values())})
band_df = pd.DataFrame({"low": [y_domain[0]], "high": [ENDURANCE_LIMIT]})

# Region labels sit at fractions of the log axis: the two fatigue regions at the top, infinite life in the band
log_lo = np.log10(x_domain[0])
span = np.log10(x_domain[1]) - log_lo
top_stress = y_domain[1] / 1.12
region_df = pd.DataFrame(
    {
        CYCLES: [10 ** (log_lo + 0.03 * span), 10 ** (log_lo + 0.45 * span), 10 ** (log_lo + 0.72 * span)],
        STRESS: [top_stress, top_stress, y_domain[0] * 1.25],
        "Region": REGIONS,
    }
)

TITLE = "sn-curve-basic · python · altair · anyplot.ai"

band = (
    alt.Chart(band_df)
    .mark_rect(opacity=0.10, color=IMPRINT_PALETTE[3])
    .encode(y=alt.Y("low:Q", scale=y_scale), y2=alt.Y2("high:Q"))
)

points = (
    alt.Chart(df)
    .mark_point(size=180, filled=True, opacity=0.75, color=IMPRINT_PALETTE[0], stroke=PAGE_BG, strokeWidth=0.8)
    .encode(
        x=alt.X(CYC, type="quantitative", scale=x_scale, title=CYCLES),
        y=alt.Y(STR, type="quantitative", scale=y_scale, title=STRESS),
        tooltip=[alt.Tooltip(CYC, title=CYCLES), alt.Tooltip(STR, title=STRESS)],
    )
)

fit_line = (
    alt.Chart(fit_df)
    .mark_line(strokeWidth=3, opacity=0.9, color=IMPRINT_PALETTE[0])
    .encode(x=alt.X(CYC, type="quantitative", scale=x_scale), y=alt.Y(STR, type="quantitative", scale=y_scale))
)

ref_rules = (
    alt.Chart(ref_df)
    .mark_rule(strokeDash=[14, 6], strokeWidth=3)
    .encode(
        y=alt.Y(STR, type="quantitative", scale=y_scale),
        color=alt.Color(
            "Property:N",
            scale=alt.Scale(domain=list(REFERENCE_STRESS), range=IMPRINT_PALETTE[1:4]),
            legend=alt.Legend(
                title="Material Properties", titleFontSize=12, labelFontSize=10, labelLimit=200, orient="top-right"
            ),
        ),
    )
)

region_labels = (
    alt.Chart(region_df)
    .mark_text(fontSize=11, fontStyle="italic", align="left", baseline="top", color=INK_SOFT)
    .encode(
        x=alt.X(CYC, type="quantitative", scale=x_scale),
        y=alt.Y(STR, type="quantitative", scale=y_scale),
        text="Region:N",
    )
)

chart = (
    (band + points + fit_line + ref_rules + region_labels)
    .properties(
        width=800,
        height=450,
        background=PAGE_BG,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        title=alt.Title(TITLE, fontSize=16),
    )
    .configure_view(fill=PAGE_BG, strokeOpacity=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.06,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_title(color=INK, fontWeight="bold")
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=12,
        labelFontSize=10,
        padding=8,
    )
)

# Save PNG and interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Scale to the exact canvas if vl-convert lands off target (never crop)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
