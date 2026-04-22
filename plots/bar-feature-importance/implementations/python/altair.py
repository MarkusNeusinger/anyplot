""" pyplots.ai
bar-feature-importance: Feature Importance Bar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


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
    y=alt.Y("feature:N", sort=None, title="Feature", axis=alt.Axis(labelFontSize=16, titleFontSize=20, labelLimit=300)),
    x=alt.X("importance:Q", title="Importance Score", axis=alt.Axis(labelFontSize=16, titleFontSize=20)),
    tooltip=[
        alt.Tooltip("feature:N", title="Feature"),
        alt.Tooltip("importance:Q", title="Importance", format=".3f"),
        alt.Tooltip("std:Q", title="Std Dev", format=".3f"),
    ],
)

# Bars with color gradient based on importance
bars = base.mark_bar(size=30).encode(color=alt.Color("importance:Q", scale=alt.Scale(scheme="blues"), legend=None))

# Error bars
error_bars = (
    base.mark_errorbar(color="#333333", thickness=2)
    .encode(x=alt.X("x_min:Q", title=""), x2="x_max:Q")
    .transform_calculate(x_min="datum.importance - datum.std", x_max="datum.importance + datum.std")
)

# Text labels at end of bars
text = (
    base.mark_text(align="left", baseline="middle", dx=5, fontSize=14, fontWeight="bold")
    .encode(text=alt.Text("importance:Q", format=".3f"), x=alt.X("text_x:Q"))
    .transform_calculate(text_x="datum.importance + datum.std + 0.005")
)

# Combine layers
chart = (
    (bars + error_bars + text)
    .properties(
        width=1400,
        height=800,
        title=alt.Title("bar-feature-importance · altair · pyplots.ai", fontSize=28, anchor="start", offset=20),
    )
    .configure_axis(labelFontSize=16, titleFontSize=20, gridColor="#e0e0e0", gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800 x 2700 at scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.save("plot.html")
