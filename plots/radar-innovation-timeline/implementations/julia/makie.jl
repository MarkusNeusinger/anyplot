# anyplot.ai
# radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-05-29

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — AI & ML (Imprint brand green, always first series)
    colorant"#C475FD",  # 2 — Cloud & Infra
    colorant"#4467A3",  # 3 — Security
    colorant"#BD8233",  # 4 — DevEx
]

# Data: Technology Radar — 24 items across 4 sectors and 4 time-horizon rings
const SECTORS = ["AI & ML", "Cloud & Infra", "Security", "DevEx"]
const RINGS   = ["Adopt", "Trial", "Assess", "Hold"]

# Ring boundaries (inner → outer radii, 4 bands)
const RING_BOUNDS  = [0.0, 0.26, 0.50, 0.74, 0.95]
const RING_CENTERS = [(RING_BOUNDS[i] + RING_BOUNDS[i+1]) / 2 for i in 1:4]

# Sector start angles in radians (counter-clockwise from positive x-axis)
# Sector 1 (AI & ML):    0°– 90°   (right quadrant)
# Sector 2 (Cloud):     90°–180°   (top quadrant)
# Sector 3 (Security): 180°–270°   (left quadrant)
# Sector 4 (DevEx):    270°–360°   (bottom quadrant)
const SECTOR_STARTS = [0.0, π/2, π, 3π/2]
const SECTOR_SPAN   = π / 2

# Each item: (label, sector_idx, ring_idx, fraction_within_sector 0→1)
const ITEMS = [
    ("LLM APIs",          1, 1, 0.28),
    ("Vector DBs",        1, 1, 0.68),
    ("RAG",               1, 2, 0.35),
    ("Fine-tuning",       1, 2, 0.72),
    ("Multimodal AI",     1, 3, 0.30),
    ("AI Agents",         1, 3, 0.65),
    ("AGI Infra",         1, 4, 0.50),
    ("Kubernetes",        2, 1, 0.28),
    ("Terraform",         2, 1, 0.65),
    ("eBPF",              2, 2, 0.38),
    ("WASM",              2, 2, 0.72),
    ("Edge Native",       2, 3, 0.45),
    ("Unikernels",        2, 4, 0.50),
    ("Zero Trust",        3, 1, 0.45),
    ("SBOM",              3, 2, 0.28),
    ("Sigstore",          3, 2, 0.72),
    ("Confidential Comp", 3, 3, 0.50),
    ("Post-Quantum",      3, 4, 0.42),
    ("GitHub Actions",    4, 1, 0.32),
    ("Dev Containers",    4, 1, 0.68),
    ("OpenTelemetry",     4, 2, 0.38),
    ("AI Code Assist",    4, 2, 0.72),
    ("Backstage",         4, 3, 0.35),
    ("DORA Metrics",      4, 3, 0.65),
]

pol2cart(r, θ) = (r * cos(θ), r * sin(θ))

# Figure — square canvas → 2400×2400 px
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    backgroundcolor = PAGE_BG,
    aspect          = DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)

# Sector fills — subtle tinted wedges, one Imprint color per sector
n_arc = 120
for i in 1:4
    θ_start = SECTOR_STARTS[i]
    θ_end   = θ_start + SECTOR_SPAN
    pts = Point2f[(0.0, 0.0)]
    for t in LinRange(θ_start, θ_end, n_arc)
        push!(pts, Point2f(pol2cart(RING_BOUNDS[5], t)...))
    end
    poly!(ax, pts; color = (IMPRINT_PALETTE[i], 0.08f0), strokewidth = 0)
end

# Ring outlines — concentric circles
n_circ = 360
for (k, r) in enumerate(RING_BOUNDS)
    r == 0.0 && continue
    θs = LinRange(0, 2π, n_circ + 1)
    xs = r .* cos.(θs)
    ys = r .* sin.(θs)
    lw = (k == length(RING_BOUNDS)) ? 1.5f0 : 0.8f0
    lines!(ax, xs, ys; color = (INK, 0.28f0), linewidth = lw)
end

# Sector dividers — radial lines at each sector boundary
for θ in SECTOR_STARTS
    x2, y2 = pol2cart(RING_BOUNDS[5], θ)
    lines!(ax, [0.0f0, Float32(x2)], [0.0f0, Float32(y2)];
           color = (INK, 0.28f0), linewidth = 1.0f0)
end

# Ring labels — placed along the 0°/360° boundary, inside each band
ring_label_θ = -0.15  # slightly into the DevEx sector for readability
for (i, ring_name) in enumerate(RINGS)
    r = RING_CENTERS[i]
    xl, yl = pol2cart(r, ring_label_θ)
    text!(ax, xl, yl; text = ring_name,
          fontsize = 9,
          color    = INK_MUTED,
          align    = (:center, :center))
end

# Sector headers — bold labels just outside the outermost ring
header_r = RING_BOUNDS[5] + 0.09
for (i, sector_name) in enumerate(SECTORS)
    θ_mid = SECTOR_STARTS[i] + SECTOR_SPAN / 2
    xl, yl = pol2cart(header_r, θ_mid)
    ha = cos(θ_mid) > 0.25 ? :left : (cos(θ_mid) < -0.25 ? :right : :center)
    va = sin(θ_mid) > 0.25 ? :bottom : (sin(θ_mid) < -0.25 ? :top : :center)
    text!(ax, xl, yl; text = sector_name,
          fontsize = 14,
          color    = IMPRINT_PALETTE[i],
          align    = (ha, va))
end

# Data points — scatter, colored by sector
for (label, sec, ring, frac) in ITEMS
    θ = SECTOR_STARTS[sec] + frac * SECTOR_SPAN
    r = RING_CENTERS[ring]
    x, y = pol2cart(r, θ)
    scatter!(ax, [x], [y];
             color       = IMPRINT_PALETTE[sec],
             markersize  = 13,
             strokewidth = 1.2f0,
             strokecolor = PAGE_BG)
end

# Item labels — offset radially outward from each point
for (label, sec, ring, frac) in ITEMS
    θ = SECTOR_STARTS[sec] + frac * SECTOR_SPAN
    r = RING_CENTERS[ring]
    x, y = pol2cart(r, θ)
    offset = 0.05
    xl = x + offset * cos(θ)
    yl = y + offset * sin(θ)
    ha = cos(θ) > 0.25 ? :left : (cos(θ) < -0.25 ? :right : :center)
    va = sin(θ) > 0.25 ? :bottom : (sin(θ) < -0.25 ? :top : :center)
    text!(ax, xl, yl; text = label,
          fontsize = 9,
          color    = INK_SOFT,
          align    = (ha, va))
end

# Axis limits — leave margin for sector headers and item labels
xlims!(ax, -1.28, 1.28)
ylims!(ax, -1.28, 1.28)

# Title
title_str      = "radar-innovation-timeline · julia · makie · anyplot.ai"
title_n        = length(title_str)
title_fontsize = title_n > 67 ? round(Int, 20 * 67 / title_n) : 20

Label(fig[0, 1], title_str;
      fontsize  = title_fontsize,
      color     = INK,
      tellwidth = false)

# Legend
legend_elems = [MarkerElement(color = IMPRINT_PALETTE[i], marker = :circle, markersize = 13)
                for i in 1:4]
Legend(fig[2, 1], legend_elems, SECTORS;
       orientation  = :horizontal,
       framevisible = false,
       labelcolor   = INK_SOFT,
       labelsize    = 11,
       tellwidth    = false)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)
