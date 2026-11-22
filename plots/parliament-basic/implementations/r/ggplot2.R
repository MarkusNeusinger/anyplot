#' anyplot.ai
#' parliament-basic: Parliament Seat Chart
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-17

library(ggplot2)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
PARTY <- "Party"  # role: group
SEATS <- "Seats"  # role: value

# Data: replace this block with your own table, for example df <- read.csv("chamber.csv", check.names = FALSE)
df <- tibble::tibble(
  !!PARTY := c("Harbor Union", "Ridgeline Front", "Cobalt Guild", "Meadow League",
               "Quarry Alliance", "Willow Assembly", "Lantern Circle"),
  !!SEATS := c(142, 118, 97, 85, 68, 62, 48)
)

# Plot: reads only df and the constants above
df[[PARTY]] <- factor(df[[PARTY]], levels = unique(df[[PARTY]]))
n_seats <- sum(df[[SEATS]])

# Concentric arcs: seats per arc grow with its radius, so spacing stays even
n_rows <- 10
radii  <- seq(1, 2.5, length.out = n_rows)
per_row <- floor(n_seats * radii / sum(radii))
short <- n_seats - sum(per_row)
per_row[n_rows - seq_len(short) + 1] <- per_row[n_rows - seq_len(short) + 1] + 1

seats <- do.call(rbind, lapply(seq_len(n_rows), function(i) {
  k <- seq_len(per_row[i])
  data.frame(angle = pi * (1 - (k - 0.5) / per_row[i]), radius = radii[i])
}))
# Left to right across all arcs, so each party fills one contiguous wedge
seats <- seats[order(-round(seats$angle, 9), seats$radius), ]
seats$party <- rep(df[[PARTY]], times = df[[SEATS]])
seats$x <- seats$radius * cos(seats$angle)
seats$y <- seats$radius * sin(seats$angle)

legend_labels <- sprintf("%s  (%d)", df[[PARTY]], df[[SEATS]])
party_colors  <- setNames(IMPRINT_PALETTE[seq_len(nrow(df))], levels(df[[PARTY]]))

p <- ggplot(seats, aes(x = x, y = y, fill = party)) +
  geom_point(shape = 21, size = 4.6, color = PAGE_BG, stroke = 0.5) +
  scale_fill_manual(values = party_colors, labels = legend_labels) +
  coord_fixed(clip = "off") +
  labs(title = "parliament-basic · r · ggplot2 · anyplot.ai",
       fill = sprintf("%s (%s)", PARTY, tolower(SEATS))) +
  guides(fill = guide_legend(override.aes = list(size = 6))) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.title        = element_blank(),
    axis.text         = element_blank(),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12, hjust = 0.5, margin = margin(b = 8)),
    plot.margin       = margin(16, 16, 16, 16),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.key        = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text       = element_text(color = INK_SOFT, size = 10),
    legend.title      = element_text(color = INK, size = 11),
    legend.position   = "right",
    legend.margin     = margin(10, 12, 10, 12)
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
