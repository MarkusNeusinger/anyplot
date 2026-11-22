#' anyplot.ai
#' logistic-regression: Logistic Regression Curve Plot
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 83/100 | Updated: 2026-11-22

library(ggplot2)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Columns: set these to your table's column names ------------------------
BIOMARKER <- "Biomarker level"  # role: x (predictor)
STATUS    <- "Status"           # role: group (binary outcome label)

# --- Data: replace this block with your own table ---------------------------
# Medical diagnostic context: biomarker level predicts disease probability
set.seed(42)
n <- 150
biomarker <- rnorm(n, mean = 5, sd = 2)
disease <- rbinom(n, size = 1, prob = 1 / (1 + exp(-(0.8 * biomarker - 2))))
df <- tibble::tibble(
  !!BIOMARKER := biomarker,
  !!STATUS    := factor(disease, levels = c(0, 1), labels = c("No Disease", "Disease"))
)

# --- Plot: reads only df and the constants above ----------------------------
status_num <- as.integer(df[[STATUS]]) - 1L
fit <- glm(status_num ~ x, family = binomial(link = "logit"),
           data = data.frame(x = df[[BIOMARKER]]))

# Smooth curve with a 95% interval built on the link scale (stays within 0..1)
x_range <- range(df[[BIOMARKER]])
curve <- data.frame(x = seq(x_range[1] - 0.5, x_range[2] + 0.5, length.out = 300))
pred <- predict(fit, newdata = curve, type = "link", se.fit = TRUE)
curve$probability <- plogis(pred$fit)
curve$ci_lower    <- plogis(pred$fit - 1.96 * pred$se.fit)
curve$ci_upper    <- plogis(pred$fit + 1.96 * pred$se.fit)

# Jitter along y only, so every point keeps its exact x value
points_df <- data.frame(
  x      = df[[BIOMARKER]],
  y      = status_num + rnorm(nrow(df), sd = 0.03),
  status = df[[STATUS]]
)

p <- ggplot() +
  geom_ribbon(data = curve, aes(x = x, ymin = ci_lower, ymax = ci_upper),
              fill = INK_SOFT, alpha = 0.18) +
  geom_hline(yintercept = 0.5, linetype = "dashed", color = INK_SOFT,
             linewidth = 0.5) +
  geom_point(data = points_df, aes(x = x, y = y, color = status),
             size = 2.5, alpha = 0.6) +
  geom_line(data = curve, aes(x = x, y = probability),
            color = INK, linewidth = 1.2) +
  scale_color_manual(values = IMPRINT_PALETTE[1:2]) +
  scale_y_continuous(limits = c(-0.1, 1.1), breaks = seq(0, 1, 0.25)) +
  labs(
    title = "logistic-regression · r · ggplot2 · anyplot.ai",
    x = BIOMARKER,
    y = "Probability",
    color = STATUS
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = alpha(INK, 0.15), linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.position   = "inside",
    legend.position.inside = c(0.12, 0.62)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
