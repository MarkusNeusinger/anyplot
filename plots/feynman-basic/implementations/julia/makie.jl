# anyplot.ai
# feynman-basic: Feynman Diagram for Particle Interactions
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-03

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint palette — positional assignment
const FERMION_COLOR = colorant"#009E73"  # position 1 — brand green (e-, e+, μ-, μ+)
const PHOTON_COLOR  = colorant"#4467A3"  # position 3 — blue (γ, EM boson)

# Diagram: e+e- → μ+μ- via virtual photon (s-channel QED)
# Vertex positions
const v1x, v1y = 0.30, 0.50
const v2x, v2y = 0.70, 0.50

# External leg endpoints
const em_x0, em_y0   = 0.02, 0.78   # e- in  (top-left)
const ep_x0, ep_y0   = 0.02, 0.22   # e+ in  (bottom-left)
const mum_x1, mum_y1 = 0.98, 0.78   # μ- out (top-right)
const mup_x1, mup_y1 = 0.98, 0.22   # μ+ out (bottom-right)

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "feynman-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
    xticksvisible      = false,
    yticksvisible      = false,
    xticklabelsvisible = false,
    yticklabelsvisible = false,
)

xlims!(ax, -0.06, 1.06)
ylims!(ax, 0.0, 1.0)

# --- e- incoming: (em_x0, em_y0) → v1 (particle: arrow forward) ---
lines!(ax, [em_x0, v1x], [em_y0, v1y]; color = FERMION_COLOR, linewidth = 2.5)
let dx = v1x - em_x0, dy = v1y - em_y0, len = sqrt((v1x - em_x0)^2 + (v1y - em_y0)^2)
    mx = em_x0 + 0.55 * dx
    my = em_y0 + 0.55 * dy
    arrows!(ax, [mx], [my], [0.001 * dx / len], [0.001 * dy / len];
            arrowsize = 14, color = FERMION_COLOR, linewidth = 0)
end

# --- e+ incoming: (ep_x0, ep_y0) → v1 (antiparticle: arrow reversed) ---
lines!(ax, [ep_x0, v1x], [ep_y0, v1y]; color = FERMION_COLOR, linewidth = 2.5)
let dx = ep_x0 - v1x, dy = ep_y0 - v1y, len = sqrt((v1x - ep_x0)^2 + (v1y - ep_y0)^2)
    mx = ep_x0 + 0.45 * (v1x - ep_x0)
    my = ep_y0 + 0.45 * (v1y - ep_y0)
    arrows!(ax, [mx], [my], [0.001 * dx / len], [0.001 * dy / len];
            arrowsize = 14, color = FERMION_COLOR, linewidth = 0)
end

# --- μ- outgoing: v2 → (mum_x1, mum_y1) (particle: arrow forward) ---
lines!(ax, [v2x, mum_x1], [v2y, mum_y1]; color = FERMION_COLOR, linewidth = 2.5)
let dx = mum_x1 - v2x, dy = mum_y1 - v2y, len = sqrt(dx^2 + dy^2)
    mx = v2x + 0.55 * dx
    my = v2y + 0.55 * dy
    arrows!(ax, [mx], [my], [0.001 * dx / len], [0.001 * dy / len];
            arrowsize = 14, color = FERMION_COLOR, linewidth = 0)
end

# --- μ+ outgoing: v2 → (mup_x1, mup_y1) (antiparticle: arrow reversed) ---
lines!(ax, [v2x, mup_x1], [v2y, mup_y1]; color = FERMION_COLOR, linewidth = 2.5)
let dx = v2x - mup_x1, dy = v2y - mup_y1, len = sqrt((mup_x1 - v2x)^2 + (mup_y1 - v2y)^2)
    mx = v2x + 0.45 * (mup_x1 - v2x)
    my = v2y + 0.45 * (mup_y1 - v2y)
    arrows!(ax, [mx], [my], [0.001 * dx / len], [0.001 * dy / len];
            arrowsize = 14, color = FERMION_COLOR, linewidth = 0)
end

# --- Virtual photon propagator (wavy line, horizontal) ---
let t = LinRange(0.0, 1.0, 600)
    n_waves   = 9
    amplitude = 0.038
    xs = @. v1x + t * (v2x - v1x)
    ys = @. v1y + amplitude * sin(n_waves * 2π * t)
    lines!(ax, xs, ys; color = PHOTON_COLOR, linewidth = 2.5)
end

# --- Vertex dots ---
scatter!(ax, [v1x, v2x], [v1y, v2y]; color = INK, markersize = 14, strokewidth = 0)

# --- Particle labels ---
text!(ax, em_x0 - 0.01, em_y0 + 0.04;
      text = "e⁻", fontsize = 20, color = FERMION_COLOR, align = (:right, :bottom))
text!(ax, ep_x0 - 0.01, ep_y0 - 0.04;
      text = "e⁺", fontsize = 20, color = FERMION_COLOR, align = (:right, :top))
text!(ax, mum_x1 + 0.01, mum_y1 + 0.04;
      text = "μ⁻", fontsize = 20, color = FERMION_COLOR, align = (:left, :bottom))
text!(ax, mup_x1 + 0.01, mup_y1 - 0.04;
      text = "μ⁺", fontsize = 20, color = FERMION_COLOR, align = (:left, :top))
text!(ax, (v1x + v2x) / 2, v1y + 0.095;
      text = "γ* (virtual photon)", fontsize = 17, color = PHOTON_COLOR, align = (:center, :bottom))

# --- Time axis indicator ---
arrows!(ax, [0.06], [0.07], [0.13], [0.0];
        arrowsize = 10, color = INK_MUTED, linewidth = 1.5)
text!(ax, 0.125, 0.035;
      text = "time →", fontsize = 13, color = INK_MUTED, align = (:center, :top))

# --- Reaction label ---
text!(ax, 0.50, 0.94;
      text = "e⁺e⁻ → μ⁺μ⁻  (QED s-channel)", fontsize = 16, color = INK_SOFT,
      align = (:center, :top))

save("plot-$(THEME).png", fig; px_per_unit = 2)
