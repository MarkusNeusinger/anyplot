# anyplot.ai
# venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-25

using CairoMakie
using Colors
using Random

Random.seed!(42)

const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 brand green
    colorant"#C475FD",  # 2 lavender
    colorant"#4467A3",  # 3 blue
    colorant"#BD8233",
    colorant"#AE3030",
    colorant"#2ABCCD",
    colorant"#954477",
    colorant"#99B314",
]

# Circle geometry (data-unit coordinates, range 0–1)
const r    = 0.25f0
const CX_A = 0.50f0;  const CY_A = 0.62f0   # top: "Goes Viral"
const CX_B = 0.325f0; const CY_B = 0.40f0   # bottom-left: "Actually Works"
const CX_C = 0.675f0; const CY_C = 0.40f0   # bottom-right: "Still Around in 5 Years"

function circle_poly(cx, cy, r; n=200)
    θ = range(0, 2π, length=n + 1)
    return Point2f.(cx .+ r .* cos.(θ), cy .+ r .* sin.(θ))
end

const col_A = IMPRINT_PALETTE[1]   # green — Goes Viral
const col_B = IMPRINT_PALETTE[2]   # lavender — Actually Works
const col_C = IMPRINT_PALETTE[3]   # blue — Still Around in 5 Years

# Items: (x, y, label) — pre-distributed across the seven interior zones + outside
const items = [
    (0.50f0,  0.83f0, "NFTs"),           # A only
    (0.50f0,  0.78f0, "Metaverse"),      # A only
    (0.50f0,  0.73f0, "Clubhouse"),      # A only
    (0.155f0, 0.47f0, "PostgreSQL"),     # B only
    (0.145f0, 0.40f0, "Nginx"),          # B only
    (0.155f0, 0.33f0, "Bash"),           # B only
    (0.845f0, 0.47f0, "Email"),          # C only
    (0.855f0, 0.40f0, "Excel"),          # C only
    (0.845f0, 0.33f0, "PDF"),            # C only
    (0.385f0, 0.58f0, "ChatGPT"),        # AB
    (0.38f0,  0.53f0, "Figma"),          # AB
    (0.615f0, 0.58f0, "Agile"),          # AC
    (0.62f0,  0.53f0, "The Cloud"),      # AC
    (0.50f0,  0.35f0, "Git"),            # BC
    (0.50f0,  0.30f0, "Docker"),         # BC
    (0.50f0,  0.48f0, "JavaScript"),     # ABC
    (0.15f0,  0.10f0, "Google+"),        # outside
    (0.85f0,  0.10f0, "Vine"),           # outside
]

const title_str = "Tech Taxonomy · venn-labeled-items · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title           = title_str,
    titlesize       = 20,
    titlecolor      = INK,
    backgroundcolor = PAGE_BG,
    aspect          = DataAspect(),
)

xlims!(ax, -0.15f0, 1.15f0)
ylims!(ax, -0.15f0, 1.15f0)
hidexdecorations!(ax)
hideydecorations!(ax)
hidespines!(ax)

# Three Venn circles: semi-transparent fill + coloured outline
poly!(ax, circle_poly(CX_A, CY_A, r);
      color = (col_A, 0.18f0), strokecolor = (col_A, 0.90f0), strokewidth = 2.5f0)
poly!(ax, circle_poly(CX_B, CY_B, r);
      color = (col_B, 0.18f0), strokecolor = (col_B, 0.90f0), strokewidth = 2.5f0)
poly!(ax, circle_poly(CX_C, CY_C, r);
      color = (col_C, 0.18f0), strokecolor = (col_C, 0.90f0), strokewidth = 2.5f0)

# Category labels — outside each circle on its outer edge
text!(ax, CX_A, CY_A + r + 0.05f0;
      text = "Goes Viral", color = col_A,
      align = (:center, :bottom), fontsize = 18)
text!(ax, CX_B - r * 0.70f0 - 0.05f0, CY_B + 0.07f0;
      text = "Actually\nWorks", color = col_B,
      align = (:right, :center), fontsize = 18)
text!(ax, CX_C + r * 0.70f0 + 0.05f0, CY_C + 0.07f0;
      text = "Still Around\nin 5 Years", color = col_C,
      align = (:left, :center), fontsize = 18)

# Item labels inside zones
for (x, y, label) in items
    text!(ax, x, y; text = label, color = INK, align = (:center, :center), fontsize = 13)
end

# Separator for outside items
text!(ax, 0.50f0, 0.07f0;
      text = "— already gone —", color = INK_MUTED,
      align = (:center, :center), fontsize = 11)

save("plot-$(THEME).png", fig; px_per_unit = 2)
