#' anyplot.ai
#' violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-18

library(ggplot2)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
TASK      <- "Task type"           # role: category
EXPERTISE <- "Expertise level"     # role: group
RESPONSE  <- "Response time (ms)"  # role: value

# Data: replace this block with your own table, for example df <- read.csv("times.csv", check.names = FALSE)
set.seed(42)
n_per_group <- 50
cells <- expand.grid(
  group    = c("Junior", "Senior"),
  category = c("Data Entry", "Analysis", "Decision-Making"),
  stringsAsFactors = FALSE
)
cells$mean <- c(800, 520, 1500, 975, 2200, 1430)
cells$sd   <- c(200, 150, 300, 225, 350, 262.5)
df <- tibble::tibble(
  !!TASK      := rep(cells$category, each = n_per_group),
  !!EXPERTISE := rep(cells$group, each = n_per_group),
  !!RESPONSE  := pmax(100, rnorm(nrow(cells) * n_per_group,
                                 mean = rep(cells$mean, each = n_per_group),
                                 sd   = rep(cells$sd, each = n_per_group)))
)

# Plot: reads only df and the constants above
df[[TASK]]      <- factor(df[[TASK]], levels = unique(df[[TASK]]))
df[[EXPERTISE]] <- factor(df[[EXPERTISE]], levels = unique(df[[EXPERTISE]]))

# Swarm layout: sideways offsets within each category-group cell (layout only,
# values stay on the value axis). Points in the same value bin spread out evenly.
n_groups   <- nlevels(df[[EXPERTISE]])
dodge      <- 0.8
slot       <- dodge / n_groups
y_range    <- diff(range(df[[RESPONSE]]))
bin_height <- y_range / 45
step       <- slot * 0.075
swarm_x    <- numeric(nrow(df))
cell_id    <- interaction(df[[TASK]], df[[EXPERTISE]], drop = TRUE)
for (cell in levels(cell_id)) {
  rows   <- which(cell_id == cell)
  bins   <- floor(df[[RESPONSE]][rows] / bin_height)
  offset <- numeric(length(rows))
  for (b in unique(bins)) {
    members <- which(bins == b)
    k <- length(members)
    offset[members] <- (seq_len(k) - (k + 1) / 2) * step
  }
  g <- as.integer(df[[EXPERTISE]][rows[1]])
  swarm_x[rows] <- as.integer(df[[TASK]][rows[1]]) + (g - (n_groups + 1) / 2) * slot + offset
}
df$swarm_x <- swarm_x

p <- ggplot(df, aes(fill = .data[[EXPERTISE]], color = .data[[EXPERTISE]])) +
  geom_violin(
    aes(x = .data[[TASK]], y = .data[[RESPONSE]]),
    alpha = 0.4,
    linewidth = 0.4,
    width = slot * 0.95,
    position = position_dodge(width = dodge)
  ) +
  geom_point(
    aes(x = swarm_x, y = .data[[RESPONSE]]),
    size = 0.9,
    alpha = 0.85,
    shape = 16
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  labs(
    title = "violin-grouped-swarm · r · ggplot2 · anyplot.ai",
    x = TASK,
    y = RESPONSE,
    fill = EXPERTISE,
    color = EXPERTISE
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK, linewidth = 0.1),
    panel.grid.minor  = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12),
    legend.background = element_rect(fill = PAGE_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    legend.position   = "top"
  )

# Save
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
