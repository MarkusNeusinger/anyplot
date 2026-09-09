#' anyplot.ai
#' waffle-basic: Basic Waffle Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 92/100 | Created: 2026-09-09

library(ggplot2)
library(patchwork)
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
dept_colors <- setNames(IMPRINT_PALETTE[seq_len(nrow(budget))], levels(budget$department))

grid_size <- 10
squares <- rep(budget$department, times = budget$share)
waffle_df <- tibble::tibble(
  department = squares,
  square_idx = seq_along(squares) - 1,
  col        = square_idx %% grid_size + 1,
  row        = grid_size - square_idx %/% grid_size
)

title_text <- "Company Budget Allocation · waffle-basic · r · ggplot2 · anyplot.ai"
title_size <- round(12 * min(1, 67 / nchar(title_text)))

# --- Waffle grid ------------------------------------------------------------
p_grid <- ggplot(waffle_df, aes(x = col, y = row, fill = department)) +
  geom_tile(color = PAGE_BG, linewidth = 0.6, width = 0.85, height = 0.85) +
  coord_equal(xlim = c(0.5, 10.5), ylim = c(0.5, 10.5), expand = FALSE) +
  scale_fill_manual(values = dept_colors, guide = "none") +
  labs(title = title_text) +
  theme_void(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    plot.title       = element_text(
      color = INK, size = title_size, hjust = 0.5,
      margin = margin(b = 20)
    ),
    plot.margin      = margin(t = 20, r = 20, b = 4, l = 20)
  )

# --- Custom legend, each row independently centered under the grid ---------
# A stock guide_legend(nrow = 2, byrow = TRUE) packs the shorter final row
# flush-left inside its grid cells; measuring each label's real rendered
# width lets every row (regardless of length) be centered as a whole block,
# with no risk of the longest label overrunning the canvas edge.
legend_font_pt <- 2.9 * .pt  # geom_text `size` (mm) -> points, matches rendered glyphs
key_w_in       <- 0.085
key_gap_in     <- 0.05
item_gap_in    <- 0.32
avail_width_in <- 6 - 2 * (20 / 72.27)  # matches p_grid's left/right plot.margin

text_width_in <- function(label) {
  grid::convertWidth(
    grid::grobWidth(grid::textGrob(label, gp = grid::gpar(fontsize = legend_font_pt))),
    "inches", valueOnly = TRUE
  )
}

legend_rows <- list(levels(budget$department)[1:3], levels(budget$department)[4:5])
build_legend_row <- function(depts, row_y) {
  labels  <- paste0(depts, " (", budget$share[match(depts, levels(budget$department))], "%)")
  item_w  <- key_w_in + key_gap_in + vapply(labels, text_width_in, numeric(1))
  row_w   <- sum(item_w) + item_gap_in * (length(depts) - 1)
  start_x <- (avail_width_in - row_w) / 2
  key_x   <- start_x + cumsum(c(0, utils::head(item_w, -1) + item_gap_in))
  data.frame(
    department = depts,
    label      = labels,
    key_x      = key_x / avail_width_in,
    text_x     = (key_x + key_w_in + key_gap_in) / avail_width_in,
    y          = row_y,
    stringsAsFactors = FALSE
  )
}
legend_df <- do.call(rbind, Map(
  build_legend_row, legend_rows, rev(seq_along(legend_rows)) - 1
))

p_legend <- ggplot(legend_df) +
  geom_point(aes(x = key_x, y = y, color = department), shape = 15, size = 4.2) +
  geom_text(aes(x = text_x, y = y, label = label), hjust = 0, color = INK_SOFT, size = 2.9) +
  scale_color_manual(values = dept_colors, guide = "none") +
  coord_cartesian(
    xlim = c(0, 1), ylim = c(-0.6, length(legend_rows) - 0.4), expand = FALSE
  ) +
  theme_void() +
  theme(plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG))

p <- (p_grid / p_legend) +
  plot_layout(heights = c(10, 1.6)) &
  theme(plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG))

# --- Save -----------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400,
  bg       = PAGE_BG
)
