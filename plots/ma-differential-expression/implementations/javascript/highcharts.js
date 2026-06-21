// anyplot.ai
// ma-differential-expression: MA Plot for Differential Expression
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 86/100 | Created: 2026-06-21

const t = window.ANYPLOT_TOKENS;

// Muted color for non-significant genes (theme-adaptive)
const MUTED = window.ANYPLOT_THEME === "light" ? "#6B6A63" : "#A8A79F";

// Deterministic LCG — no seeded Math.random in browser
let seed = 42;
function lcg() {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 0x100000000;
}
function normal() {
    let u;
    do { u = lcg(); } while (u === 0);
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * lcg());
}

// Generate RNA-seq MA plot data (~5 000 genes)
const N = 5000;
const genes = [];
for (let i = 0; i < N; i++) {
    // Mean expression A: skewed so more genes land at moderate values
    const A = +(1 + Math.pow(lcg(), 0.55) * 13).toFixed(3);
    // Variance (fan shape): higher at low expression, tighter at high
    const sigma = Math.max(0.18, 1.7 / Math.sqrt(A + 0.5));
    // Slight systematic upward bias at low expression (realistic normalisation artefact)
    const bias = A < 4 ? 0.12 * (4 - A) / 4 : 0;
    const M = +(normal() * sigma + bias).toFixed(3);
    // Significance: genes with large |M| and sufficient coverage
    const absM = Math.abs(M);
    const sigScore = A > 2 ? (absM - 0.95) * 0.28 : 0;
    const significant = sigScore > 0 && lcg() < sigScore;
    genes.push({ A, M, significant });
}

// Partition into three series
const nonSig  = genes.filter(g => !g.significant).map(g => [g.A, g.M]);
const upReg   = genes.filter(g =>  g.significant && g.M > 0).map(g => [g.A, g.M]);
const downReg = genes.filter(g =>  g.significant && g.M < 0).map(g => [g.A, g.M]);

// LOESS-like smoothed trend: sliding window average over sorted genes
const sorted = [...genes].sort((a, b) => a.A - b.A);
const WIN = 480;
const STEP = 45;
const loess = [];
for (let i = 0; i + WIN <= sorted.length; i += STEP) {
    const chunk = sorted.slice(i, i + WIN);
    const avgA = +(chunk.reduce((s, g) => s + g.A, 0) / WIN).toFixed(3);
    const avgM = +(chunk.reduce((s, g) => s + g.M, 0) / WIN).toFixed(3);
    loess.push([avgA, avgM]);
}

// Title length = 65 chars — under 67, no scaling needed
const TITLE_SIZE = "22px";

Highcharts.chart("container", {
    chart: {
        type: "scatter",
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" },
        marginRight: 30,
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: "ma-differential-expression · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: TITLE_SIZE, fontWeight: "600" },
    },
    xAxis: {
        title: {
            text: "A — Mean Average Expression (log₂)",
            style: { color: t.inkSoft, fontSize: "16px" },
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    },
    yAxis: {
        title: {
            text: "M — Log₂ Fold Change",
            style: { color: t.inkSoft, fontSize: "16px" },
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
        plotLines: [
            {
                value: 0,
                color: t.inkSoft,
                width: 1.5,
                dashStyle: "Solid",
                zIndex: 4,
            },
            {
                value: 1,
                color: t.inkSoft,
                width: 1,
                dashStyle: "ShortDash",
                zIndex: 4,
                label: {
                    text: "+1 (2× up)",
                    align: "right",
                    style: { color: t.inkSoft, fontSize: "12px" },
                },
            },
            {
                value: -1,
                color: t.inkSoft,
                width: 1,
                dashStyle: "ShortDash",
                zIndex: 4,
                label: {
                    text: "−1 (2× down)",
                    align: "right",
                    style: { color: t.inkSoft, fontSize: "12px" },
                },
            },
        ],
    },
    legend: {
        enabled: true,
        align: "right",
        verticalAlign: "top",
        itemStyle: { color: t.inkSoft, fontSize: "14px" },
        itemHoverStyle: { color: t.ink },
        backgroundColor: t.elevatedBg,
        borderColor: t.grid,
        borderWidth: 1,
        borderRadius: 4,
        padding: 12,
    },
    tooltip: { enabled: false },
    plotOptions: {
        series: { animation: false },
        scatter: {
            marker: { symbol: "circle" },
        },
    },
    series: [
        {
            name: "Not significant",
            type: "scatter",
            data: nonSig,
            color: MUTED,
            opacity: 0.45,
            marker: { radius: 2 },
            enableMouseTracking: false,
        },
        {
            name: "Upregulated (padj < 0.05)",
            type: "scatter",
            data: upReg,
            color: t.palette[0],
            opacity: 0.85,
            marker: { radius: 3 },
            enableMouseTracking: false,
        },
        {
            name: "Downregulated (padj < 0.05)",
            type: "scatter",
            data: downReg,
            color: t.palette[4],
            opacity: 0.85,
            marker: { radius: 3 },
            enableMouseTracking: false,
        },
        {
            name: "LOESS bias trend",
            type: "spline",
            data: loess,
            color: t.amber,
            lineWidth: 2.5,
            marker: { enabled: false },
            enableMouseTracking: false,
        },
    ],
});
