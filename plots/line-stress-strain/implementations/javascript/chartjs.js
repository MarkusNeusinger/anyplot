// anyplot.ai
// line-stress-strain: Engineering Stress-Strain Curve
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-21

const t = window.ANYPLOT_TOKENS;

// --- Data (deterministic, analytical mild steel tensile test) ---
const E_MPa = 200000; // Young's modulus (MPa)
const sigmaY = 250;   // upper yield stress (MPa)
const sigmaUTS = 400; // ultimate tensile strength (MPa)
const sigmaFx = 280;  // fracture stress (MPa)
const epsY = sigmaY / E_MPa; // elastic limit strain (~0.00125)
const epsPlate = 0.020;      // end of yield plateau
const epsUTS = 0.200;        // strain at UTS
const epsFx = 0.350;         // fracture strain

const mainCurve = [];

// Elastic region (linear, 0 → epsY)
for (let i = 0; i <= 25; i++) {
    const e = (i / 25) * epsY;
    mainCurve.push({ x: e, y: E_MPa * e });
}

// Upper yield drop to lower yield plateau (~240 MPa)
mainCurve.push({ x: epsY * 1.06, y: 240 });

// Yield plateau (epsY → epsPlate)
for (let i = 1; i <= 8; i++) {
    mainCurve.push({ x: epsY + (i / 8) * (epsPlate - epsY), y: 240 });
}

// Strain hardening — concave-down rise to UTS
for (let i = 1; i <= 35; i++) {
    const u = i / 35;
    const e = epsPlate + u * (epsUTS - epsPlate);
    const s = 240 + (sigmaUTS - 240) * (1 - Math.pow(1 - u, 1.8));
    mainCurve.push({ x: e, y: s });
}

// Necking — rapid drop to fracture
for (let i = 1; i <= 25; i++) {
    const u = i / 25;
    const e = epsUTS + u * (epsFx - epsUTS);
    const s = sigmaUTS - (sigmaUTS - sigmaFx) * Math.pow(u, 0.6);
    mainCurve.push({ x: e, y: s });
}

// 0.2% offset line: sigma = E * (eps - 0.002), from (0.002, 0) to just past yield
const offsetPts = [];
const epsOffEnd = 0.002 + (sigmaY + 15) / E_MPa;
for (let i = 0; i <= 14; i++) {
    const e = 0.002 + (i / 14) * (epsOffEnd - 0.002);
    offsetPts.push({ x: e, y: E_MPa * (e - 0.002) });
}

// Critical points: yield (0.2% offset), UTS, fracture
const epsYieldPt = 0.002 + 240 / E_MPa; // offset line meets yield plateau (~0.0032)
const critPts = [
    { x: epsYieldPt, y: 240 },
    { x: epsUTS, y: sigmaUTS },
    { x: epsFx, y: sigmaFx },
];

// --- Mount ---
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Plugin: region labels and critical-point annotations ---
const labelPlugin = {
    id: "stressStrainLabels",
    afterDraw(chart) {
        const ctx = chart.ctx;
        const xS = chart.scales.x;
        const yS = chart.scales.y;
        ctx.save();
        ctx.textAlign = "center";

        // Region shading labels
        ctx.font = "italic 15px system-ui, sans-serif";
        ctx.fillStyle = t.inkSoft;
        ctx.fillText("Elastic", xS.getPixelForValue(0.0005), yS.getPixelForValue(55));
        ctx.fillText("Yield Plateau", xS.getPixelForValue(0.0115), yS.getPixelForValue(218));
        ctx.fillText("Strain Hardening", xS.getPixelForValue(0.110), yS.getPixelForValue(268));
        ctx.fillText("Necking", xS.getPixelForValue(0.277), yS.getPixelForValue(358));

        // E = 200 GPa label — placed in open lower-left space
        ctx.font = "13px system-ui, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText("E = 200 GPa", xS.getPixelForValue(0.024), yS.getPixelForValue(140));

        // Critical point labels (matte red)
        ctx.fillStyle = t.palette[4];

        // Yield point — positioned above the red marker
        ctx.font = "bold 13px system-ui, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText("Yield Pt.", xS.getPixelForValue(epsYieldPt + 0.004), yS.getPixelForValue(265));
        ctx.font = "11px system-ui, sans-serif";
        ctx.fillText("(0.2% offset)", xS.getPixelForValue(epsYieldPt + 0.004), yS.getPixelForValue(250));

        // UTS
        ctx.font = "bold 13px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("UTS", xS.getPixelForValue(epsUTS), yS.getPixelForValue(sigmaUTS + 19));

        // Fracture
        ctx.textAlign = "right";
        ctx.fillText("Fracture", xS.getPixelForValue(epsFx - 0.004), yS.getPixelForValue(sigmaFx + 19));

        ctx.restore();
    },
};

// --- Chart ---
new Chart(canvas, {
    type: "scatter",
    data: {
        datasets: [
            {
                label: "Mild Steel",
                data: mainCurve,
                showLine: true,
                borderColor: t.palette[0],
                backgroundColor: "transparent",
                borderWidth: 3,
                pointRadius: 0,
                tension: 0.15,
            },
            {
                label: "0.2% Offset Line",
                data: offsetPts,
                showLine: true,
                borderColor: t.palette[2],
                backgroundColor: "transparent",
                borderWidth: 2,
                borderDash: [8, 6],
                pointRadius: 0,
                tension: 0,
            },
            {
                label: "Critical Points",
                data: critPts,
                pointRadius: 9,
                pointHoverRadius: 11,
                backgroundColor: t.palette[4],
                borderColor: t.pageBg,
                borderWidth: 2,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        layout: { padding: { top: 10, right: 24, bottom: 10, left: 10 } },
        plugins: {
            title: {
                display: true,
                text: "line-stress-strain · javascript · chartjs · anyplot.ai",
                color: t.ink,
                font: { size: 22, weight: "bold" },
                padding: { bottom: 18 },
            },
            legend: {
                labels: { color: t.ink, font: { size: 15 }, padding: 20 },
            },
        },
        scales: {
            x: {
                type: "linear",
                min: 0,
                max: 0.38,
                ticks: {
                    color: t.inkSoft,
                    font: { size: 13 },
                    stepSize: 0.05,
                    callback: (v) => v.toFixed(2),
                },
                grid: { color: t.grid },
                title: {
                    display: true,
                    text: "Engineering Strain (dimensionless)",
                    color: t.ink,
                    font: { size: 15 },
                    padding: { top: 8 },
                },
            },
            y: {
                min: 0,
                max: 450,
                ticks: {
                    color: t.inkSoft,
                    font: { size: 13 },
                    stepSize: 50,
                },
                grid: { color: t.grid },
                title: {
                    display: true,
                    text: "Engineering Stress (MPa)",
                    color: t.ink,
                    font: { size: 15 },
                    padding: { bottom: 8 },
                },
            },
        },
    },
    plugins: [labelPlugin],
});
