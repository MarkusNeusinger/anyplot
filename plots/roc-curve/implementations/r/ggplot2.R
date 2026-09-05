#' anyplot.ai
#' roc-curve: ROC Curve with AUC
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)
library(scales)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data -----------------------------------------------------------------
# Diagnostic test scores for two candidate classifiers separating
# disease-positive from disease-negative patients.
n_patients <- 400
disease <- rbinom(n_patients, 1, 0.4)

score_logistic <- ifelse(disease == 1,
                          rnorm(n_patients, mean = 2.2, sd = 1.0),
                          rnorm(n_patients, mean = 0.0, sd = 1.0))
score_forest <- ifelse(disease == 1,
                        rnorm(n_patients, mean = 1.2, sd = 1.1),
                        rnorm(n_patients, mean = 0.0, sd = 1.1))

roc_points <- function(scores, labels) {
  thresholds <- sort(unique(c(scores, Inf, -Inf)), decreasing = TRUE)
  n_pos <- sum(labels == 1)
  n_neg <- sum(labels == 0)
  tpr <- sapply(thresholds, function(t) sum(scores >= t & labels == 1) / n_pos)
  fpr <- sapply(thresholds, function(t) sum(scores >= t & labels == 0) / n_neg)
  tibble::tibble(fpr = fpr, tpr = tpr)
}

trapezoid_auc <- function(fpr, tpr) {
  ord <- order(fpr)
  fpr_sorted <- fpr[ord]
  tpr_sorted <- tpr[ord]
  sum(diff(fpr_sorted) * (head(tpr_sorted, -1) + tail(tpr_sorted, -1)) / 2)
}

roc_logistic <- roc_points(score_logistic, disease)
roc_forest <- roc_points(score_forest, disease)

auc_logistic <- trapezoid_auc(roc_logistic$fpr, roc_logistic$tpr)
auc_forest <- trapezoid_auc(roc_forest$fpr, roc_forest$tpr)

label_logistic <- sprintf("Logistic Regression (AUC = %.2f)", auc_logistic)
label_forest <- sprintf("Random Forest (AUC = %.2f)", auc_forest)

roc_df <- bind_rows(
  roc_logistic %>% mutate(model = label_logistic),
  roc_forest %>% mutate(model = label_forest)
) %>%
  mutate(model = factor(model, levels = c(label_logistic, label_forest)))

# --- Plot -------------------------------------------------------------------
p <- ggplot(roc_df, aes(x = fpr, y = tpr, color = model)) +
  geom_abline(intercept = 0, slope = 1, linetype = "dashed",
              linewidth = 0.6, color = INK_SOFT) +
  geom_line(linewidth = 1.2) +
  annotate("text", x = 0.98, y = 0.90, label = "Random classifier",
           hjust = 1, size = 3, color = INK_SOFT, angle = 41) +
  scale_color_manual(values = IMPRINT_PALETTE[1:2]) +
  scale_x_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.25),
                      expand = expansion(mult = c(0.01, 0.03))) +
  scale_y_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.25),
                      expand = expansion(mult = c(0.01, 0.03))) +
  coord_fixed(ratio = 1) +
  labs(
    title = "Disease Diagnostic Test · roc-curve · r · ggplot2 · anyplot.ai",
    x = "False Positive Rate",
    y = "True Positive Rate",
    color = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background       = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background      = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y    = element_line(color = alpha(INK, 0.15), linewidth = 0.5),
    panel.grid.major.x    = element_blank(),
    panel.grid.minor      = element_blank(),
    axis.title            = element_text(color = INK, size = 10),
    axis.text              = element_text(color = INK_SOFT, size = 8),
    axis.line              = element_line(color = INK_SOFT),
    plot.title              = element_text(color = INK, size = 12),
    legend.position        = "inside",
    legend.position.inside = c(0.68, 0.14),
    legend.background      = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.text            = element_text(color = INK_SOFT, size = 8),
    legend.title            = element_blank()
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
