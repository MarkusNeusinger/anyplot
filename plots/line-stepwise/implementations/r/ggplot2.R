#' anyplot.ai
#' line-stepwise: Step Line Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 74/100 | Created: 2026-09-05

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)
BRAND <- IMPRINT_PALETTE[1]

# --- Data -----------------------------------------------------------------
# An elevator's floor position over an extended service period: it holds a
# floor while passengers board or alight, then jumps instantly to the next
# requested floor. The value is only known at each stop and is constant in
# between.
n_stops <- 90
floor_num <- integer(n_stops)
floor_num[1] <- sample(1:12, 1)
for (i in 2:n_stops) {
  repeat {
    candidate <- sample(1:12, 1)
    if (candidate != floor_num[i - 1]) break
  }
  floor_num[i] <- candidate
}
wait_min <- round(runif(n_stops, 1, 6), 1)
elapsed_min <- cumsum(c(0, wait_min[-n_stops]))

df <- tibble::tibble(elapsed_min = elapsed_min, floor_num = floor_num)

# Call out the single largest floor change: this is the moment the elevator
# travels farthest in one hop, giving the plot a focal point beyond the raw
# step shape.
floor_diff <- diff(floor_num)
jump_idx <- which.max(abs(floor_diff))
jump_size <- floor_diff[jump_idx]
jump_x <- elapsed_min[jump_idx + 1]
jump_y <- floor_num[jump_idx + 1]

# --- Plot -------------------------------------------------------------------
title_text <- "Elevator Floor Position · line-stepwise · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = elapsed_min, y = floor_num)) +
  geom_step(color = BRAND, linewidth = 1.1, direction = "hv") +
  geom_point(color = BRAND, size = 2.2, alpha = 0.9) +
  geom_vline(xintercept = jump_x, color = INK_SOFT, linetype = "dashed", linewidth = 0.4) +
  geom_point(
    data = data.frame(x = jump_x, y = jump_y),
    mapping = aes(x = x, y = y),
    shape = 21, size = 4.5, fill = BRAND, color = PAGE_BG, stroke = 1.2,
    inherit.aes = FALSE
  ) +
  scale_y_continuous(breaks = breaks_width(2)) +
  labs(
    title = title_text,
    x = "Elapsed Time (minutes)",
    y = "Floor",
    caption = sprintf(
      "Largest single change: %+d floors at %.0f min elapsed",
      jump_size, jump_x
    )
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    axis.title = element_text(color = INK, size = 10),
    axis.text = element_text(color = INK_SOFT, size = 8),
    axis.line = element_line(color = INK_SOFT),
    axis.ticks = element_blank(),
    plot.title = element_text(color = INK, size = 12),
    plot.caption = element_text(color = INK_SOFT, size = 7, hjust = 0),
    panel.border = element_blank()
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot = p,
  device = ragg::agg_png,
  width = 8,
  height = 4.5,
  units = "in",
  dpi = 400
)
