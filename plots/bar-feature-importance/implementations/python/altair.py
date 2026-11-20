"""anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-10
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]  # single-polarity ramp: brand green to blue

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Importance score"  # role: importance
STD = "Std. deviation"  # role: std

# Data: replace this block with your own table, for example df = pd.read_csv("importances.csv")
# Feature importances from a hypothetical RandomForest churn model
np.random.seed(42)
importances = [0.182, 0.156, 0.134, 0.098, 0.087, 0.072, 0.058, 0.051, 0.042, 0.038, 0.031, 0.022, 0.015, 0.009, 0.005]
df = pd.DataFrame(
    {
        FEATURE: [
            "customer_lifetime_value",
            "purchase_frequency",
            "avg_order_value",
            "days_since_last_purchase",
            "total_purchases",
            "account_age_months",
            "email_open_rate",
            "website_visits",
            "support_tickets",
            "referral_count",
            "cart_abandonment_rate",
            "discount_usage",
            "mobile_app_usage",
            "newsletter_subscribed",
            "social_media_engagement",
        ],
        IMPORTANCE: importances,
        STD: np.array(importances) * np.random.uniform(0.15, 0.35, len(importances)),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
LOW, HIGH = "low", "high"
plot_df = df.copy()
plot_df[LOW] = df[IMPORTANCE] - df[STD]
plot_df[HIGH] = df[IMPORTANCE] + np.fmax(df[STD], 0)
x_max = plot_df[HIGH].max() * 1.12

base = alt.Chart(plot_df).encode(
    y=alt.Y(
        FEATURE.translate(ESCAPE),
        type="nominal",
        title=FEATURE,
        sort=df.sort_values(IMPORTANCE, ascending=False)[FEATURE].tolist(),
        axis=alt.Axis(labelLimit=400, ticks=False, domain=False),
    )
)

x_scale = alt.Scale(domain=[0, x_max], nice=False)
bars = base.mark_bar(size=17).encode(
    x=alt.X(IMPORTANCE.translate(ESCAPE), type="quantitative", title=IMPORTANCE, scale=x_scale),
    color=alt.Color(IMPORTANCE.translate(ESCAPE), type="quantitative", scale=alt.Scale(range=IMPRINT_SEQ), legend=None),
    tooltip=[
        alt.Tooltip(FEATURE.translate(ESCAPE), type="nominal", title=FEATURE),
        alt.Tooltip(IMPORTANCE.translate(ESCAPE), type="quantitative", title=IMPORTANCE, format=".3f"),
        alt.Tooltip(STD.translate(ESCAPE), type="quantitative", title=STD, format=".3f"),
    ],
)

error_bars = base.mark_rule(color=INK, strokeWidth=1.6).encode(
    x=alt.X(LOW, type="quantitative", scale=x_scale), x2=alt.X2(HIGH)
)

labels = base.mark_text(align="left", baseline="middle", dx=6, fontSize=11, fontWeight="bold", color=INK).encode(
    x=alt.X(HIGH, type="quantitative", scale=x_scale),
    text=alt.Text(IMPORTANCE.translate(ESCAPE), type="quantitative", format=".3f"),
)

chart = (
    (bars + error_bars + labels)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            "bar-feature-importance · python · altair · anyplot.ai", fontSize=16, anchor="start", color=INK
        ),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        gridColor=INK,
        gridOpacity=0.10,
        labelFontSize=11,
        titleFontSize=13,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
)

# Save output, padded (never cropped) to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
