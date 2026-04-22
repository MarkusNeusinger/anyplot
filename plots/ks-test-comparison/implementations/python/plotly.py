""" pyplots.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: plotly 6.5.2 | Python 3.14.3
Quality: 92/100 | Created: 2026-02-17
"""

import numpy as np
import plotly.graph_objects as go
from scipy.stats import ecdf, ks_2samp


# Data — credit scoring context with overlapping distributions
np.random.seed(42)
good_customers = np.random.beta(4, 2.5, size=200) * 100
bad_customers = np.random.beta(2, 3.5, size=200) * 100

# ECDFs via scipy
good_ecdf_result = ecdf(good_customers)
bad_ecdf_result = ecdf(bad_customers)

good_sorted = good_ecdf_result.cdf.quantiles
good_cdf = good_ecdf_result.cdf.probabilities
bad_sorted = bad_ecdf_result.cdf.quantiles
bad_cdf = bad_ecdf_result.cdf.probabilities

# K-S test
ks_stat, p_value = ks_2samp(good_customers, bad_customers)

# Find the point of maximum divergence
all_values = np.sort(np.concatenate([good_sorted, bad_sorted]))
good_cdf_at_all = good_ecdf_result.cdf.evaluate(all_values)
bad_cdf_at_all = bad_ecdf_result.cdf.evaluate(all_values)
diff = np.abs(good_cdf_at_all - bad_cdf_at_all)
max_idx = np.argmax(diff)
max_x = all_values[max_idx]
max_good_y = good_cdf_at_all[max_idx]
max_bad_y = bad_cdf_at_all[max_idx]
y_lo = min(max_good_y, max_bad_y)
y_hi = max(max_good_y, max_bad_y)

# Colors — refined palette
blue = "#306998"
orange = "#E8590C"
green = "#2B8A3E"
axis_color = "#666666"
text_dark = "#2D2D2D"
spine_color = "#CCCCCC"

# Plot
fig = go.Figure()

# Good Customers ECDF
fig.add_trace(
    go.Scatter(
        x=good_sorted,
        y=good_cdf,
        mode="lines",
        name="Good Customers",
        line={"color": blue, "width": 3, "shape": "hv"},
        hovertemplate="<b>Good Customers</b><br>Credit Score: %{x:.1f}<br>Cumulative: %{y:.3f}<extra></extra>",
    )
)

# Bad Customers ECDF
fig.add_trace(
    go.Scatter(
        x=bad_sorted,
        y=bad_cdf,
        mode="lines",
        name="Bad Customers",
        line={"color": orange, "width": 3, "shape": "hv"},
        hovertemplate="<b>Bad Customers</b><br>Credit Score: %{x:.1f}<br>Cumulative: %{y:.3f}<extra></extra>",
    )
)

# Shaded region between ECDFs at the divergence zone
region_width = 5
region_mask = (all_values >= max_x - region_width) & (all_values <= max_x + region_width)
region_x = all_values[region_mask]
region_upper = np.maximum(good_cdf_at_all[region_mask], bad_cdf_at_all[region_mask])
region_lower = np.minimum(good_cdf_at_all[region_mask], bad_cdf_at_all[region_mask])

fig.add_trace(
    go.Scatter(
        x=np.concatenate([region_x, region_x[::-1]]),
        y=np.concatenate([region_upper, region_lower[::-1]]),
        fill="toself",
        fillcolor="rgba(43,138,62,0.15)",
        line={"color": "rgba(43,138,62,0.25)", "width": 1},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Maximum divergence line with endpoint markers
fig.add_trace(
    go.Scatter(
        x=[max_x, max_x],
        y=[y_lo, y_hi],
        mode="lines+markers",
        name=f"Max Divergence (D = {ks_stat:.3f})",
        line={"color": green, "width": 3, "dash": "dash"},
        marker={"color": green, "size": 11, "symbol": "diamond", "line": {"color": "white", "width": 1.5}},
        hovertemplate=(f"<b>Max Divergence</b><br>Score: {max_x:.1f}<br>D = {ks_stat:.3f}<extra></extra>"),
    )
)

# Annotation for K-S statistic and p-value — positioned close to divergence
p_text = f"p = {p_value:.2e}" if p_value >= 0.001 else "p < 0.001"
fig.add_annotation(
    x=max_x,
    y=(y_lo + y_hi) / 2,
    text=f"<b>K-S Statistic</b><br>D = {ks_stat:.3f}<br>{p_text}",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.0,
    arrowwidth=2.5,
    arrowcolor=green,
    ax=90,
    ay=-40,
    font={"size": 18, "color": text_dark, "family": "Arial, sans-serif"},
    bordercolor=green,
    borderwidth=2,
    borderpad=10,
    bgcolor="rgba(255,255,255,0.95)",
)

# Horizontal reference lines at quartiles
for y_ref in [0.25, 0.50, 0.75]:
    fig.add_shape(
        type="line", x0=0, x1=100, y0=y_ref, y1=y_ref, line={"color": "rgba(0,0,0,0.08)", "width": 1, "dash": "dot"}
    )

# Subtle axis spines — bottom and left only
fig.add_shape(type="line", x0=0, x1=100, y0=0, y1=0, line={"color": spine_color, "width": 1.5})
fig.add_shape(type="line", x0=0, x1=0, y0=0, y1=1, line={"color": spine_color, "width": 1.5})

# Style
fig.update_layout(
    title={
        "text": (
            "ks-test-comparison · plotly · pyplots.ai"
            '<br><span style="font-size:16px;color:#888888">'
            "Good vs. Bad customers — distributions differ significantly (D = "
            f"{ks_stat:.3f}, {p_text})</span>"
        ),
        "font": {"size": 28, "color": text_dark, "family": "Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Credit Score (0–100)", "font": {"size": 22, "color": axis_color}, "standoff": 12},
        "tickfont": {"size": 18, "color": axis_color},
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "range": [-2, 102],
        "dtick": 20,
    },
    yaxis={
        "title": {"text": "Cumulative Proportion", "font": {"size": 22, "color": axis_color}, "standoff": 8},
        "tickfont": {"size": 18, "color": axis_color},
        "range": [-0.02, 1.05],
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "dtick": 0.25,
        "tickformat": ".2f",
    },
    template="plotly_white",
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.92)",
        "bordercolor": "rgba(0,0,0,0.12)",
        "borderwidth": 1,
    },
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 80, "r": 40, "t": 100, "b": 70},
    hoverlabel={"font": {"size": 16}, "bgcolor": "white", "bordercolor": "#CCCCCC"},
)

# Plotly-distinctive interactivity: unified hover with spike lines
fig.update_layout(
    hovermode="x unified",
    xaxis_spikemode="across",
    xaxis_spikesnap="cursor",
    xaxis_spikethickness=1,
    xaxis_spikecolor="rgba(0,0,0,0.15)",
    xaxis_spikedash="dot",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html(
    "plot.html",
    include_plotlyjs="cdn",
    config={"displayModeBar": True, "modeBarButtonsToAdd": ["drawline", "eraseshape"]},
)
