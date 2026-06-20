// anyplot.ai
// curve-oc: Operating Characteristic (OC) Curve
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-20

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Math helpers (fully deterministic — no RNG needed) ----------------------
function logFactorial(n) {
    let logF = 0;
    for (let i = 2; i <= n; i++) logF += Math.log(i);
    return logF;
}

function binomialPMF(n, k, p) {
    if (p <= 0) return k === 0 ? 1 : 0;
    if (p >= 1) return k === n ? 1 : 0;
    const logP = logFactorial(n) - logFactorial(k) - logFactorial(n - k)
               + k * Math.log(p) + (n - k) * Math.log(1 - p);
    return Math.exp(logP);
}

function binomialCDF(n, c, p) {
    let prob = 0;
    for (let k = 0; k <= c; k++) prob += binomialPMF(n, k, p);
    return Math.min(1, Math.max(0, prob));
}

// --- Sampling plans ----------------------------------------------------------
const plans = [
    { n: 50,  c: 1, label: "n=50, c=1"  },
    { n: 100, c: 2, label: "n=100, c=2" },
    { n: 150, c: 3, label: "n=150, c=3" },
];

const AQL  = 0.01;   // Acceptable Quality Level
const LTPD = 0.08;   // Lot Tolerance Percent Defective

const N_POINTS = 120;
const X_MAX = 0.15;
const xValues = Array.from({ length: N_POINTS }, (_, i) => i * X_MAX / (N_POINTS - 1));

const series = plans.map(({ n, c, label }) => ({
    name: label,
    type: "spline",
    data: xValues.map(p => [p, binomialCDF(n, c, p)]),
    lineWidth: 2.5,
    marker: { enabled: false },
}));

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
    chart: {
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" },
        marginRight: 30,
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: "curve-oc · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
    },
    xAxis: {
        title: {
            text: "Fraction Defective (p)",
            style: { color: t.inkSoft, fontSize: "16px" },
        },
        min: 0,
        max: X_MAX,
        tickAmount: 7,
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        labels: {
            style: { color: t.inkSoft, fontSize: "14px" },
            formatter: function () { return (this.value * 100).toFixed(0) + "%"; },
        },
        plotLines: [
            {
                value: AQL,
                color: t.inkSoft,
                dashStyle: "Dash",
                width: 1.5,
                label: {
                    text: "AQL (1%)",
                    style: { color: t.inkSoft, fontSize: "12px" },
                    rotation: 0,
                    y: -6,
                    x: 4,
                },
                zIndex: 3,
            },
            {
                value: LTPD,
                color: t.inkSoft,
                dashStyle: "Dash",
                width: 1.5,
                label: {
                    text: "LTPD (8%)",
                    style: { color: t.inkSoft, fontSize: "12px" },
                    rotation: 0,
                    y: -6,
                    x: 4,
                },
                zIndex: 3,
            },
        ],
    },
    yAxis: {
        title: {
            text: "Probability of Acceptance",
            style: { color: t.inkSoft, fontSize: "16px" },
        },
        min: 0,
        max: 1,
        tickAmount: 6,
        gridLineColor: t.grid,
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        labels: {
            style: { color: t.inkSoft, fontSize: "14px" },
            formatter: function () { return (this.value * 100).toFixed(0) + "%"; },
        },
        plotLines: [
            {
                value: 0.95,
                color: t.inkSoft,
                dashStyle: "ShortDot",
                width: 1,
                label: {
                    text: "α = 5% (producer’s risk)",
                    align: "right",
                    style: { color: t.inkSoft, fontSize: "12px" },
                    x: -6,
                },
                zIndex: 3,
            },
            {
                value: 0.10,
                color: t.inkSoft,
                dashStyle: "ShortDot",
                width: 1,
                label: {
                    text: "β = 10% (consumer’s risk)",
                    align: "right",
                    style: { color: t.inkSoft, fontSize: "12px" },
                    x: -6,
                },
                zIndex: 3,
            },
        ],
    },
    legend: {
        enabled: true,
        align: "right",
        verticalAlign: "middle",
        layout: "vertical",
        itemStyle: { color: t.inkSoft, fontSize: "14px", fontWeight: "normal" },
        itemHoverStyle: { color: t.ink },
        title: {
            text: "Sampling Plan",
            style: { color: t.inkSoft, fontSize: "12px", fontWeight: "normal" },
        },
    },
    plotOptions: {
        series: { animation: false },
        spline: {
            lineWidth: 2.5,
            states: { hover: { lineWidth: 2.5 } },
        },
    },
    series,
});
