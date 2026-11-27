#' anyplot.ai
#' radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-05-29

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens — Imprint palette
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — brand green → AI & ML
  "#C475FD",  # 2 — lavender    → Cloud & Infra
  "#4467A3",  # 3 — blue        → Security
  "#BD8233"   # 4 — ochre       → Dev Tools
)

sector_names  <- c("AI & ML", "Cloud & Infra", "Security", "Dev Tools")
ring_labels_v <- c("Now", "Near-term", "Mid-term", "Future")
color_map     <- setNames(IMPRINT_PALETTE, sector_names)
sector_starts <- setNames(c(0, 67.5, 135, 202.5), sector_names)

# 16 technology items: one per (sector × ring) cell
items <- tibble::tibble(
  name = c(
    "LLM Deployment", "Agentic AI", "Foundation Models", "Neuromorphic Chips",
    "Kubernetes Automation", "FinOps Tooling", "Edge ML Platforms", "Quantum Cloud",
    "Zero-Trust Network", "AI-Powered SIEM", "Homomorphic Encryption", "Post-Quantum Crypto",
    "AI Code Assistance", "Platform Engineering", "WebAssembly", "Autonomous Testing"
  ),
  sector = rep(sector_names, each = 4),
  ring_r = rep(1:4, times = 4),
  # Angles inside each 67.5-degree sector, chosen so labels in a sector sit at distinct heights
  angle_offset = c(57, 58, 35, 38, 56, 21, 54, 57, 38, 44, 48, 38, 58, 8, 48, 58)
)

items$angle      <- sector_starts[items$sector] + items$angle_offset
items$color      <- color_map[items$sector]
# Labels run away from the centre; the Dev Tools outer item's runs inward so they stay on the canvas
items$right_side <- (sin(items$angle * pi / 180) > 0) != (items$sector == "Dev Tools" & items$ring_r == 4)
# Larger points for more-immediate rings to convey urgency/immediacy
items$point_size <- c(6.5, 5.5, 4.5, 3.5)[items$ring_r]

# Rings 1 and 3 get a subtle tinted fill (alternating)
RING_FILL    <- if (THEME == "light") "#E6E3DB" else "#232320"
theta_full   <- seq(0, 360, length.out = 301)
ring_band_df <- do.call(rbind, lapply(list(c(0.5, 1.5), c(2.5, 3.5)), function(b) {
  data.frame(
    angle = c(theta_full, rev(theta_full)),
    r     = rep(c(b[2], b[1]), each = length(theta_full)),
    grp   = as.character(b[1])
  )
}))

# Ring boundary circles
n_circ     <- 301
angles_seq <- seq(0, 360, length.out = n_circ)
circle_df  <- do.call(rbind, lapply(c(0.5, 1.5, 2.5, 3.5, 4.5), function(r) {
  data.frame(angle = angles_seq, r = r, grp = as.character(r))
}))

# Sector divider spokes: three-quarter layout, the 270-360 quadrant stays open
spoke_df <- do.call(rbind, lapply(c(0, 67.5, 135, 202.5, 270), function(a) {
  data.frame(angle = c(a, a), r = c(0.5, 4.5), grp = as.character(a))
}))

# Ring annotation labels — centred in each ring band, inside the open quadrant
ring_ann_df <- tibble::tibble(
  angle = 315,
  r     = 1:4,
  label = ring_labels_v
)

# Sector headers outside the outermost ring boundary
sector_hdr_df <- tibble::tibble(
  angle = sector_starts + 33.75,
  r     = 4.85,
  label = sector_names
)

title_str <- "radar-innovation-timeline · r · ggplot2 · anyplot.ai"
title_sz  <- max(8L, round(12 * 67 / nchar(title_str)))

p <- ggplot() +
  # Alternating ring fills (rings 1 and 3)
  geom_polygon(
    data = ring_band_df,
    aes(x = angle, y = r, group = grp),
    fill = RING_FILL, color = NA, alpha = 0.75
  ) +
  # Ring boundary circles
  geom_path(
    data = circle_df,
    aes(x = angle, y = r, group = grp),
    color = INK_SOFT, linewidth = 0.25, alpha = 0.5
  ) +
  # Sector divider spokes
  geom_path(
    data = spoke_df,
    aes(x = angle, y = r, group = grp),
    color = INK_SOFT, linewidth = 0.45, alpha = 0.6
  ) +
  # Sector header labels
  geom_text(
    data = sector_hdr_df,
    aes(x = angle, y = r, label = label),
    size = 3.6, fontface = "bold", color = INK, hjust = 0.5
  ) +
  # Ring annotation labels (ring names near the 0-degree spoke)
  geom_text(
    data = ring_ann_df,
    aes(x = angle, y = r, label = label),
    size = 3.4, color = INK_SOFT, fontface = "bold", hjust = 0.5
  ) +
  # Technology item points — larger for more-immediate rings
  geom_point(
    data = items,
    aes(x = angle, y = ring_r, color = sector, size = point_size),
    alpha = 0.95
  ) +
  scale_size_identity(guide = "none") +
  # Technology item labels (offset outward from each point)
  geom_text(
    data = items,
    aes(x = angle, y = ring_r, label = ifelse(right_side, paste0("   ", name), paste0(name, "   ")),
        hjust = ifelse(right_side, 0, 1), color = sector),
    size = 2.9, vjust = 0.5, show.legend = FALSE
  ) +
  coord_polar(theta = "x", start = 0) +
  scale_x_continuous(limits = c(0, 360), breaks = NULL, expand = c(0, 0)) +
  scale_y_continuous(limits = c(0, 5.1), breaks = NULL) +
  scale_color_manual(values = color_map) +
  labs(title = title_str, color = "Sector") +
  theme_void(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    plot.title = element_text(
      color = INK, size = title_sz, hjust = 0.5,
      margin = margin(b = 4)
    ),
    legend.position   = "inside",
    legend.position.inside = c(0.02, 0.9),
    legend.justification = c(0, 1),
    legend.direction  = "vertical",
    legend.background = element_rect(
      fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3
    ),
    legend.text     = element_text(color = INK_SOFT, size = 10),
    legend.title    = element_text(color = INK, size = 11),
    legend.key.size = unit(0.45, "cm"),
    plot.margin     = margin(10, 10, 10, 10)
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
