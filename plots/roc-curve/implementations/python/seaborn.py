""" pyplots.ai
roc-curve: ROC Curve with AUC
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


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

# Set seaborn style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot ROC curves using seaborn lineplot
sns.lineplot(x=fpr1, y=tpr1, ax=ax, linewidth=3.5, color="#306998", label=f"Random Forest (AUC = {auc1:.3f})")
sns.lineplot(x=fpr2, y=tpr2, ax=ax, linewidth=3.5, color="#FFD43B", label=f"Logistic Regression (AUC = {auc2:.3f})")
sns.lineplot(x=fpr3, y=tpr3, ax=ax, linewidth=3.5, color="#E74C3C", label=f"Decision Tree (AUC = {auc3:.3f})")

# Diagonal reference line (random classifier)
ax.plot([0, 1], [0, 1], linestyle="--", linewidth=2.5, color="#7F8C8D", label="Random Classifier (AUC = 0.500)")

# Styling
ax.set_xlabel("False Positive Rate (FPR)", fontsize=22)
ax.set_ylabel("True Positive Rate (TPR)", fontsize=22)
ax.set_title("roc-curve · seaborn · pyplots.ai", fontsize=26, fontweight="bold")
ax.tick_params(axis="both", labelsize=18)

# Set axis limits and aspect
ax.set_xlim([-0.02, 1.02])
ax.set_ylim([-0.02, 1.02])
ax.set_aspect("equal", adjustable="box")

# Legend
ax.legend(loc="lower right", fontsize=18, framealpha=0.95)

# Grid styling
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
