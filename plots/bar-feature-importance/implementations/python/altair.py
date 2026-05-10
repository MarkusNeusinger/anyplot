"""anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: altair | Python 3.13
Quality: pending | Created: 2025-12-26
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Feature importances from a hypothetical RandomForest model
np.random.seed(42)

features = [
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
]

# Realistic importance scores (sum to ~1.0 for tree-based models)
importances = np.array(
    [0.182, 0.156, 0.134, 0.098, 0.087, 0.072, 0.058, 0.051, 0.042, 0.038, 0.031, 0.022, 0.015, 0.009, 0.005]
)

# Standard deviations for ensemble variability
stds = importances * np.random.uniform(0.15, 0.35, len(importances))

df = pd.DataFrame({"feature": features, "importance": importances, "std": stds})

# Sort by importance for display
df = df.sort_values("importance", ascending=True).reset_index(drop=True)

# Create base chart
base = alt.Chart(df).encode(
    y=alt.Y("feature:N", sort=None, title="Feature", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelLimit=300)),
    x=alt.X("importance:Q", title="Importance Score", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
    tooltip=[
        alt.Tooltip("feature:N", title="Feature"),
        alt.Tooltip("importance:Q", title="Importance", format=".3f"),
        alt.Tooltip("std:Q", title="Std Dev", format=".3f"),
    ],
)

# Bars with color gradient based on importance using viridis (continuous sequential)
bars = base.mark_bar(size=30).encode(color=alt.Color("importance:Q", scale=alt.Scale(scheme="viridis"), legend=None))

# Error bars
error_bars = (
    base.mark_errorbar(color=INK_SOFT, thickness=2)
    .encode(x=alt.X("x_min:Q", title=""), x2="x_max:Q")
    .transform_calculate(x_min="datum.importance - datum.std", x_max="datum.importance + datum.std")
)

# Text labels at end of bars
text = (
    base.mark_text(align="left", baseline="middle", dx=5, fontSize=16, fontWeight="bold", color=INK)
    .encode(text=alt.Text("importance:Q", format=".3f"), x=alt.X("text_x:Q"))
    .transform_calculate(text_x="datum.importance + datum.std + 0.005")
)

# Combine layers
chart = (
    (bars + error_bars + text)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "bar-feature-importance · altair · anyplot.ai", fontSize=28, anchor="start", offset=20, color=INK
        ),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        gridColor=INK,
        gridOpacity=0.10,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save output
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
