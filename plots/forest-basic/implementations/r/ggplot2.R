#' anyplot.ai
#' forest-basic: Meta-Analysis Forest Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette — position 1 is ALWAYS the brand green
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
BRAND <- IMPRINT_PALETTE[1]

# --- Data: RCTs of a novel antihypertensive vs. placebo on stroke risk -------
# Effect measure is an odds ratio (log-normal, inverse-variance weighted).
surname <- c("Bergstrom", "Chen", "Diaz", "Okafor", "Kowalski",
             "Nguyen", "Patel", "Silva", "Haddad", "Kim")
year <- sort(sample(2010:2023, length(surname)))
study <- paste0(surname, " (", year, ")")

sample_size <- round(runif(length(surname), 90, 640))
true_log_or <- log(0.72)
study_se <- 1.6 / sqrt(sample_size)
log_or <- rnorm(length(surname), mean = true_log_or, sd = 0.18)

studies <- tibble(
  study       = study,
  effect_size = exp(log_or),
  ci_lower    = exp(log_or - 1.96 * study_se),
  ci_upper    = exp(log_or + 1.96 * study_se),
  inv_var     = 1 / study_se^2
) %>%
  mutate(weight_pct = 100 * inv_var / sum(inv_var))

# Pooled estimate — inverse-variance fixed-effect model
pooled_log_or <- sum(log_or * studies$inv_var) / sum(studies$inv_var)
pooled_se     <- sqrt(1 / sum(studies$inv_var))
pooled_effect <- exp(pooled_log_or)
pooled_lower  <- exp(pooled_log_or - 1.96 * pooled_se)
pooled_upper  <- exp(pooled_log_or + 1.96 * pooled_se)

# Row positions: studies stacked top-down in chronological order, pooled
# estimate isolated near the bottom with a gap for the diamond + rule.
n_studies <- nrow(studies)
studies$y_pos <- rev(seq_len(n_studies))
pooled_y <- 0

whisker_cap <- 0.15
diamond_half_h <- 0.32

diamond_df <- tibble(
  x = c(pooled_lower, pooled_effect, pooled_upper, pooled_effect),
  y = c(pooled_y, pooled_y + diamond_half_h, pooled_y, pooled_y - diamond_half_h)
)

# --- Plot ---------------------------------------------------------------
p <- ggplot(studies, aes(x = effect_size, y = y_pos)) +
  geom_vline(xintercept = 1, linetype = "dashed", linewidth = 0.5, color = INK_SOFT) +
  geom_hline(yintercept = 0.55, linewidth = 0.3, color = INK_SOFT) +
  geom_segment(aes(x = ci_lower, xend = ci_upper, yend = y_pos),
               color = BRAND, linewidth = 0.9) +
  geom_segment(aes(x = ci_lower, xend = ci_lower,
                    y = y_pos - whisker_cap, yend = y_pos + whisker_cap),
               color = BRAND, linewidth = 0.9) +
  geom_segment(aes(x = ci_upper, xend = ci_upper,
                    y = y_pos - whisker_cap, yend = y_pos + whisker_cap),
               color = BRAND, linewidth = 0.9) +
  geom_point(aes(size = weight_pct), shape = 15, color = BRAND) +
  geom_segment(data = tibble(x = pooled_lower, xend = pooled_upper),
               aes(x = x, xend = xend, y = pooled_y, yend = pooled_y),
               inherit.aes = FALSE, color = BRAND, linewidth = 0.9, alpha = 0.35) +
  geom_polygon(data = diamond_df, aes(x = x, y = y),
               inherit.aes = FALSE, fill = BRAND, color = INK) +
  scale_x_log10(breaks = c(0.25, 0.5, 1, 2, 4),
                labels = scales::label_number(accuracy = 0.01)) +
  scale_y_continuous(
    breaks = c(pooled_y, studies$y_pos),
    labels = c("Pooled estimate", studies$study),
    expand = expansion(add = c(0.9, 0.9))
  ) +
  scale_size_continuous(range = c(3, 9), name = "Weight (%)") +
  labs(
    title = "forest-basic · r · ggplot2 · anyplot.ai",
    x = "Odds ratio (stroke, log scale)",
    y = NULL
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y  = element_blank(),
    panel.grid.minor.y  = element_blank(),
    panel.grid.minor.x  = element_blank(),
    panel.grid.major.x  = element_line(color = INK, linewidth = 0.2),
    axis.line.x         = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks          = element_blank(),
    axis.title.x        = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    plot.title          = element_text(color = INK, size = 12),
    legend.position      = "right",
    legend.background   = element_blank(),
    legend.text         = element_text(color = INK_SOFT, size = 8),
    legend.title        = element_text(color = INK, size = 10)
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
