// anyplot.ai
// line-tanabe-sugano: Tanabe-Sugano Diagram for Crystal Field Theory
// Library: chartjs 4.4.7 | JavaScript 22.23.3
// Quality: 90/100 | Created: 2026-10-01
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data ------------------------------------------------------------------
// d² (V³⁺) in an octahedral field at C/B = 4.42. Term energies come from the
// Tanabe-Sugano matrices for d², in units of B with the Racah A dropped and
// Dq = Δo/10: every cubic term is a 1x1 or 2x2 block that is diagonalised
// exactly, so terms of the same symmetry and multiplicity (the two ³T₁g, the
// ¹Eg/¹T₂g pairs) stay as avoided crossings instead of crossing.
const RACAH_C = 4.42;
const eigenvalues = (upper, lower, coupling) => {
    const mean = (upper + lower) / 2;
    const half = Math.hypot((upper - lower) / 2, coupling);
    return [mean - half, mean + half];
};

// ³T₁g: t₂g²(-5B) and t₂g¹eg¹(+4B) mix through 6B; its lower root is the
// ground term for every field strength, so d² has no high-spin/low-spin
// crossover and the diagram needs no crossover line.
const groundTerm = (dq) => eigenvalues(-5 - 8 * dq, 4 + 2 * dq, 6)[0];

const terms = [
    { label: "³T₁g(F)", spinAllowed: true, energy: groundTerm },
    { label: "³T₂g", spinAllowed: true, energy: (dq) => -8 + 2 * dq },
    { label: "³T₁g(P)", spinAllowed: true, energy: (dq) => eigenvalues(-5 - 8 * dq, 4 + 2 * dq, 6)[1] },
    { label: "³A₂g", spinAllowed: true, energy: (dq) => -8 + 12 * dq },
    {
        label: "¹Eg",
        spinAllowed: false,
        energy: (dq) => eigenvalues(1 + 2 * RACAH_C - 8 * dq, 2 * RACAH_C + 12 * dq, 2 * Math.sqrt(3))[0],
    },
    {
        label: "¹T₂g",
        spinAllowed: false,
        energy: (dq) => eigenvalues(1 + 2 * RACAH_C - 8 * dq, 2 * RACAH_C + 2 * dq, 2 * Math.sqrt(3))[0],
    },
    { label: "¹T₁g", spinAllowed: false, energy: (dq) => 4 + 2 * RACAH_C + 2 * dq },
    {
        label: "¹A₁g",
        spinAllowed: false,
        energy: (dq) =>
            eigenvalues(10 + 5 * RACAH_C - 8 * dq, 8 + 4 * RACAH_C + 12 * dq, Math.sqrt(6) * (2 + RACAH_C))[0],
    },
];

// Δo/B from 0 to 40 in 321 steps — dense enough to keep avoided crossings smooth
const fieldStrengths = Array.from({ length: 321 }, (_, i) => i / 8);

// Imprint palette positions 1-8 in canonical order; spin-allowed terms (the ones
// sharing the ground term's triplet multiplicity, so the strong absorptions) are
// thick and solid, spin-forbidden singlets thin and dashed.
const datasets = terms.map((term, i) => ({
    label: term.label,
    data: fieldStrengths.map((fieldStrength) => ({
        x: fieldStrength,
        y: term.energy(fieldStrength / 10) - groundTerm(fieldStrength / 10),
    })),
    borderColor: t.palette[i],
    borderWidth: term.spinAllowed ? 6 : 3,
    borderDash: term.spinAllowed ? [] : [13, 10],
    pointRadius: 0,
    // the flat ground term runs along the x axis — let its full stroke draw
    clip: 8,
}));

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Term symbols sit at the right end of their own curve instead of in a legend,
// which keeps eight curves readable; labels are nudged apart vertically where
// curves converge (¹Eg and ¹T₂g end ~0.2 E/B apart).
const termLabels = {
    id: "termLabels",
    afterDatasetsDraw(chart) {
        const { ctx, chartArea, scales } = chart;
        const labels = chart.data.datasets
            .map((dataset) => ({
                text: dataset.label,
                color: dataset.borderColor,
                y: scales.y.getPixelForValue(dataset.data[dataset.data.length - 1].y),
            }))
            .sort((a, b) => a.y - b.y);
        labels.forEach((label, i) => {
            if (i > 0) label.y = Math.max(label.y, labels[i - 1].y + 28);
        });

        ctx.save();
        ctx.font = "600 20px Helvetica, Arial, sans-serif";
        ctx.textBaseline = "middle";
        labels.forEach((label) => {
            ctx.fillStyle = label.color;
            ctx.fillText(label.text, chartArea.right + 14, label.y);
        });
        ctx.restore();
    },
};

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
    type: "line",
    data: { datasets },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        layout: { padding: { right: 120, top: 6, bottom: 6, left: 6 } },
        plugins: {
            title: {
                display: true,
                text: "line-tanabe-sugano · javascript · chartjs · anyplot.ai",
                color: t.ink,
                font: { size: 26, weight: "500" },
                padding: { bottom: 4 },
            },
            subtitle: {
                display: true,
                text: "d² (V³⁺) in Oₕ, C/B = 4.42 · solid: spin-allowed triplets · dashed: spin-forbidden singlets",
                color: t.inkSoft,
                font: { size: 18 },
                padding: { bottom: 20 },
            },
            legend: { display: false },
        },
        scales: {
            x: {
                type: "linear",
                min: 0,
                max: 40,
                title: { display: true, text: "Δₒ/B — reduced ligand-field strength", color: t.ink, font: { size: 19 } },
                ticks: { color: t.inkSoft, font: { size: 16 }, stepSize: 5, padding: 8 },
                grid: { color: t.grid, tickLength: 0 },
                border: { color: t.grid },
            },
            y: {
                min: 0,
                max: 80,
                title: { display: true, text: "E/B — term energy above ground term", color: t.ink, font: { size: 19 } },
                ticks: { color: t.inkSoft, font: { size: 16 }, stepSize: 10, padding: 8 },
                grid: { color: t.grid, tickLength: 0 },
                border: { color: t.grid },
            },
        },
    },
    plugins: [termLabels],
});
