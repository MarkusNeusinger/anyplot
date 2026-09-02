# anyplot.ai
# chernoff-basic: Chernoff Faces for Multivariate Data
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG      = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG  = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK          = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT     = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND        = colorant"#009E73"  # Imprint palette position 1 -- ALWAYS first series
const ANYPLOT_AMBER = colorant"#DDCC77" # warning / caution -- flags the outlier patient

# --- Chernoff face recipe -------------------------------------------------------
# A custom Makie recipe: `chernoffface!` is a reusable, self-contained glyph
# (face outline + eyes/pupils + eyebrows + nose + mouth + label) whose shape is
# entirely driven by declarative attributes. This leans on Makie's recipe
# system (`@recipe`, attribute-linked sub-plots) rather than a generic
# poly!/lines!/text! loop.
@recipe(ChernoffFace, cx, cy) do scene
    Attributes(
        face_width    = 0.5,
        face_height   = 0.5,
        eye_size      = 0.5,
        eye_spacing   = 0.5,
        eyebrow_slant = 0.5,
        nose_length   = 0.5,
        mouth_curve   = 0.5,
        mouth_width   = 0.5,
        rx_base       = 0.55,
        ry_base       = 0.68,
        facecolor     = :white,
        outlinecolor  = :black,
        outlinewidth  = 3.0,
        ink           = :black,
        ink_soft      = :gray,
        label         = "",
        labelcolor    = :gray,
        labelsize     = 13.0,
    )
end

function Makie.plot!(cf::ChernoffFace)
    cx = cf[1][]
    cy = cf[2][]

    rx = cf.rx_base[] * (0.75 + 0.55 * cf.face_width[])
    ry = cf.ry_base[] * (0.75 + 0.55 * cf.face_height[])

    θ_face = range(0, 2π; length = 80)
    face_pts = [Point2f(cx + rx * cos(t), cy + ry * sin(t)) for t in θ_face]
    poly!(cf, face_pts; color = cf.facecolor, strokecolor = cf.outlinecolor,
          strokewidth = cf.outlinewidth)

    eye_r  = 0.05 + 0.09 * cf.eye_size[]
    eye_dx = rx * (0.30 + 0.24 * cf.eye_spacing[])
    eye_y  = cy + ry * 0.15
    θ_eye  = range(0, 2π; length = 40)

    for side in (-1, 1)
        ex = cx + side * eye_dx
        eye_pts = [Point2f(ex + eye_r * cos(t), eye_y + eye_r * sin(t)) for t in θ_eye]
        poly!(cf, eye_pts; color = cf.facecolor, strokecolor = cf.ink, strokewidth = 2)
        pupil_pts = [Point2f(ex + 0.4 * eye_r * cos(t), eye_y + 0.4 * eye_r * sin(t)) for t in θ_eye]
        poly!(cf, pupil_pts; color = cf.ink, strokewidth = 0)
    end

    brow_half_len = rx * 0.32
    brow_y = eye_y + eye_r * 1.9
    brow_slope = (0.5 - cf.eyebrow_slant[]) * 0.32 * ry

    for (side, mirror) in ((-1, 1), (1, -1))
        bx = cx + side * eye_dx
        dy = mirror * brow_slope
        lines!(cf, [Point2f(bx - brow_half_len, brow_y - dy), Point2f(bx + brow_half_len, brow_y + dy)];
               color = cf.ink_soft, linewidth = 4)
    end

    nose_len = ry * (0.22 + 0.30 * cf.nose_length[])
    nose_top = cy + ry * 0.02
    lines!(cf, [Point2f(cx, nose_top), Point2f(cx, nose_top - nose_len)];
           color = cf.ink_soft, linewidth = 2.5)

    mouth_width = rx * (0.55 + 0.55 * cf.mouth_width[])
    mouth_base_y = cy - ry * 0.42
    mouth_a = (0.5 - cf.mouth_curve[]) * 0.9 * ry / max((mouth_width / 2)^2, 1e-6)
    mouth_xs = range(-mouth_width / 2, mouth_width / 2; length = 30)
    mouth_pts = [Point2f(cx + xv, mouth_base_y + mouth_a * xv^2) for xv in mouth_xs]
    lines!(cf, mouth_pts; color = cf.ink, linewidth = 3.5)

    text!(cf, cx, cy - ry - 0.16; text = cf.label, color = cf.labelcolor,
          fontsize = cf.labelsize, align = (:center, :top))

    cf
end

# --- Data: patient vital-sign profiles -----------------------------------------
n = 12
patient_ids = [string("P", lpad(i, 2, '0')) for i in 1:n]

resting_heart_rate = clamp.(72 .+ 12 .* randn(n), 50, 110)     # bpm            -> eye size
systolic_bp        = clamp.(122 .+ 14 .* randn(n), 95, 165)    # mmHg           -> face width
cholesterol        = clamp.(195 .+ 30 .* randn(n), 130, 280)   # mg/dL          -> eyebrow slant
bmi                = clamp.(26 .+ 4 .* randn(n), 18, 38)       # kg/m^2         -> face height
blood_glucose      = clamp.(100 .+ 18 .* randn(n), 75, 160)    # mg/dL          -> mouth curvature
sleep_hours        = clamp.(6.8 .+ 1.1 .* randn(n), 4.5, 9.0)  # hours          -> mouth width
respiratory_rate   = clamp.(15 .+ 2.5 .* randn(n), 11, 22)     # breaths/minute -> nose length
body_temperature   = clamp.(98.2 .+ 0.6 .* randn(n), 96.8, 100.4) # deg F       -> eye spacing

# Min-max normalize each variable to [0, 1] before mapping to a facial feature
eye_size_n    = (resting_heart_rate .- minimum(resting_heart_rate)) ./ (maximum(resting_heart_rate) - minimum(resting_heart_rate))
face_width_n  = (systolic_bp .- minimum(systolic_bp)) ./ (maximum(systolic_bp) - minimum(systolic_bp))
eyebrow_n     = (cholesterol .- minimum(cholesterol)) ./ (maximum(cholesterol) - minimum(cholesterol))
face_height_n = (bmi .- minimum(bmi)) ./ (maximum(bmi) - minimum(bmi))
mouth_curve_n = (blood_glucose .- minimum(blood_glucose)) ./ (maximum(blood_glucose) - minimum(blood_glucose))
mouth_width_n = (sleep_hours .- minimum(sleep_hours)) ./ (maximum(sleep_hours) - minimum(sleep_hours))
nose_len_n    = (respiratory_rate .- minimum(respiratory_rate)) ./ (maximum(respiratory_rate) - minimum(respiratory_rate))
eye_spacing_n = (body_temperature .- minimum(body_temperature)) ./ (maximum(body_temperature) - minimum(body_temperature))

# Flag the most extreme combined profile -- largest total deviation from the
# cohort midpoint (0.5) across all 8 normalized variables -- as a visual entry
# point into the comparison.
normalized = hcat(eye_size_n, face_width_n, eyebrow_n, face_height_n,
                   mouth_curve_n, mouth_width_n, nose_len_n, eye_spacing_n)
extremity = vec(sum((normalized .- 0.5) .^ 2; dims = 2))
outlier_idx = argmax(extremity)

# --- Grid layout: 4 columns x 3 rows -------------------------------------------
ncols, nrows = 4, 3
spacing_x, spacing_y = 2.0, 2.6

centers = Point2f[]
for i in 1:n
    row = div(i - 1, ncols)
    col = mod(i - 1, ncols)
    push!(centers, Point2f(col * spacing_x, -row * spacing_y))
end

rx_max = 0.55 * 1.30
ry_max = 0.68 * 1.30

# --- Figure -------------------------------------------------------------------
fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "chernoff-basic · julia · makie · anyplot.ai",
    titlesize         = 26,
    titlecolor        = INK,
    backgroundcolor   = PAGE_BG,
    aspect            = DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)

xlims!(ax, -rx_max - 0.3, (ncols - 1) * spacing_x + rx_max + 0.3)
ylims!(ax, -(nrows - 1) * spacing_y - ry_max - 0.55, ry_max + 0.3)

# --- Draw one Chernoff face per patient via the custom recipe -------------------
for i in 1:n
    is_outlier = i == outlier_idx
    chernoffface!(ax, centers[i][1], centers[i][2];
        face_width    = face_width_n[i],
        face_height   = face_height_n[i],
        eye_size      = eye_size_n[i],
        eye_spacing   = eye_spacing_n[i],
        eyebrow_slant = eyebrow_n[i],
        nose_length   = nose_len_n[i],
        mouth_curve   = mouth_curve_n[i],
        mouth_width   = mouth_width_n[i],
        facecolor     = ELEVATED_BG,
        outlinecolor  = is_outlier ? ANYPLOT_AMBER : BRAND,
        outlinewidth  = is_outlier ? 5.0 : 3.0,
        ink           = INK,
        ink_soft      = INK_SOFT,
        label         = patient_ids[i],
        labelcolor    = INK_SOFT,
        labelsize     = 13,
    )
end

# --- Save -----------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
