#' anyplot.ai
#' lift-curve: Model Lift Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 79/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_LINE   <- scales::alpha(INK, 0.15)
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data: fraud detection model scores -------------------------------------
n_transactions <- 4000
fraud_rate <- 0.06

is_fraud <- rbinom(n_transactions, 1, fraud_rate)
fraud_score <- rbeta(n_transactions, 6, 2)
legit_score <- rbeta(n_transactions, 2, 6)
model_score <- ifelse(is_fraud == 1, fraud_score, legit_score)

transactions <- tibble::tibble(is_fraud = is_fraud, model_score = model_score) %>%
  arrange(desc(model_score)) %>%
  mutate(
    rank = row_number(),
    pct_targeted = rank / n() * 100,
    cum_capture_rate = cumsum(is_fraud) / rank,
    lift = cum_capture_rate / mean(is_fraud)
  )

decile_marks <- transactions %>%
  filter(rank %in% round(n() * seq(0.1, 1.0, by = 0.1)))

callouts <- decile_marks %>%
  filter(rank %in% round(n_transactions * c(0.1, 0.5))) %>%
  mutate(label = sprintf("%.1fx @ %d%%", lift, round(pct_targeted)))

# --- Plot ---------------------------------------------------------------
p <- ggplot(transactions, aes(x = pct_targeted, y = lift)) +
  geom_hline(aes(yintercept = 1, color = "Random baseline"),
             linetype = "dashed", linewidth = 0.8) +
  geom_line(aes(color = "Model"), linewidth = 1.2) +
  geom_point(data = decile_marks, color = IMPRINT_PALETTE[1], size = 3) +
  geom_text(
    data = callouts, aes(label = label),
    color = INK, size = 3.2, fontface = "bold",
    nudge_y = 1, hjust = 0
  ) +
  scale_color_manual(
    name   = NULL,
    values = c("Model" = IMPRINT_PALETTE[1], "Random baseline" = INK_SOFT)
  ) +
  scale_x_continuous(labels = scales::label_percent(scale = 1)) +
  labs(
    title = "Fraud Detection Model · lift-curve · r · ggplot2 · anyplot.ai",
    x = "Population Targeted",
    y = "Cumulative Lift"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = GRID_LINE, linewidth = 0.3),
    panel.grid.major.x = element_blank(),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK,      size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK,      size = 12),
    legend.position   = "inside",
    legend.position.inside = c(0.98, 0.98),
    legend.justification = c(1, 1),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.key        = element_blank(),
    legend.text       = element_text(color = INK_SOFT, size = 8)
  )

# --- Save ---------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
