"""pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-14
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn theme and context
sns.set_theme(style="white", context="talk", font_scale=1.1)
python_blue = "#306998"

# Data: ARMA(1,1) process with seasonal component (airline passenger residuals)
np.random.seed(42)
n_obs = 200
ar1_coeff = 0.7
ma1_coeff = 0.4
seasonal_period = 12
seasonal_strength = 0.3
noise = np.random.randn(n_obs)
series = np.zeros(n_obs)
series[0] = noise[0]
for t in range(1, n_obs):
    seasonal = seasonal_strength * np.sin(2 * np.pi * t / seasonal_period)
    series[t] = ar1_coeff * series[t - 1] + noise[t] + ma1_coeff * noise[t - 1] + seasonal

# Compute ACF
n_lags = 35
mean = np.mean(series)
var = np.sum((series - mean) ** 2)
acf_values = np.array([np.sum((series[: n_obs - k] - mean) * (series[k:] - mean)) / var for k in range(n_lags + 1)])

# Compute PACF via Durbin-Levinson recursion
pacf_values = np.zeros(n_lags + 1)
pacf_values[0] = 1.0
pacf_values[1] = acf_values[1]
phi = np.zeros((n_lags + 1, n_lags + 1))
phi[1, 1] = acf_values[1]
for k in range(2, n_lags + 1):
    num = acf_values[k] - np.sum(phi[k - 1, 1:k] * acf_values[k - 1 : 0 : -1])
    den = 1.0 - np.sum(phi[k - 1, 1:k] * acf_values[1:k])
    phi[k, k] = num / den if den != 0 else 0
    for j in range(1, k):
        phi[k, j] = phi[k - 1, j] - phi[k, k] * phi[k - 1, k - j]
    pacf_values[k] = phi[k, k]

lags_acf = np.arange(0, n_lags + 1)
lags_pacf = np.arange(1, n_lags + 1)
conf_bound = 1.96 / np.sqrt(n_obs)

# Build unified DataFrame for seaborn FacetGrid
acf_df = pd.DataFrame({"Lag": lags_acf, "Correlation": acf_values, "Panel": "Autocorrelation (ACF)"})
pacf_df = pd.DataFrame({"Lag": lags_pacf, "Correlation": pacf_values[1:], "Panel": "Partial Autocorrelation (PACF)"})
df = pd.concat([acf_df, pacf_df], ignore_index=True)

# Classify each lag as significant or not (distinctive seaborn hue feature)
df["Significance"] = np.where(
    (df["Correlation"].abs() > conf_bound) | ((df["Panel"] == "Autocorrelation (ACF)") & (df["Lag"] == 0)),
    "Significant",
    "Within CI",
)

# Color palette for significance categories
sig_palette = {"Significant": python_blue, "Within CI": "#A8C4D8"}

# Create FacetGrid - distinctive seaborn multi-panel approach
g = sns.FacetGrid(df, row="Panel", height=4.5, aspect=3.55, sharex=True, sharey=False, margin_titles=False)


# Custom stem plot function using seaborn barplot + scatterplot
def stem_plot(data, **kwargs):
    ax = plt.gca()
    panel = data["Panel"].iloc[0]

    # Use seaborn barplot with narrow width for stems (seaborn-native visualization)
    sns.barplot(
        data=data,
        x="Lag",
        y="Correlation",
        hue="Significance",
        palette=sig_palette,
        width=0.15,
        dodge=False,
        legend=False,
        ax=ax,
    )

    # Markers via seaborn scatterplot with hue-based coloring
    sns.scatterplot(
        data=data,
        x="Lag",
        y="Correlation",
        hue="Significance",
        palette=sig_palette,
        s=90,
        zorder=5,
        edgecolor="white",
        linewidth=0.8,
        ax=ax,
        legend=False,
    )

    # Confidence interval band and lines
    ci_color = sns.color_palette("muted")[1]
    xlims = (-0.5, n_lags + 0.5)
    ax.axhline(y=0, color="#333333", linewidth=0.8)
    ax.axhline(y=conf_bound, color=ci_color, linestyle="--", linewidth=1.5, alpha=0.8)
    ax.axhline(y=-conf_bound, color=ci_color, linestyle="--", linewidth=1.5, alpha=0.8)
    ax.fill_between([xlims[0], xlims[1]], -conf_bound, conf_bound, color=ci_color, alpha=0.08)

    # Annotate first significant lag (beyond lag 0 for ACF)
    sig_data = data[data["Significance"] == "Significant"]
    if panel == "Autocorrelation (ACF)":
        sig_data = sig_data[sig_data["Lag"] > 0]
    if len(sig_data) > 0:
        first = sig_data.iloc[0]
        ax.annotate(
            f"lag {int(first['Lag'])}: {first['Correlation']:.2f}",
            xy=(first["Lag"], first["Correlation"]),
            xytext=(first["Lag"] + 5, first["Correlation"] + 0.12),
            fontsize=13,
            color=python_blue,
            fontweight="bold",
            arrowprops={"arrowstyle": "->", "color": python_blue, "lw": 1.5},
        )

    # Mark seasonal peaks in ACF
    if panel == "Autocorrelation (ACF)":
        seasonal_lags = data[(data["Lag"] == 12) | (data["Lag"] == 24)]
        for _, row in seasonal_lags.iterrows():
            if abs(row["Correlation"]) > conf_bound:
                ax.annotate(
                    f"seasonal\nlag {int(row['Lag'])}",
                    xy=(row["Lag"], row["Correlation"]),
                    xytext=(row["Lag"] + 3, row["Correlation"] + 0.15),
                    fontsize=11,
                    color="#8B4513",
                    fontstyle="italic",
                    arrowprops={"arrowstyle": "->", "color": "#8B4513", "lw": 1.2},
                )

    ax.set_xlim(xlims)
    ax.set_ylabel(panel, fontsize=20)


g.map_dataframe(stem_plot)

# Remove FacetGrid default row titles
g.set_titles("")

# Style each axis
for ax in g.axes.flat:
    ax.tick_params(axis="both", labelsize=16)
    ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
    ax.set_xlabel("")
    # Show every 5th tick label for cleaner x-axis
    tick_labels = ax.get_xticklabels()
    for i, label in enumerate(tick_labels):
        if i % 5 != 0:
            label.set_visible(False)

# Bottom axis label
g.axes[-1, 0].set_xlabel("Lag (months)", fontsize=20)

# Add significance legend using seaborn's distinctive hue legend
handles = [
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=python_blue, markersize=10, label="Significant"),
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#A8C4D8", markersize=10, label="Within CI"),
    plt.Line2D([0], [0], linestyle="--", color=sns.color_palette("muted")[1], linewidth=1.5, label="95% CI"),
]
g.axes[0, 0].legend(handles=handles, loc="upper right", fontsize=13, framealpha=0.9)

sns.despine(fig=g.figure)

g.figure.suptitle("acf-pacf · seaborn · pyplots.ai", fontsize=24, fontweight="medium", y=0.99)
g.figure.subplots_adjust(top=0.93, hspace=0.25)

# Save
g.savefig("plot.png", dpi=300, bbox_inches="tight")
