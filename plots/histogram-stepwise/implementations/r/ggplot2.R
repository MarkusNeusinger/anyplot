#' anyplot.ai
#' histogram-stepwise: Step Histogram
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#4467A3")

# --- Data ---------------------------------------------------------------
# Reaction times (ms) for two lighting conditions in a visual response task.
n_subjects <- 1200
bright_light  <- rnorm(n_subjects, mean = 320, sd = 45)
dim_light     <- rnorm(n_subjects, mean = 370, sd = 55)

bin_width <- 12
breaks <- seq(
  floor(min(bright_light, dim_light) / bin_width) * bin_width,
  ceiling(max(bright_light, dim_light) / bin_width) * bin_width,
  by = bin_width
)

make_steps <- function(values, condition) {
  counts <- hist(values, breaks = breaks, plot = FALSE)$counts
  tibble::tibble(
    bin_start = breaks[-length(breaks)],
    count     = counts,
    condition = condition
  )
}

steps_df <- bind_rows(
  make_steps(bright_light, "Bright light"),
  make_steps(dim_light, "Dim light")
) |>
  mutate(condition = factor(condition, levels = c("Bright light", "Dim light")))

# --- Plot ---------------------------------------------------------------
p <- ggplot(steps_df, aes(x = bin_start, y = count, color = condition)) +
  geom_step(linewidth = 1.1, direction = "hv") +
  scale_color_manual(values = IMPRINT_PALETTE) +
  labs(
    title  = "histogram-stepwise · r · ggplot2 · anyplot.ai",
    x      = "Reaction Time (ms)",
    y      = "Number of Trials",
    color  = "Condition"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.line         = element_line(color = INK_SOFT),
    plot.title        = element_text(color = INK, size = 12),
    legend.position   = "top",
    legend.title      = element_text(color = INK, size = 10),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.background = element_blank(),
    legend.key        = element_blank()
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
