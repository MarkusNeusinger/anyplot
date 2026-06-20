// anyplot.ai
// histogram-capability: Process Capability Plot with Specification Limits
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-20

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Deterministic data generation (LCG + Box-Muller) ----------------------
let seed = 42;
function lcgNext() {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    return seed / 4294967296;
}
function randn() {
    const u1 = Math.max(lcgNext(), 1e-15);
    const u2 = lcgNext();
    return Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
}

// Process parameters — shaft diameter (mm) quality control
const LSL = 9.95;
const USL = 10.05;
const TARGET = 10.00;
const TRUE_MEAN = 10.003;
const TRUE_SIGMA = 0.013;
const N = 200;

const measurements = Array.from({ length: N }, () => TRUE_MEAN + TRUE_SIGMA * randn());

// Sample statistics
const sampleMean = measurements.reduce((a, b) => a + b, 0) / N;
const sampleVariance = measurements.reduce((s, x) => s + (x - sampleMean) ** 2, 0) / (N - 1);
const sampleSigma = Math.sqrt(sampleVariance);

// Process capability indices
const cp = (USL - LSL) / (6 * sampleSigma);
const cpk = Math.min(
    (USL - sampleMean) / (3 * sampleSigma),
    (sampleMean - LSL) / (3 * sampleSigma)
);

// --- Histogram bins --------------------------------------------------------
const BIN_MIN = 9.92;
const BIN_MAX = 10.08;
const N_BINS = 20;
const BIN_WIDTH = (BIN_MAX - BIN_MIN) / N_BINS;

const binCounts = new Array(N_BINS).fill(0);
measurements.forEach(m => {
    const i = Math.floor((m - BIN_MIN) / BIN_WIDTH);
    if (i >= 0 && i < N_BINS) binCounts[i]++;
});

const histData = binCounts.map((count, i) => ({
    x: BIN_MIN + (i + 0.5) * BIN_WIDTH,
    y: count
}));

// --- Normal distribution curve (scaled to count space) ---------------------
function normalPDF(x, mu, sigma) {
    return Math.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * Math.sqrt(2 * Math.PI));
}

const CURVE_POINTS = 120;
const normalCurveData = Array.from({ length: CURVE_POINTS }, (_, i) => {
    const x = BIN_MIN + (i / (CURVE_POINTS - 1)) * (BIN_MAX - BIN_MIN);
    const y = N * BIN_WIDTH * normalPDF(x, sampleMean, sampleSigma);
    return [x, y];
});

// --- Chart -----------------------------------------------------------------
const chart = Highcharts.chart("container", {
    chart: {
        type: "column",
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" }
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: "histogram-capability · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" }
    },
    subtitle: {
        text: `Shaft Diameter Measurements  ·  n = ${N}  ·  Mean = ${sampleMean.toFixed(4)} mm  ·  σ = ${sampleSigma.toFixed(4)} mm`,
        style: { color: t.inkSoft, fontSize: "14px" }
    },
    xAxis: {
        title: {
            text: "Shaft Diameter (mm)",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        tickInterval: 0.02,
        startOnTick: false,
        endOnTick: false,
        min: BIN_MIN,
        max: BIN_MAX,
        labels: {
            formatter: function () { return this.value.toFixed(2); },
            style: { color: t.inkSoft, fontSize: "14px" }
        },
        gridLineWidth: 0,
        plotBands: [
            {
                from: BIN_MIN,
                to: LSL,
                color: "rgba(174, 48, 48, 0.08)",
                zIndex: 0
            },
            {
                from: USL,
                to: BIN_MAX,
                color: "rgba(174, 48, 48, 0.08)",
                zIndex: 0
            }
        ],
        plotLines: [
            {
                color: "#AE3030",
                width: 3,
                value: LSL,
                dashStyle: "Dash",
                zIndex: 5,
                label: {
                    text: "LSL",
                    align: "left",
                    rotation: 0,
                    x: 5,
                    y: 20,
                    style: { color: "#AE3030", fontSize: "13px", fontWeight: "bold" }
                }
            },
            {
                color: "#AE3030",
                width: 3,
                value: USL,
                dashStyle: "Dash",
                zIndex: 5,
                label: {
                    text: "USL",
                    align: "right",
                    rotation: 0,
                    x: -5,
                    y: 20,
                    style: { color: "#AE3030", fontSize: "13px", fontWeight: "bold" }
                }
            },
            {
                color: "#BD8233",
                width: 2.5,
                value: TARGET,
                dashStyle: "ShortDot",
                zIndex: 4,
                label: {
                    text: "Target",
                    align: "left",
                    rotation: 0,
                    x: 5,
                    y: 50,
                    style: { color: "#BD8233", fontSize: "13px", fontWeight: "bold" }
                }
            }
        ]
    },
    yAxis: {
        title: {
            text: "Count",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        gridLineColor: t.grid,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
        min: 0
    },
    legend: {
        enabled: true,
        itemStyle: { color: t.inkSoft, fontSize: "14px" },
        itemHoverStyle: { color: t.ink }
    },
    tooltip: { enabled: false },
    plotOptions: {
        series: { animation: false },
        column: {
            pointRange: BIN_WIDTH,
            groupPadding: 0,
            pointPadding: 0,
            borderWidth: 0
        }
    },
    series: [
        {
            name: "Measurements",
            type: "column",
            data: histData,
            color: t.palette[0]
        },
        {
            name: "Normal Fit",
            type: "line",
            data: normalCurveData,
            color: t.palette[1],
            lineWidth: 3,
            marker: { enabled: false }
        }
    ]
});

// --- Cp / Cpk annotation box in plot area ----------------------------------
const BOX_W = 190, BOX_H = 70, BOX_PAD = 12, BOX_R = 5;
const boxX = chart.plotLeft + chart.plotWidth - BOX_W - BOX_PAD;
const boxY = chart.plotTop + BOX_PAD;

chart.renderer.rect(boxX, boxY, BOX_W, BOX_H, BOX_R).attr({
    fill: t.elevatedBg,
    stroke: t.inkSoft,
    "stroke-width": 1,
    zIndex: 7
}).add();

chart.renderer.text(`Cp = ${cp.toFixed(2)}`, boxX + BOX_W / 2, boxY + 28)
    .attr({ align: "center", zIndex: 8 })
    .css({ color: t.ink, fontSize: "15px", fontWeight: "600" })
    .add();

chart.renderer.text(`Cpk = ${cpk.toFixed(2)}`, boxX + BOX_W / 2, boxY + 56)
    .attr({ align: "center", zIndex: 8 })
    .css({ color: t.ink, fontSize: "15px", fontWeight: "600" })
    .add();
