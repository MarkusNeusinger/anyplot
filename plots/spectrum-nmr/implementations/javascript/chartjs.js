// anyplot.ai
// spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-03
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Lorentzian lineshape: models sharp NMR resonance peaks
const lorentz = (x, c, hw, h) => h / (1 + ((x - c) / hw) ** 2);

// Chemical shift axis: 4.5 to -0.3 ppm, 4000 points
const N = 4000;
const ppmMin = -0.3;
const ppmMax = 4.5;
const ppmStep = (ppmMax - ppmMin) / (N - 1);

// 1H NMR of ethanol (400 MHz): J = 7 Hz = 0.0175 ppm coupling constant
const J = 0.0175;
const hw = 0.006; // Lorentzian half-width (~2.4 Hz at 400 MHz; J/hw ≈ 2.9 gives resolved multiplets)

const peakDefs = [
    // TMS internal standard at 0.00 ppm — singlet, small reference peak
    { c: 0.00,           hw,          h: 0.10, label: "TMS\n0.00 ppm" },
    // CH3 triplet at 1.25 ppm (3H, 1:2:1 intensity pattern)
    { c: 1.25 - J,       hw,          h: 0.42 },
    { c: 1.25,           hw,          h: 0.85, label: "CH₃\n1.25 ppm" },
    { c: 1.25 + J,       hw,          h: 0.42 },
    // OH singlet at 2.61 ppm (1H, broad due to fast proton exchange)
    { c: 2.61,           hw: hw * 2.5, h: 0.28, label: "OH\n2.61 ppm" },
    // CH2 quartet at 3.69 ppm (2H, 1:3:3:1 intensity pattern)
    { c: 3.69 - 1.5 * J, hw,          h: 0.20 },
    { c: 3.69 - 0.5 * J, hw,          h: 0.60, label: "CH₂\n3.69 ppm" },
    { c: 3.69 + 0.5 * J, hw,          h: 0.60 },
    { c: 3.69 + 1.5 * J, hw,          h: 0.20 },
];

// Compute spectrum intensities across the chemical shift axis
const chartData = Array.from({ length: N }, (_, i) => {
    const ppm = ppmMax - ppmStep * i;
    const y = peakDefs.reduce((sum, p) => sum + lorentz(ppm, p.c, p.hw, p.h), 0);
    return { x: ppm, y };
});

// Peaks that carry labels
const labeledPeaks = peakDefs.filter(p => p.label);

// Title with font size scaled to length (baseline 67 chars → 22px)
const titleText =
    "1H NMR Spectrum of Ethanol · spectrum-nmr · javascript · chartjs · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(22 * 67 / titleText.length));

// Fill the full canvas with the page background before Chart.js draws
const bgPlugin = {
    id: "bg",
    beforeDraw({ ctx, width, height }) {
        ctx.save();
        ctx.fillStyle = t.pageBg;
        ctx.fillRect(0, 0, width, height);
        ctx.restore();
    },
};

// Draw only bottom and left axis spines (L-shaped frame, scientific style)
const spinePlugin = {
    id: "spines",
    afterDatasetsDraw({ ctx, chartArea: { top, right, bottom, left } }) {
        ctx.save();
        ctx.strokeStyle = t.inkSoft;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(left, top);
        ctx.lineTo(left, bottom);
        ctx.moveTo(left, bottom);
        ctx.lineTo(right, bottom);
        ctx.stroke();
        ctx.restore();
    },
};

// Draw chemical group labels above each key peak
const labelPlugin = {
    id: "peakLabels",
    afterDatasetsDraw({ ctx, scales: { x: xs, y: ys } }) {
        ctx.save();
        ctx.textAlign = "center";
        ctx.fillStyle = t.ink;
        ctx.font = "600 13px sans-serif";
        labeledPeaks.forEach(({ c, h, label }) => {
            const px = xs.getPixelForValue(c);
            const lines = label.split("\n");
            lines.forEach((line, i) => {
                const py = ys.getPixelForValue(h + 0.09) - (lines.length - 1 - i) * 17;
                ctx.fillText(line, px, py);
            });
        });
        ctx.restore();
    },
};

// Mount
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

new Chart(canvas, {
    type: "scatter",
    data: {
        datasets: [{
            data: chartData,
            showLine: true,
            borderColor: t.palette[0],
            backgroundColor: t.palette[0] + "1a",
            borderWidth: 1.8,
            pointRadius: 0,
            fill: "origin",
            tension: 0,
        }],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
            title: {
                display: true,
                text: titleText,
                color: t.ink,
                font: { size: titleFontSize, weight: "600" },
                padding: { top: 8, bottom: 16 },
            },
            legend: { display: false },
            tooltip: { enabled: false },
        },
        scales: {
            x: {
                type: "linear",
                reverse: true,
                min: ppmMin,
                max: ppmMax,
                border: { display: false },
                ticks: {
                    color: t.inkSoft,
                    font: { size: 14 },
                    stepSize: 0.5,
                    callback: (v) => v.toFixed(1),
                },
                grid: { color: t.grid },
                title: {
                    display: true,
                    text: "Chemical Shift (ppm)",
                    color: t.ink,
                    font: { size: 16 },
                },
            },
            y: {
                min: 0,
                max: 1.05,
                border: { display: false },
                ticks: {
                    color: t.inkSoft,
                    font: { size: 14 },
                    callback: (v) => v.toFixed(1),
                },
                grid: { color: t.grid },
                title: {
                    display: true,
                    text: "Intensity (a.u.)",
                    color: t.ink,
                    font: { size: 16 },
                },
            },
        },
    },
    plugins: [bgPlugin, spinePlugin, labelPlugin],
});
