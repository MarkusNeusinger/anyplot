#' anyplot.ai
#' venn-basic: Venn Diagram
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(ragg)

# --- Theme tokens ------------------------------------------------------------
THEME     <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG   <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK       <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT  <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
  "#009E73", # 1 - Python
  "#C475FD", # 2 - SQL
  "#4467A3"  # 3 - R
)

# --- Data: skill overlap across job candidates -------------------------------
python_total <- 120
sql_total    <- 95
r_total      <- 70
python_sql   <- 40
python_r     <- 25
sql_r        <- 30
all_three    <- 12

python_only     <- python_total - python_sql - python_r + all_three
sql_only        <- sql_total - python_sql - sql_r + all_three
r_only          <- r_total - python_r - sql_r + all_three
python_sql_only <- python_sql - all_three
python_r_only   <- python_r - all_three
sql_r_only      <- sql_r - all_three

circle_points <- function(cx, cy, radius, n = 200) {
  theta <- seq(0, 2 * pi, length.out = n)
  tibble::tibble(x = cx + radius * cos(theta), y = cy + radius * sin(theta))
}

radius <- 2.2
center_python <- c(0, 1.27)
center_sql    <- c(-1.10, -0.635)
center_r      <- c(1.10, -0.635)

circles <- bind_rows(
  circle_points(center_python[1], center_python[2], radius) |> mutate(set = "Python"),
  circle_points(center_sql[1], center_sql[2], radius) |> mutate(set = "SQL"),
  circle_points(center_r[1], center_r[2], radius) |> mutate(set = "R")
) |> mutate(set = factor(set, levels = c("Python", "SQL", "R")))

region_counts <- tibble::tibble(
  x = c(0, -1.9, 1.9, -0.9, 0.9, 0, 0),
  y = c(2.0, -1.35, -1.35, 0.9, 0.9, -1.15, 0.05),
  count = c(python_only, sql_only, r_only, python_sql_only, python_r_only, sql_r_only, all_three)
)

set_name_labels <- tibble::tibble(
  x = c(0, -1.9, 1.9),
  y = c(3.15, -2.0, -2.0),
  label = c(
    paste0("Python (n=", python_total, ")"),
    paste0("SQL (n=", sql_total, ")"),
    paste0("R (n=", r_total, ")")
  )
)

# --- Plot ---------------------------------------------------------------------
p <- ggplot() +
  geom_polygon(
    data = circles, aes(x = x, y = y, fill = set, group = set),
    alpha = 0.5, color = INK_SOFT, linewidth = 0.6
  ) +
  geom_text(
    data = set_name_labels, aes(x = x, y = y, label = label),
    color = INK, size = 4.6, fontface = "bold"
  ) +
  geom_text(
    data = region_counts, aes(x = x, y = y, label = count),
    color = INK, size = 5.6, fontface = "bold"
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  coord_fixed(xlim = c(-3.6, 3.6), ylim = c(-3.6, 3.6), expand = FALSE) +
  labs(title = "venn-basic · r · ggplot2 · anyplot.ai") +
  theme_void(base_size = 8) +
  theme(
    plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG),
    plot.title = element_text(
      color = INK, size = 12, hjust = 0.5, margin = margin(b = 16)
    ),
    legend.position = "none",
    plot.margin = margin(24, 24, 24, 24)
  )

# --- Save ----------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
