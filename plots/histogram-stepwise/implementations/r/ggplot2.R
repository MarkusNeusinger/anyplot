#' anyplot.ai
#' histogram-stepwise: Step Histogram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-09-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD")

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

bright_counts <- hist(bright_light, breaks = breaks, plot = FALSE)$counts
dim_counts    <- hist(dim_light, breaks = breaks, plot = FALSE)$counts

steps_df <- bind_rows(
  tibble::tibble(
    bin_start = breaks[-length(breaks)],
    count     = bright_counts,
    condition = "Bright light"
  ),
  tibble::tibble(
    bin_start = breaks[-length(breaks)],
    count     = dim_counts,
    condition = "Dim light"
  )
) |>
  mutate(condition = factor(condition, levels = c("Bright light", "Dim light")))

mean_bright <- mean(bright_light)
mean_dim    <- mean(dim_light)
gap_label   <- sprintf("+%.0f ms slower under dim light", mean_dim - mean_bright)

# --- Plot ---------------------------------------------------------------
p <- ggplot(steps_df, aes(x = bin_start, y = count, color = condition)) +
  geom_vline(xintercept = mean_bright, color = IMPRINT_PALETTE[1], linetype = "dashed", linewidth = 0.5, alpha = 0.6) +
  geom_vline(xintercept = mean_dim, color = IMPRINT_PALETTE[2], linetype = "dashed", linewidth = 0.5, alpha = 0.6) +
  geom_step(linewidth = 1.1, direction = "hv") +
  annotate(
    "text",
    x     = (mean_bright + mean_dim) / 2,
    y     = max(steps_df$count) * 1.12,
    label = gap_label,
    color = INK_SOFT,
    size  = 3,
    hjust = 0.5
  ) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.18))) +
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
