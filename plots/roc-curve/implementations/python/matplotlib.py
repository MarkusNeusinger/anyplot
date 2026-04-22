""" pyplots.ai
roc-curve: ROC Curve with AUC
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Generate synthetic classification data for ROC curve
np.random.seed(42)

# Simulate three models with different performances
n_samples = 1000

# Ground truth labels
y_true = np.random.binomial(1, 0.5, n_samples)

# Model 1: Excellent classifier (AUC ~ 0.94)
y_scores_model1 = y_true * np.random.beta(5, 2, n_samples) + (1 - y_true) * np.random.beta(2, 6, n_samples)

# Model 2: Good classifier (AUC ~ 0.82)
y_scores_model2 = y_true * np.random.beta(4, 2, n_samples) + (1 - y_true) * np.random.beta(2, 4, n_samples)

# Model 3: Fair classifier (AUC ~ 0.68)
y_scores_model3 = y_true * np.random.beta(2.5, 2, n_samples) + (1 - y_true) * np.random.beta(2, 2.5, n_samples)


# Compute ROC curve from threshold sweeping
def compute_roc(y_true, y_scores, n_thresholds=200):
    thresholds = np.linspace(0, 1, n_thresholds)
    tpr_list = []
    fpr_list = []

    for thresh in thresholds:
        y_pred = (y_scores >= thresh).astype(int)
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        tn = np.sum((y_pred == 0) & (y_true == 0))

        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        tpr_list.append(tpr)
        fpr_list.append(fpr)

    return np.array(fpr_list), np.array(tpr_list)


def compute_auc(fpr, tpr):
    # Sort by FPR for proper integration
    sorted_indices = np.argsort(fpr)
    fpr_sorted = fpr[sorted_indices]
    tpr_sorted = tpr[sorted_indices]
    return np.trapezoid(tpr_sorted, fpr_sorted)


# Compute ROC curves for all models
fpr1, tpr1 = compute_roc(y_true, y_scores_model1)
auc1 = compute_auc(fpr1, tpr1)

fpr2, tpr2 = compute_roc(y_true, y_scores_model2)
auc2 = compute_auc(fpr2, tpr2)

fpr3, tpr3 = compute_roc(y_true, y_scores_model3)
auc3 = compute_auc(fpr3, tpr3)

# Create figure (16:9 landscape format)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot ROC curves - using Python colors and accessible palette
ax.plot(fpr1, tpr1, color="#306998", linewidth=3.5, label=f"Random Forest (AUC = {auc1:.2f})")
ax.plot(fpr2, tpr2, color="#FFD43B", linewidth=3.5, label=f"Logistic Regression (AUC = {auc2:.2f})")
ax.plot(fpr3, tpr3, color="#2E8B57", linewidth=3.5, label=f"Decision Tree (AUC = {auc3:.2f})")

# Diagonal reference line (random classifier)
ax.plot([0, 1], [0, 1], color="#888888", linewidth=2.5, linestyle="--", label="Random Classifier (AUC = 0.50)")

# Fill area under curves for visual emphasis
ax.fill_between(fpr1, tpr1, alpha=0.12, color="#306998")
ax.fill_between(fpr2, tpr2, alpha=0.08, color="#FFD43B")

# Styling
ax.set_xlabel("False Positive Rate", fontsize=20)
ax.set_ylabel("True Positive Rate", fontsize=20)
ax.set_title("roc-curve · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim([-0.02, 1.0])
ax.set_ylim([0.0, 1.02])
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(loc="lower right", fontsize=16, framealpha=0.95)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
