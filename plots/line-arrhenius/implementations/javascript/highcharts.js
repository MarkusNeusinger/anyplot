// anyplot.ai
// line-arrhenius: Arrhenius Plot for Reaction Kinetics
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: 81/100 | Created: 2026-06-24

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: first-order thermal decomposition with realistic experimental scatter ---
// Temperatures spanning 300–600 K; ln(k) values reflect real measurement noise (R² ≈ 0.98)
const temperatures = [300, 325, 350, 375, 400, 425, 450, 475, 500, 550, 600];
const lnK = [-8.6, -8.1, -5.3, -2.3, -1.9, 1.1, 0.9, 3.4, 4.5, 4.8, 7.5];
const invT = temperatures.map(T => 1 / T);

// --- Linear regression: ln(k) = ln(A) − (Ea/R)·(1/T) ---
const n = invT.length;
const sx = invT.reduce((a, b) => a + b, 0);
const sy = lnK.reduce((a, b) => a + b, 0);
const sxy = invT.reduce((a, x, i) => a + x * lnK[i], 0);
const sxx = invT.reduce((a, x) => a + x * x, 0);
const slope = (n * sxy - sx * sy) / (n * sxx - sx * sx);
const intercept = (sy - slope * sx) / n;
const yMean = sy / n;
const ssTot = lnK.reduce((a, y) => a + (y - yMean) ** 2, 0);
const ssRes = invT.reduce((a, x, i) => a + (lnK[i] - (slope * x + intercept)) ** 2, 0);
const r2 = 1 - ssRes / ssTot;

const eaOverR = Math.round(-slope);
const ea = (-slope * 8.314 / 1000).toFixed(1);

// Fit line from slightly extended x range
const xLo = Math.min(...invT) * 0.97;
const xHi = Math.max(...invT) * 1.03;
const fitLine = [
    [xLo, slope * xLo + intercept],
    [xHi, slope * xHi + intercept]
];

const scatterPoints = invT.map((x, i) => [x, lnK[i]]);

// --- Chart ---
const chart = Highcharts.chart("container", {
    chart: {
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" },
        marginBottom: 110
    },
    credits: { enabled: false },
    colors: t.palette,

    title: {
        text: "line-arrhenius · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" }
    },
    subtitle: {
        text: "Linear fit — Ea/R = " + eaOverR.toLocaleString() + " K | Ea ≈ " + ea + " kJ/mol | R² = " + r2.toFixed(3),
        style: { color: t.inkSoft, fontSize: "14px" }
    },

    xAxis: {
        title: {
            text: "1/T  (K⁻¹)",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: {
            useHTML: true,
            style: { color: t.inkSoft, fontSize: "13px", textAlign: "center" },
            formatter: function () {
                const T = Math.round(1 / this.value);
                return this.value.toFixed(4) +
                    "<br><span style=\"font-size:11px;color:" + t.inkSoft + "\">" + T + " K</span>";
            }
        }
    },

    yAxis: {
        title: {
            text: "ln(k)",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } }
    },

    legend: {
        itemStyle: { color: t.inkSoft, fontSize: "14px" },
        itemHoverStyle: { color: t.ink }
    },

    tooltip: { enabled: false },

    plotOptions: {
        series: { animation: false },
        line: {
            marker: { enabled: false },
            lineWidth: 2.5,
            states: { hover: { lineWidth: 2.5 } }
        },
        scatter: {
            marker: {
                radius: 7,
                symbol: "circle",
                lineColor: t.pageBg,
                lineWidth: 1.5
            }
        }
    },

    series: [
        {
            type: "scatter",
            name: "Measured k",
            data: scatterPoints,
            color: t.palette[0],
            zIndex: 2,
            marker: {
                radius: 7,
                symbol: "circle",
                lineColor: t.pageBg,
                lineWidth: 1.5
            }
        },
        {
            type: "line",
            name: "Arrhenius fit",
            data: fitLine,
            color: t.palette[2],
            lineWidth: 2.5,
            zIndex: 1,
            showInLegend: true
        }
    ]
});

// On-chart Ea/R annotation near the regression line midpoint
const xAnnot = xLo + 0.45 * (xHi - xLo);
const yAnnot = slope * xAnnot + intercept;
const pxAnnot = chart.xAxis[0].toPixels(xAnnot, false);
const pyAnnot = chart.yAxis[0].toPixels(yAnnot, false);
chart.renderer.text("Ea/R = " + eaOverR.toLocaleString() + " K", pxAnnot + 8, pyAnnot - 14)
    .attr({ align: "left", zIndex: 5 })
    .css({ color: t.inkSoft, fontSize: "13px" })
    .add();
