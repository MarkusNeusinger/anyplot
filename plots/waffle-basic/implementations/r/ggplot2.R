#' anyplot.ai
#' waffle-basic: Basic Waffle Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data ---------------------------------------------------------------
# Annual department budget allocation, in percentage points (sums to 100)
budget <- tibble::tibble(
  department = factor(
    c("Engineering", "Marketing", "Operations", "Sales", "R&D"),
    levels = c("Engineering", "Marketing", "Operations", "Sales", "R&D")
  ),
  share = c(32, 24, 19, 15, 10)
)

grid_size <- 10
squares <- rep(budget$department, times = budget$share)
waffle_df <- tibble::tibble(
  department = squares,
  square_idx = seq_along(squares) - 1,
  col        = square_idx %% grid_size + 1,
  row        = grid_size - square_idx %/% grid_size
)

legend_labels <- paste0(budget$department, " (", budget$share, "%)")

title_text <- "Company Budget Allocation · waffle-basic · r · ggplot2 · anyplot.ai"
title_size <- round(12 * min(1, 67 / nchar(title_text)))

# --- Plot ---------------------------------------------------------------
p <- ggplot(waffle_df, aes(x = col, y = row, fill = department)) +
  geom_tile(color = PAGE_BG, linewidth = 0.6, width = 0.85, height = 0.85) +
  coord_equal(xlim = c(0.5, 10.5), ylim = c(0.5, 10.5), expand = FALSE) +
  scale_fill_manual(values = IMPRINT_PALETTE[seq_len(nrow(budget))],
                     labels = legend_labels,
                     name   = NULL) +
  guides(fill = guide_legend(nrow = 2, byrow = TRUE)) +
  labs(title = title_text) +
  theme_void(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    plot.title       = element_text(
      color = INK, size = title_size, hjust = 0.5,
      margin = margin(b = 24)
    ),
    legend.position  = "bottom",
    legend.text      = element_text(color = INK_SOFT, size = 10),
    legend.key.size  = unit(1, "lines"),
    plot.margin      = margin(t = 20, r = 20, b = 12, l = 20)
  )

# --- Save -----------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
