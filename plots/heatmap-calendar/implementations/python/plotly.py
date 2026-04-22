""" pyplots.ai
heatmap-calendar: Basic Calendar Heatmap
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - GitHub-style activity over one year
np.random.seed(42)
start_date = pd.Timestamp("2024-01-01")
end_date = pd.Timestamp("2024-12-31")
dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Generate realistic activity data with weekly patterns and occasional bursts
base_activity = np.random.poisson(lam=3, size=len(dates))
# Add weekend effect (less activity)
weekend_mask = dates.dayofweek >= 5
base_activity[weekend_mask] = np.random.poisson(lam=1, size=weekend_mask.sum())
# Add some burst days
burst_days = np.random.choice(len(dates), size=20, replace=False)
base_activity[burst_days] = np.random.randint(10, 20, size=20)
# Add some zero days
zero_days = np.random.choice(len(dates), size=50, replace=False)
base_activity[zero_days] = 0

df = pd.DataFrame({"date": dates, "value": base_activity})

# Extract calendar components
df["week"] = df["date"].dt.isocalendar().week
df["dayofweek"] = df["date"].dt.dayofweek
df["month"] = df["date"].dt.month
df["year"] = df["date"].dt.year

# Handle week numbering at year boundary
df["week_of_year"] = (df["date"] - start_date).dt.days // 7

# Create the heatmap matrix (7 rows for days, 53 columns for weeks)
n_weeks = df["week_of_year"].max() + 1
heatmap_data = np.full((7, n_weeks), np.nan)

for _, row in df.iterrows():
    heatmap_data[row["dayofweek"], row["week_of_year"]] = row["value"]

# Day labels
day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Month labels and positions
month_starts = df.groupby("month")["week_of_year"].min()
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Create figure
fig = go.Figure()

# Add heatmap with GitHub-style green colorscale
fig.add_trace(
    go.Heatmap(
        z=heatmap_data,
        x=list(range(n_weeks)),
        y=day_labels,
        colorscale=[
            [0, "#ebedf0"],  # Empty/zero
            [0.25, "#9be9a8"],  # Light green
            [0.5, "#40c463"],  # Medium green
            [0.75, "#30a14e"],  # Dark green
            [1, "#216e39"],  # Darkest green
        ],
        showscale=True,
        colorbar={
            "title": {"text": "Contributions", "font": {"size": 20}},
            "tickfont": {"size": 16},
            "thickness": 25,
            "len": 0.6,
        },
        hoverongaps=False,
        hovertemplate="Week %{x}<br>%{y}<br>Value: %{z}<extra></extra>",
        xgap=3,
        ygap=3,
    )
)

# Update layout
fig.update_layout(
    title={
        "text": "GitHub Activity 2024 · heatmap-calendar · plotly · pyplots.ai",
        "font": {"size": 32},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "", "font": {"size": 22}},
        "tickmode": "array",
        "tickvals": list(month_starts.values),
        "ticktext": month_labels,
        "tickfont": {"size": 18},
        "side": "top",
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "autorange": "reversed",
        "showgrid": False,
    },
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 80, "r": 120, "t": 120, "b": 60},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
