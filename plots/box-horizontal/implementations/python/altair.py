""" anyplot.ai
box-horizontal: Horizontal Box Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-12
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

BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Response times by service type
np.random.seed(42)

data = []
# Create distributions with different characteristics
distributions = {
    "Database Query": (120, 40, 5),  # mean, std, n_outliers
    "API Gateway": (85, 25, 3),
    "Authentication": (45, 15, 2),
    "File Storage": (200, 60, 4),
    "Cache Lookup": (15, 8, 2),
    "Email Service": (150, 50, 3),
}

for service, (mean, std, n_outliers) in distributions.items():
    # Main distribution
    values = np.random.normal(mean, std, 50)
    values = np.clip(values, 5, None)  # No negative response times
    # Add some outliers
    outliers = np.random.uniform(mean + 3 * std, mean + 5 * std, n_outliers)
    all_values = np.concatenate([values, outliers])
    for v in all_values:
        data.append({"Service": service, "Response Time (ms)": v})

df = pd.DataFrame(data)

# Sort by median for easier comparison
medians = df.groupby("Service")["Response Time (ms)"].median().sort_values()
df["Service"] = pd.Categorical(df["Service"], categories=medians.index, ordered=True)

# Create horizontal box plot
chart = (
    alt.Chart(df)
    .mark_boxplot(
        box=alt.MarkConfig(color=BRAND),
        median=alt.MarkConfig(color=INK, size=3),
        outliers=alt.MarkConfig(color=BRAND, size=80),
        ticks=alt.MarkConfig(color=BRAND),
        rule=alt.MarkConfig(color=BRAND),
    )
    .encode(
        x=alt.X("Response Time (ms):Q", title="Response Time (ms)", scale=alt.Scale(zero=False)),
        y=alt.Y("Service:N", title="Service Type", sort=list(medians.index)),
        tooltip=["Service:N", "Response Time (ms):Q"],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("box-horizontal · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
        labelLimit=300,
    )
    .configure_title(color=INK)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .interactive()
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
