"""anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: altair 6.2.2 | Python 3.13.14
Quality: 89/100 | Updated: 2026-06-30
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")
PILImage = importlib.import_module("PIL.Image")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1
ACCENT = "#BD8233"  # Imprint ochre — highlights peak-response group

# Data
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
y_values = [25.3, 38.7, 42.1, 35.8, 48.2, 31.5]

# Asymmetric errors: Treatment C shows wide lower bound; Treatment D peaks highest
asymmetric_lower = [2.1, 3.5, 2.8, 6.5, 4.8, 2.5]
asymmetric_upper = [2.1, 3.5, 2.8, 2.8, 2.2, 2.5]

df = pd.DataFrame(
    {
        "category": categories,
        "value": y_values,
        "error_lower": [y - el for y, el in zip(y_values, asymmetric_lower, strict=True)],
        "error_upper": [y + eu for y, eu in zip(y_values, asymmetric_upper, strict=True)],
    }
)

# Plot
y_scale = alt.Scale(domain=[15, 55], nice=False)
y_title = "Response Value (units)"

base = alt.Chart(df).encode(x=alt.X("category:N", title="Experimental Group", sort=categories))

# Condition-based encoding: Treatment D (peak response) accented in ochre via alt.condition()
highlight = alt.datum.category == "Treatment D"

error_bars = base.mark_rule(strokeWidth=3).encode(
    y=alt.Y("error_lower:Q", title=y_title, scale=y_scale),
    y2="error_upper:Q",
    color=alt.condition(highlight, alt.value(ACCENT), alt.value(BRAND)),
)

caps_top = base.mark_tick(thickness=3, size=22).encode(
    y=alt.Y("error_upper:Q", title=y_title, scale=y_scale),
    color=alt.condition(highlight, alt.value(ACCENT), alt.value(BRAND)),
)

caps_bottom = base.mark_tick(thickness=3, size=22).encode(
    y=alt.Y("error_lower:Q", title=y_title, scale=y_scale),
    color=alt.condition(highlight, alt.value(ACCENT), alt.value(BRAND)),
)

points = base.mark_circle().encode(
    y=alt.Y("value:Q", title=y_title, scale=y_scale),
    color=alt.condition(highlight, alt.value(ACCENT), alt.value(BRAND)),
    size=alt.condition(highlight, alt.value(480), alt.value(280)),
    tooltip=[
        alt.Tooltip("category:N", title="Group"),
        alt.Tooltip("value:Q", title="Mean", format=".2f"),
        alt.Tooltip("error_lower:Q", title="Lower bound", format=".2f"),
        alt.Tooltip("error_upper:Q", title="Upper bound", format=".2f"),
    ],
)

# Annotation surfacing the "Peak response" label for Treatment D
peak_df = df[df["category"] == "Treatment D"]
annotation = (
    alt.Chart(peak_df)
    .mark_text(dy=-28, color=ACCENT, fontSize=10, fontStyle="italic", text="Peak response")
    .encode(x=alt.X("category:N", sort=categories), y=alt.Y("error_upper:Q", scale=y_scale))
)

chart = (
    alt.layer(error_bars, caps_bottom, caps_top, points, annotation)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "errorbar-basic · python · altair · anyplot.ai", fontSize=16, color=INK, anchor="start", offset=20
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=11,
        titleFontSize=12,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        domainOpacity=0,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.13,
        labelAngle=0,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad to exact 3200×1800 target — only expand, never crop (AR-09 guard)
TW, TH = 3200, 1800
_img = PILImage.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = PILImage.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
