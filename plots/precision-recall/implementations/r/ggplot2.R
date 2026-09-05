#' anyplot.ai
#' precision-recall: Precision-Recall Curve
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data ---------------------------------------------------------------
# Fraud detection: 5% of transactions are fraudulent (heavily imbalanced),
# comparing a weak baseline classifier against a tuned one.
n <- 3000
positive_rate <- 0.05
y_true <- rbinom(n, 1, positive_rate)

baseline_scores <- plogis(ifelse(y_true == 1, rnorm(n, 1.0, 1.0), rnorm(n, -1.0, 1.0)))
tuned_scores    <- plogis(ifelse(y_true == 1, rnorm(n, 2.2, 1.0), rnorm(n, -2.2, 1.0)))

scores_df <- bind_rows(
  tibble(model = "Tuned model",    y_true = y_true, y_score = tuned_scores),
  tibble(model = "Baseline model", y_true = y_true, y_score = baseline_scores)
)

# Precision/recall at every threshold, walking scores from high to low.
pr_curve <- scores_df %>%
  arrange(model, desc(y_score)) %>%
  group_by(model) %>%
  mutate(
    tp = cumsum(y_true),
    fp = cumsum(1 - y_true),
    precision = tp / (tp + fp),
    recall = tp / sum(y_true),
    recall_prev = lag(recall, default = 0)
  )

# Average precision: AP = sum_k (R_k - R_{k-1}) * P_k (sklearn convention).
ap_scores <- pr_curve %>%
  summarise(ap = sum((recall - recall_prev) * precision), .groups = "drop")

pr_curve <- pr_curve %>%
  ungroup() %>%
  left_join(ap_scores, by = "model") %>%
  mutate(model_label = sprintf("%s (AP = %.2f)", model, ap))

model_labels <- pr_curve %>%
  distinct(model, model_label) %>%
  arrange(match(model, c("Tuned model", "Baseline model")))

baseline_df <- tibble(recall = c(0, 1), precision = positive_rate)

# Iso-F1 reference curves: F1 = 2PR / (P+R) solved for P at fixed F1 levels.
f1_levels <- c(0.2, 0.4, 0.6, 0.8)
iso_f1 <- expand_grid(f1 = f1_levels, recall = seq(0.02, 1, length.out = 300)) %>%
  mutate(precision = f1 * recall / (2 * recall - f1)) %>%
  filter(precision > 0, precision <= 1)
iso_f1_labels <- iso_f1 %>%
  group_by(f1) %>%
  slice_max(recall, n = 1) %>%
  ungroup() %>%
  mutate(label = sprintf("F1=%.1f", f1))

# --- Plot ---------------------------------------------------------------
plot_title <- "Fraud Detection Model Comparison · precision-recall · r · ggplot2 · anyplot.ai"
title_fontsize <- max(8, round(12 * min(1, 67 / nchar(plot_title))))

p <- ggplot() +
  geom_line(
    data = iso_f1, aes(x = recall, y = precision, group = f1),
    color = INK_MUTED, linewidth = 0.35, linetype = "dotted", alpha = 0.6
  ) +
  geom_text(
    data = iso_f1_labels, aes(x = recall, y = precision, label = label),
    color = INK_MUTED, size = 2.6, hjust = 0, nudge_x = 0.015
  ) +
  geom_line(
    data = baseline_df, aes(x = recall, y = precision, linetype = "Baseline (random)"),
    color = INK_MUTED, linewidth = 0.7
  ) +
  geom_step(
    data = pr_curve, aes(x = recall, y = precision, color = model_label),
    linewidth = 1.1
  ) +
  scale_color_manual(values = IMPRINT_PALETTE[1:2], breaks = model_labels$model_label, name = NULL) +
  scale_linetype_manual(values = c("Baseline (random)" = "dashed"), name = NULL) +
  scale_x_continuous(expand = expansion(mult = c(0.01, 0.1))) +
  scale_y_continuous(expand = expansion(mult = c(0.02, 0.05))) +
  coord_cartesian(xlim = c(0, 1), ylim = c(0, 1), clip = "off") +
  labs(x = "Recall", y = "Precision", title = plot_title) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = alpha(INK, 0.15), linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = title_fontsize),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.background = element_blank(),
    legend.key        = element_rect(fill = PAGE_BG, color = NA),
    legend.position   = "inside",
    legend.position.inside = c(0.02, 0.05),
    legend.justification = c(0, 0)
  )

# --- Save -----------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
