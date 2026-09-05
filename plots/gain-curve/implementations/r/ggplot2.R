#' anyplot.ai
#' gain-curve: Cumulative Gains Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 0/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED <- if (THEME == "light") "#6B6A63" else "#A8A79F"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
GRID_COLOR <- scales::alpha(INK, 0.15)
ANYPLOT_NEUTRAL <- INK
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data ---------------------------------------------------------------
# Churn-prevention scenario: a risk model scores customers by likelihood of
# churning; the cumulative gains curve shows how much of the actual churn
# base is captured as we contact increasing shares of the customer list,
# ranked by predicted score.
n_customers <- 2000
churn_rate <- 0.18

true_risk <- rnorm(n_customers)
noise <- rnorm(n_customers, sd = 1.35)
model_score <- true_risk + noise

churn_threshold <- quantile(true_risk, probs = 1 - churn_rate)
churned <- as.integer(true_risk >= churn_threshold)

order_idx <- order(model_score, decreasing = TRUE)
churned_sorted <- churned[order_idx]

cumulative_churners <- cumsum(churned_sorted)
total_churners <- sum(churned_sorted)

gains <- tibble::tibble(
  pct_targeted = seq_len(n_customers) / n_customers * 100,
  pct_captured = cumulative_churners / total_churners * 100,
  series = "Churn model"
)
gains <- bind_rows(
  tibble::tibble(pct_targeted = 0, pct_captured = 0, series = "Churn model"),
  gains
)
baseline <- tibble::tibble(
  pct_targeted = c(0, 100), pct_captured = c(0, 100),
  series = "Random targeting"
)
df <- bind_rows(gains, baseline)

# --- Plot -----------------------------------------------------------------
title_text <- "Churn Model · gain-curve · r · ggplot2 · anyplot.ai"

p <- ggplot(
  df,
  aes(x = pct_targeted, y = pct_captured,
      color = series, linetype = series, linewidth = series)
) +
  geom_line() +
  scale_color_manual(values = c("Churn model" = IMPRINT_PALETTE[1], "Random targeting" = ANYPLOT_NEUTRAL)) +
  scale_linetype_manual(values = c("Churn model" = "solid", "Random targeting" = "dashed")) +
  scale_linewidth_manual(values = c("Churn model" = 1.8, "Random targeting" = 1.0)) +
  scale_x_continuous(
    limits = c(0, 100), expand = c(0, 0),
    labels = scales::label_number(suffix = "%")
  ) +
  scale_y_continuous(
    limits = c(0, 100), expand = c(0, 0),
    labels = scales::label_number(suffix = "%")
  ) +
  labs(
    title = title_text,
    x = "Percentage of Customers Targeted",
    y = "Percentage of Churners Captured"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.3),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 11),
    panel.border      = element_blank(),
    legend.title      = element_blank(),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.background = element_rect(fill = ELEVATED_BG, color = NA),
    legend.position        = "inside",
    legend.position.inside = c(0.80, 0.18)
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
