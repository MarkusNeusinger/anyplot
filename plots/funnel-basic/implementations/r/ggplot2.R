#' anyplot.ai
#' funnel-basic: Basic Funnel Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 84/100 | Created: 2026-09-05
#' Repair 1: widen the funnel + add leader lines to balance canvas whitespace

library(ggplot2)
library(dplyr)
library(tibble)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Data: HR recruitment funnel ---------------------------------------------
stage_names <- c("Applications", "Screened", "Interviewed", "Offer Extended", "Hired")
value <- c(4200, 2600, 1450, 680, 340)
n <- length(stage_names)
stage <- factor(stage_names, levels = stage_names)

# Each trapezoid narrows from its own value at the top to the next stage's
# value at the bottom; the final stage is a flat-bottomed rectangle. Widened
# relative to attempt 1 so the funnel + labels use the full landscape canvas
# instead of leaving the right side empty.
half_width <- (value / value[1]) * 0.95

segments <- lapply(seq_len(n), function(i) {
  top <- half_width[i]
  bottom <- if (i < n) half_width[i + 1] else half_width[i]
  y_top <- n - i + 1
  y_bot <- n - i
  tibble(
    stage = stage[i],
    x = c(-top, top, bottom, -bottom),
    y = c(y_top, y_top, y_bot, y_bot)
  )
})
funnel_df <- bind_rows(segments)

label_x <- max(half_width) + 0.35

# Thin leader line from each trapezoid's right edge to its label block, so
# the gap between funnel and text reads as an intentional connector rather
# than dead space.
leaders_df <- tibble(
  stage = stage,
  x_start = (half_width + c(half_width[-1], half_width[n])) / 2,
  x_end = label_x - 0.06,
  y = n - seq_len(n) + 0.5
)

labels_df <- tibble(
  stage = stage,
  x = label_x,
  y_name = n - seq_len(n) + 0.62,
  y_value = n - seq_len(n) + 0.38,
  name_text = stage_names,
  value_text = sprintf("%s (%.0f%%)", format(value, big.mark = ","), value / value[1] * 100)
)

title_text <- "funnel-basic · r · ggplot2 · anyplot.ai"

# --- Plot ---------------------------------------------------------------------
p <- ggplot() +
  geom_polygon(
    data = funnel_df,
    aes(x = x, y = y, group = stage, fill = stage),
    color = PAGE_BG, linewidth = 0.6
  ) +
  geom_segment(
    data = leaders_df,
    aes(x = x_start, xend = x_end, y = y, yend = y),
    color = INK_SOFT, linewidth = 0.35, alpha = 0.6
  ) +
  geom_text(
    data = labels_df,
    aes(x = x, y = y_name, label = name_text),
    hjust = 0, size = 3.6, fontface = "bold", color = INK
  ) +
  geom_text(
    data = labels_df,
    aes(x = x, y = y_value, label = value_text),
    hjust = 0, size = 3.2, color = INK_SOFT
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE[1:n]) +
  coord_cartesian(xlim = c(-1.0, label_x + 1.05), ylim = c(0, n), expand = FALSE) +
  labs(title = title_text) +
  theme_void(base_size = 8) +
  theme(
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    plot.title = element_text(color = INK, size = 12, hjust = 0.5, margin = margin(b = 14)),
    legend.position = "none",
    plot.margin = margin(t = 18, r = 24, b = 18, l = 24)
  )

# --- Save -----------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot = p,
  device = ragg::agg_png,
  width = 8,
  height = 4.5,
  units = "in",
  dpi = 400
)
