""" anyplot.ai
roc-curve: ROC Curve with AUC
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette - first series ALWAYS #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Set random seed for reproducibility
np.random.seed(42)

# Generate synthetic classification data for three models with different performance levels
n_samples = 1000

# True labels (binary)
y_true = np.concatenate([np.zeros(500), np.ones(500)])

# Model 1: Good classifier (AUC ~0.92)
y_scores_model1 = np.concatenate(
    [
        np.random.beta(2, 5, 500),  # Low scores for class 0
        np.random.beta(5, 2, 500),  # High scores for class 1
    ]
)

# Model 2: Moderate classifier (AUC ~0.78)
y_scores_model2 = np.concatenate([np.random.beta(2, 3, 500), np.random.beta(3, 2, 500)])

# Model 3: Weak classifier (AUC ~0.65)
y_scores_model3 = np.concatenate([np.random.beta(2, 2.5, 500), np.random.beta(2.5, 2, 500)])

# Compute ROC curves manually at various thresholds
n_thresholds = 200
thresholds = np.linspace(0, 1, n_thresholds)

# Model 1 ROC
tpr1, fpr1 = [], []
for thresh in thresholds:
    y_pred = (y_scores_model1 >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr1.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr1.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr1, tpr1 = np.array(fpr1), np.array(tpr1)

# Model 2 ROC
tpr2, fpr2 = [], []
for thresh in thresholds:
    y_pred = (y_scores_model2 >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr2.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr2.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr2, tpr2 = np.array(fpr2), np.array(tpr2)

# Model 3 ROC
tpr3, fpr3 = [], []
for thresh in thresholds:
    y_pred = (y_scores_model3 >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr3.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr3.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr3, tpr3 = np.array(fpr3), np.array(tpr3)

# Calculate AUC scores using trapezoidal rule
idx1 = np.argsort(fpr1)
auc1 = np.trapezoid(tpr1[idx1], fpr1[idx1])
idx2 = np.argsort(fpr2)
auc2 = np.trapezoid(tpr2[idx2], fpr2[idx2])
idx3 = np.argsort(fpr3)
auc3 = np.trapezoid(tpr3[idx3], fpr3[idx3])

# Configure seaborn with theme-adaptive colors and settings
sns.set_theme(
    style="whitegrid",
    palette=IMPRINT,
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.1,
        "grid.linewidth": 0.8,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
        "legend.framealpha": 0.95,
    },
)

# Create figure with theme-aware background
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Grid should be drawn before data to appear behind lines
ax.set_axisbelow(True)

# Plot ROC curves using seaborn lineplot with theme-aware palette
sns.lineplot(
    x=fpr1, y=tpr1, ax=ax, linewidth=3.5, color=IMPRINT[0], label=f"Support Vector Machine (AUC = {auc1:.3f})"
)
sns.lineplot(x=fpr2, y=tpr2, ax=ax, linewidth=3.5, color=IMPRINT[1], label=f"Random Forest (AUC = {auc2:.3f})")
sns.lineplot(x=fpr3, y=tpr3, ax=ax, linewidth=3.5, color=IMPRINT[2], label=f"Logistic Regression (AUC = {auc3:.3f})")

# Diagonal reference line (random classifier) - use neutral theme-aware color
ax.plot([0, 1], [0, 1], linestyle="--", linewidth=2.5, color=INK_SOFT, label="Random Classifier (AUC = 0.500)")

# Styling
ax.set_xlabel("False Positive Rate (FPR)", fontsize=20, color=INK)
ax.set_ylabel("True Positive Rate (TPR)", fontsize=20, color=INK)
ax.set_title("roc-curve · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Set axis limits and aspect
ax.set_xlim([-0.02, 1.02])
ax.set_ylim([-0.02, 1.02])
ax.set_aspect("equal", adjustable="box")

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

# Legend
ax.legend(loc="lower right", fontsize=16, framealpha=0.95, fancybox=False)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
