""" pyplots.ai
roc-curve: ROC Curve with AUC
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate synthetic classification scores and compute ROC curve
np.random.seed(42)
n_samples = 500
n_thresholds = 200

# Simulate two models with different performance levels
# Model 1 (Good): higher separation between classes
y_true = np.concatenate([np.zeros(n_samples // 2), np.ones(n_samples // 2)])
scores_model1 = np.where(
    y_true == 1,
    np.random.beta(5, 2, n_samples),  # Positive class scores shifted higher
    np.random.beta(2, 5, n_samples),  # Negative class scores shifted lower
)

# Model 2 (Moderate): less separation
scores_model2 = np.where(y_true == 1, np.random.beta(3, 2, n_samples), np.random.beta(2, 3, n_samples))

# Compute ROC curve for Model 1
thresholds = np.linspace(0, 1, n_thresholds)
tpr1_list, fpr1_list = [], []
for thresh in thresholds:
    y_pred = (scores_model1 >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr1_list.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr1_list.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr1 = np.array(fpr1_list)
tpr1 = np.array(tpr1_list)

# Compute ROC curve for Model 2
tpr2_list, fpr2_list = [], []
for thresh in thresholds:
    y_pred = (scores_model2 >= thresh).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    tpr2_list.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
    fpr2_list.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
fpr2 = np.array(fpr2_list)
tpr2 = np.array(tpr2_list)

# Compute AUC using trapezoidal rule
auc1 = -np.trapezoid(tpr1, fpr1)
auc2 = -np.trapezoid(tpr2, fpr2)

# Create labels for legend
label1 = f"Good Model (AUC = {auc1:.2f})"
label2 = f"Moderate Model (AUC = {auc2:.2f})"
label_random = "Random (AUC = 0.50)"

# Create DataFrames for Altair
df_model1 = pd.DataFrame({"fpr": fpr1, "tpr": tpr1, "Model": label1})
df_model2 = pd.DataFrame({"fpr": fpr2, "tpr": tpr2, "Model": label2})
df_roc = pd.concat([df_model1, df_model2], ignore_index=True)

# Diagonal reference line (random classifier)
df_diagonal = pd.DataFrame({"fpr": [0, 1], "tpr": [0, 1], "Model": label_random})

# Create ROC curves
roc_lines = (
    alt.Chart(df_roc)
    .mark_line(strokeWidth=4)
    .encode(
        x=alt.X("fpr:Q", title="False Positive Rate", scale=alt.Scale(domain=[0, 1])),
        y=alt.Y("tpr:Q", title="True Positive Rate", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color(
            "Model:N",
            scale=alt.Scale(domain=[label1, label2, label_random], range=["#306998", "#FFD43B", "#888888"]),
            legend=alt.Legend(
                orient="none",
                legendX=930,
                legendY=1150,
                direction="vertical",
                titleFontSize=20,
                labelFontSize=18,
                symbolStrokeWidth=4,
                symbolSize=400,
                labelLimit=400,
            ),
        ),
    )
)

# Diagonal reference line
diagonal_line = (
    alt.Chart(df_diagonal)
    .mark_line(strokeWidth=3, strokeDash=[8, 6])
    .encode(
        x="fpr:Q",
        y="tpr:Q",
        color=alt.Color(
            "Model:N", scale=alt.Scale(domain=[label1, label2, label_random], range=["#306998", "#FFD43B", "#888888"])
        ),
    )
)

# Combine charts
chart = (
    (roc_lines + diagonal_line)
    .properties(width=1400, height=1400, title="roc-curve · altair · pyplots.ai")
    .configure_title(fontSize=32, anchor="middle", fontWeight="bold")
    .configure_axis(
        labelFontSize=18, titleFontSize=22, titlePadding=15, labelPadding=10, gridOpacity=0.3, gridDash=[4, 4]
    )
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=2.5)
chart.save("plot.html")
