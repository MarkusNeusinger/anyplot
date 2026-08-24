# anyplot.ai
# line-stress-strain: Engineering Stress-Strain Curve
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-08-24

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome") ---
const THEME     = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK       = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT  = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint categorical palette — first series always brand green
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const BRAND = IMPRINT_PALETTE[1]
const ANYPLOT_AMBER = colorant"#DDCC77"

# --- Data: mild steel tensile test -------------------------------------------
elastic_modulus   = 200_000.0  # MPa (Young's modulus, mild steel)
yield_stress      = 250.0      # MPa (upper yield point)
yield_strain      = yield_stress / elastic_modulus
luders_end_strain = 0.02       # end of the Luders (yield) plateau
uts_strain        = 0.18
uts_stress        = 420.0      # MPa
fracture_strain   = 0.28
fracture_stress   = 330.0      # MPa

n_elastic = 20
elastic_strain = collect(range(0.0, yield_strain; length=n_elastic))
elastic_stress = elastic_modulus .* elastic_strain

n_luders = 40
luders_strain = collect(range(yield_strain, luders_end_strain; length=n_luders))
luders_serration = (rand(n_luders) .- 0.5) .* 6.0
luders_stress = fill(yield_stress, n_luders) .+ luders_serration
luders_stress[1] = yield_stress
luders_stress[end] = yield_stress

n_hardening = 100
hardening_strain = collect(range(luders_end_strain, uts_strain; length=n_hardening))
hardening_progress = (hardening_strain .- luders_end_strain) ./ (uts_strain - luders_end_strain)
hardening_stress = yield_stress .+ (uts_stress - yield_stress) .* hardening_progress .^ 0.55

n_necking = 50
necking_strain = collect(range(uts_strain, fracture_strain; length=n_necking))
necking_progress = (necking_strain .- uts_strain) ./ (fracture_strain - uts_strain)
necking_stress = uts_stress .- (uts_stress - fracture_stress) .* necking_progress .^ 1.4

strain = vcat(elastic_strain, luders_strain[2:end], hardening_strain[2:end], necking_strain[2:end])
stress = vcat(elastic_stress, luders_stress[2:end], hardening_stress[2:end], necking_stress[2:end])

# 0.2% offset construction line — parallel to the elastic slope, shifted by 0.002 strain
offset = 0.002
offset_strain_end = offset + (yield_stress * 1.15) / elastic_modulus
offset_line_strain = [offset, offset_strain_end]
offset_line_stress = elastic_modulus .* (offset_line_strain .- offset)
yield_point_strain = offset + yield_stress / elastic_modulus
yield_point_stress = yield_stress

# --- Title (scale fontsize to length; 67-char baseline) -----------------------
title_str = "Mild Steel Tensile Test · line-stress-strain · julia · makie · anyplot.ai"
title_ratio = length(title_str) > 67 ? 67 / length(title_str) : 1.0
title_fontsize = round(Int, 20 * title_ratio)

# --- Plot ----------------------------------------------------------------------
fig = Figure(size=(1600, 900), fontsize=14, backgroundcolor=PAGE_BG)

ax = Axis(
    fig[1, 1];
    title = title_str,
    titlesize = title_fontsize,
    titlecolor = INK,
    xlabel = "Engineering Strain",
    ylabel = "Engineering Stress (MPa)",
    xlabelsize = 16,
    ylabelsize = 16,
    xlabelcolor = INK,
    ylabelcolor = INK,
    xticklabelsize = 13,
    yticklabelsize = 13,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    xtickcolor = INK_SOFT,
    ytickcolor = INK_SOFT,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinecolor = INK_SOFT,
    bottomspinecolor = INK_SOFT,
    xgridvisible = false,
    ygridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    yminorgridvisible = false,
)

xlims!(ax, -0.01, fracture_strain * 1.1)
ylims!(ax, 0, uts_stress * 1.28)

# Region bands — loading (elastic + strain hardening, brand tint) vs.
# necking (semantic red tint, foreshadowing fracture). The elastic segment
# is too narrow in strain to shade on its own (it is a near-vertical rise),
# so it is called out with the "Elastic" text label below instead.
vspan!(ax, 0.0, uts_strain; color=(IMPRINT_PALETTE[1], 0.05))
vspan!(ax, uts_strain, fracture_strain; color=(IMPRINT_PALETTE[5], 0.06))

label_y = uts_stress * 1.2
text!(ax, yield_strain + 0.008, label_y; text="Elastic",
      color=INK_MUTED, fontsize=14, align=(:left, :center))
text!(ax, (luders_end_strain + uts_strain) / 2, label_y; text="Plastic (strain hardening)",
      color=INK_MUTED, fontsize=14, align=(:center, :center))
text!(ax, (uts_strain + fracture_strain) / 2, label_y; text="Necking",
      color=INK_MUTED, fontsize=14, align=(:center, :center))

# 0.2% offset construction line
lines!(ax, offset_line_strain, offset_line_stress; color=INK_SOFT, linewidth=2, linestyle=:dash)
text!(ax, offset_strain_end + 0.003, offset_line_stress[end]; text="0.2% offset\nconstruction line",
      color=INK_SOFT, fontsize=13, align=(:left, :center))

# Stress-strain curve — first (and only) series, always Imprint position 1
lines!(ax, strain, stress; color=BRAND, linewidth=3.5)

# Elastic modulus annotation
text!(ax, yield_strain + 0.02, yield_stress * 0.5; text="E ≈ 200 GPa\n(elastic modulus)",
      color=INK, fontsize=14, align=(:left, :center))

# Critical points
scatter!(ax, [yield_point_strain], [yield_point_stress];
         color=ANYPLOT_AMBER, markersize=22, strokewidth=2, strokecolor=PAGE_BG)
text!(ax, yield_point_strain, yield_point_stress - 26; text="Yield point\n(0.2% offset)",
      color=INK, fontsize=13, align=(:left, :top))

scatter!(ax, [uts_strain], [uts_stress];
         color=IMPRINT_PALETTE[3], markersize=22, strokewidth=2, strokecolor=PAGE_BG)
text!(ax, uts_strain, uts_stress + 16; text="UTS",
      color=INK, fontsize=13, align=(:center, :bottom))

scatter!(ax, [fracture_strain], [fracture_stress];
         color=IMPRINT_PALETTE[5], markersize=24, marker=:xcross, strokewidth=3)
text!(ax, fracture_strain, fracture_stress - 26; text="Fracture",
      color=INK, fontsize=13, align=(:right, :top))

# --- Save ------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit=2)
