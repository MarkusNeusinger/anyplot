"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, Normalize
from sklearn.datasets import make_classification
from sklearn.ensemble import GradientBoostingClassifier


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: blue and red anchors of the diverging scale (Imprint positions 3 and 5),
# with a neutral mid-grey so mid-scale dots stay visible on both page backgrounds
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_div = LinearSegmentedColormap.from_list("imprint_div", [IMPRINT_PALETTE[2], "#B4B2A8", IMPRINT_PALETTE[4]])

# Constants
TOP_FEATURES = 10  # rows shown, most important first

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature_names
SHAP = "SHAP value (impact on approval)"  # role: shap_values
FEATURE_VALUE = "Feature value (low to high)"  # role: feature_values

# Data: replace this block with your own long table, one row per sample and feature,
# for example df = pd.read_csv("shap_long.csv") with the three columns above
np.random.seed(42)
X, y = make_classification(
    n_samples=300, n_features=12, n_informative=10, n_redundant=2, n_classes=2, random_state=42, class_sep=1.5
)
feature_names = [
    "Annual Income",
    "Credit Score",
    "Employment Years",
    "Debt Ratio",
    "Savings Balance",
    "Age",
    "Loan Amount",
    "Payment History",
    "Number of Accounts",
    "Previous Defaults",
    "Revolving Credit",
    "Inquiries",
]
model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Approximate SHAP values from tree-model contributions
n_samples = 200
X_sample = X[np.random.choice(len(X), n_samples, replace=False)]
shap_values = np.zeros((n_samples, X_sample.shape[1]))
for i in range(X_sample.shape[1]):
    X_low = X_sample.copy()
    X_high = X_sample.copy()
    X_low[:, i] = np.percentile(X_sample[:, i], 10)
    X_high[:, i] = np.percentile(X_sample[:, i], 90)
    pred_low = model.predict_proba(X_low)[:, 1]
    pred_high = model.predict_proba(X_high)[:, 1]
    feat_normalized = (X_sample[:, i] - X_sample[:, i].min()) / (X_sample[:, i].max() - X_sample[:, i].min() + 1e-8)
    shap_values[:, i] = (pred_high - pred_low) * (feat_normalized - 0.5) * 2
feature_values_norm = (X_sample - X_sample.min(axis=0)) / (X_sample.max(axis=0) - X_sample.min(axis=0) + 1e-8)

df = pd.DataFrame(
    {FEATURE: np.tile(feature_names, n_samples), SHAP: shap_values.ravel(), FEATURE_VALUE: feature_values_norm.ravel()}
)

# Plot: reads only df and the constants above
order = df[SHAP].abs().groupby(df[FEATURE]).mean().sort_values(ascending=False).index[:TOP_FEATURES]
df = df[df[FEATURE].isin(order)]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.stripplot(
    data=df,
    x=SHAP,
    y=FEATURE,
    order=list(order),
    hue=FEATURE_VALUE,
    hue_norm=(0, 1),
    palette=imprint_div,
    size=4.5,
    alpha=0.75,
    jitter=0.3,
    legend=False,
    ax=ax,
)

# Zero line separating positive and negative impact
ax.axvline(x=0, color=INK_SOFT, linestyle="-", linewidth=1.2, alpha=0.7, zorder=0)

# Colorbar for the feature value scale
sm = plt.cm.ScalarMappable(cmap=imprint_div, norm=Normalize(vmin=0, vmax=1))
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label(FEATURE_VALUE, fontsize=10, rotation=270, labelpad=14, color=INK)
cbar.set_ticks([0, 1], labels=["Low", "High"])
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_title("shap-summary · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(SHAP, fontsize=10, color=INK)
ax.set_ylabel(FEATURE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.grid(True, axis="x", alpha=0.15, linestyle="-", linewidth=0.6)
sns.despine(left=True, ax=ax)

fig.subplots_adjust(left=0.2, right=0.97, top=0.9, bottom=0.14)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
