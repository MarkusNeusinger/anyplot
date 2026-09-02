#' anyplot.ai
#' bar-feature-importance: Feature Importance Bar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-09-02

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint sequential colormap (single-polarity: brand green -> blue)
IMPRINT_SEQ_LOW  <- "#009E73"
IMPRINT_SEQ_HIGH <- "#4467A3"

# --- Data -----------------------------------------------------------------
# Feature importances from a gradient-boosting model predicting loan default
features <- c(
  "Credit Score", "Debt-to-Income Ratio", "Annual Income",
  "Loan Amount", "Employment Length", "Payment History",
  "Credit Utilization", "Number of Open Accounts", "Loan Purpose",
  "Home Ownership", "Interest Rate", "Delinquencies (2yr)",
  "Account Age", "Revolving Balance", "Inquiries (6mo)"
)

n <- length(features)
importance_raw <- sort(rexp(n, rate = 3), decreasing = TRUE)
importance <- round(importance_raw / sum(importance_raw), 4)
std <- round(importance * runif(n, 0.10, 0.30), 4)

df <- tibble::tibble(feature = features, importance = importance, std = std) |>
  arrange(importance) |>
  mutate(feature = factor(feature, levels = feature))

# --- Plot -------------------------------------------------------------------
title_text <- "bar-feature-importance · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = importance, y = feature, fill = importance)) +
  geom_col(width = 0.68) +
  geom_errorbar(
    aes(xmin = importance - std, xmax = importance + std),
    width = 0.28, color = INK_SOFT, linewidth = 0.5
  ) +
  geom_text(
    aes(x = importance + std, label = sprintf("%.3f", importance)),
    hjust = -0.25, size = 3.0, color = INK, family = "sans"
  ) +
  scale_fill_gradient(low = IMPRINT_SEQ_LOW, high = IMPRINT_SEQ_HIGH, guide = "none") +
  scale_x_continuous(
    labels = scales::number_format(accuracy = 0.01),
    expand = expansion(mult = c(0, 0.18))
  ) +
  labs(
    title = title_text,
    x = "Feature Importance",
    y = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_line(color = INK_MUTED, linewidth = 0.2),
    panel.grid.major.y = element_blank(),
    panel.grid.minor   = element_blank(),
    axis.title.x      = element_text(color = INK, size = 10, margin = margin(t = 8)),
    axis.title.y      = element_blank(),
    axis.text.x       = element_text(color = INK_SOFT, size = 8),
    axis.text.y       = element_text(color = INK_SOFT, size = 9),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, margin = margin(b = 12)),
    plot.margin       = margin(t = 14, r = 20, b = 10, l = 10)
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
