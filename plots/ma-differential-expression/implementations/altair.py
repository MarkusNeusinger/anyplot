"""pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated RNA-seq differential expression results
np.random.seed(42)
n_genes = 15000

mean_expression = np.concatenate(
    [
        np.random.exponential(3, n_genes // 3),
        np.random.uniform(0.5, 12, n_genes // 3),
        np.random.normal(6, 2.5, n_genes - 2 * (n_genes // 3)),
    ]
)
mean_expression = np.clip(mean_expression, 0.1, 16)

log_fold_change = np.random.normal(0, 0.4, n_genes)
n_up = 400
n_down = 350
up_idx = np.random.choice(n_genes, n_up, replace=False)
remaining = np.setdiff1d(np.arange(n_genes), up_idx)
down_idx = np.random.choice(remaining, n_down, replace=False)
log_fold_change[up_idx] = np.random.uniform(1.0, 4.5, n_up)
log_fold_change[down_idx] = np.random.uniform(-4.5, -1.0, n_down)

significant = np.zeros(n_genes, dtype=bool)
significant[up_idx] = True
significant[down_idx] = True

gene_names = [f"Gene{i}" for i in range(n_genes)]

# Select top genes spread across expression range for labeling
top_up_sorted = up_idx[np.argsort(-log_fold_change[up_idx])]
top_down_sorted = down_idx[np.argsort(log_fold_change[down_idx])]
up_names = ["BRCA1", "MYC", "EGFR"]
down_names = ["PTEN", "RB1", "KRAS"]
label_idx = np.concatenate([top_up_sorted[:3], top_down_sorted[:3]])
example_names = up_names + down_names
for i, idx in enumerate(label_idx):
    gene_names[idx] = example_names[i]

df = pd.DataFrame(
    {
        "mean_expression": mean_expression,
        "log_fold_change": log_fold_change,
        "significant": significant,
        "gene_name": gene_names,
    }
)
df["status"] = np.where(
    ~df["significant"], "Not significant", np.where(df["log_fold_change"] > 0, "Upregulated", "Downregulated")
)
df_labels = df.loc[df["gene_name"].isin(example_names)].copy()
df_labels = df_labels.sort_values("mean_expression").reset_index(drop=True)
df_labels["label_x"] = df_labels["mean_expression"].values
df_labels["label_y"] = df_labels["log_fold_change"].values
for i in range(1, len(df_labels)):
    if abs(df_labels.loc[i, "label_x"] - df_labels.loc[i - 1, "label_x"]) < 1.5:
        if abs(df_labels.loc[i, "label_y"] - df_labels.loc[i - 1, "label_y"]) < 0.8:
            df_labels.loc[i, "label_y"] += 0.5 * (1 if df_labels.loc[i, "log_fold_change"] > 0 else -1)

# Separate non-significant and significant for layering with different sizes/opacity
df_nonsig = df[~df["significant"]].copy()
df_sig = df[df["significant"]].copy()

# X and Y axis definitions (shared)
x_axis = alt.X(
    "mean_expression:Q",
    title="Mean Expression (A)",
    axis=alt.Axis(labelFontSize=18, titleFontSize=22, titleColor="#333333", labelColor="#555555", domain=False),
)
y_axis = alt.Y(
    "log_fold_change:Q",
    title="Log₂ Fold Change (M)",
    axis=alt.Axis(labelFontSize=18, titleFontSize=22, titleColor="#333333", labelColor="#555555", domain=False),
)

# Non-significant points (small, faint gray)
points_nonsig = (
    alt.Chart(df_nonsig)
    .mark_point(filled=True, size=20, opacity=0.25, strokeWidth=0, color="#CCCCCC")
    .encode(
        x=x_axis,
        y=y_axis,
        tooltip=[
            alt.Tooltip("gene_name:N", title="Gene"),
            alt.Tooltip("mean_expression:Q", title="Mean Expr", format=".2f"),
            alt.Tooltip("log_fold_change:Q", title="Log₂ FC", format=".2f"),
        ],
    )
)

# Significant points (larger, vivid colors)
color_scale = alt.Scale(domain=["Upregulated", "Downregulated"], range=["#D7263D", "#306998"])
points_sig = (
    alt.Chart(df_sig)
    .mark_point(filled=True, size=60, opacity=0.7, stroke="white", strokeWidth=0.5)
    .encode(
        x=alt.X("mean_expression:Q"),
        y=alt.Y("log_fold_change:Q"),
        color=alt.Color(
            "status:N",
            scale=color_scale,
            legend=alt.Legend(title="Status", titleFontSize=18, labelFontSize=16, symbolSize=200, orient="top-right"),
        ),
        tooltip=[
            alt.Tooltip("gene_name:N", title="Gene"),
            alt.Tooltip("mean_expression:Q", title="Mean Expr", format=".2f"),
            alt.Tooltip("log_fold_change:Q", title="Log₂ FC", format=".2f"),
        ],
    )
)

# Reference lines
zero_line = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#333333", strokeWidth=1.5, opacity=0.6).encode(y="y:Q")

fc_thresholds = (
    alt.Chart(pd.DataFrame({"y": [-1, 1]}))
    .mark_rule(color="#777777", strokeWidth=2, strokeDash=[8, 6], opacity=0.6)
    .encode(y="y:Q")
)

# LOESS smoothing curve
loess_line = (
    alt.Chart(df)
    .transform_loess("mean_expression", "log_fold_change", bandwidth=0.3)
    .mark_line(color="#D4770B", strokeWidth=2.5, opacity=0.7)
    .encode(x="mean_expression:Q", y="log_fold_change:Q")
)

# Gene labels for top DE genes
labels = (
    alt.Chart(df_labels)
    .mark_text(fontSize=16, fontStyle="italic", fontWeight="bold", color="#222222", dy=-14, align="center")
    .encode(x="label_x:Q", y="label_y:Q", text="gene_name:N")
)

# Compose chart
chart = (
    (zero_line + fc_thresholds + points_nonsig + points_sig + loess_line + labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "ma-differential-expression · altair · pyplots.ai",
            fontSize=28,
            color="#222222",
            subtitle="RNA-seq differential expression: upregulated (red) and downregulated (blue) genes",
            subtitleFontSize=17,
            subtitleColor="#777777",
            subtitlePadding=6,
        ),
    )
    .configure_axis(
        labelFontSize=18, titleFontSize=22, titlePadding=12, grid=True, gridOpacity=0.15, gridColor="#cccccc"
    )
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
