"""anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: single series uses position 1
BRAND = "#009E73"

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Importance score"  # role: importance
STD = "Importance std"  # role: std

# Data: replace this block with your own table, for example df = pd.read_csv("importances.csv")
np.random.seed(42)
base_importance = np.array(
    [0.18, 0.15, 0.14, 0.11, 0.09, 0.07, 0.06, 0.05, 0.04, 0.03, 0.025, 0.02, 0.015, 0.012, 0.008]
)
importance = np.clip(base_importance + np.random.uniform(-0.005, 0.005, len(base_importance)), 0.001, None)
df = pd.DataFrame(
    {
        FEATURE: [
            "age",
            "income",
            "credit_score",
            "employment_years",
            "debt_ratio",
            "num_accounts",
            "payment_history",
            "loan_amount",
            "property_value",
            "monthly_expenses",
            "education_level",
            "marital_status",
            "num_dependents",
            "savings_balance",
            "investment_portfolio",
        ],
        IMPORTANCE: importance,
        STD: importance * np.random.uniform(0.1, 0.3, len(importance)),
    }
)

# Plot: reads only df and the constants above
table = df.sort_values(IMPORTANCE, ascending=False)
reach = (table[IMPORTANCE] + table[STD]).max()
label_gap = reach * 0.04

# Opacity gradient of the brand green: weakest bars stay visible, strongest are solid
share = table[IMPORTANCE] / table[IMPORTANCE].max()
colors = [f"rgba(0, 158, 115, {0.3 + 0.7 * s})" if pd.notna(s) else "rgba(0, 158, 115, 0)" for s in share]

fig = go.Figure()
fig.add_trace(
    go.Bar(
        y=table[FEATURE],
        x=table[IMPORTANCE],
        orientation="h",
        marker=dict(color=colors, line=dict(color=BRAND, width=0.5)),
        error_x=dict(type="data", array=table[STD], color=INK_SOFT, thickness=1, width=3),
        hovertemplate="<b>%{y}</b><br>" + IMPORTANCE + ": %{x:.4f}<extra></extra>",
    )
)

# Value labels sit just past each error bar
for feat, imp, err in zip(table[FEATURE], table[IMPORTANCE], table[STD], strict=True):
    if pd.isna(imp):
        continue
    fig.add_annotation(
        x=imp + (0 if pd.isna(err) else err) + label_gap,
        y=feat,
        text=f"{imp:.3f}",
        showarrow=False,
        font=dict(size=10, color=INK_SOFT),
        xanchor="left",
    )

# Style
fig.update_layout(
    autosize=False,
    title=dict(
        text="bar-feature-importance · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text=IMPORTANCE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        range=[0, reach * 1.18],
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(tickfont=dict(size=10, color=INK_SOFT), autorange="reversed", linecolor=INK_SOFT),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=100, r=40, t=60, b=50),
    showlegend=False,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
