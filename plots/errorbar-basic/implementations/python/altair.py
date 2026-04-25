""" anyplot.ai
errorbar-basic: Basic Error Bar Plot
Library: altair 6.1.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-25
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
y_values = [25.3, 38.7, 42.1, 35.8, 48.2, 31.5]

# Asymmetric errors: Treatment C and D show notably different lower/upper bounds
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

error_bars = base.mark_rule(strokeWidth=3, color=BRAND).encode(
    y=alt.Y("error_lower:Q", title=y_title, scale=y_scale), y2="error_upper:Q"
)

caps_top = base.mark_tick(thickness=3, size=22, color=BRAND).encode(
    y=alt.Y("error_upper:Q", title=y_title, scale=y_scale)
)
caps_bottom = base.mark_tick(thickness=3, size=22, color=BRAND).encode(
    y=alt.Y("error_lower:Q", title=y_title, scale=y_scale)
)

points = base.mark_circle(size=320, color=BRAND).encode(
    y=alt.Y("value:Q", title=y_title, scale=y_scale),
    tooltip=[
        alt.Tooltip("category:N", title="Group"),
        alt.Tooltip("value:Q", title="Mean", format=".2f"),
        alt.Tooltip("error_lower:Q", title="Lower bound", format=".2f"),
        alt.Tooltip("error_upper:Q", title="Upper bound", format=".2f"),
    ],
)

chart = (
    alt.layer(error_bars, caps_bottom, caps_top, points)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("errorbar-basic · altair · anyplot.ai", fontSize=28, color=INK, anchor="start", offset=20),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelAngle=0,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
