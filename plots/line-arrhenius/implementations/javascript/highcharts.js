// anyplot.ai
// line-arrhenius: Arrhenius Plot for Reaction Kinetics
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 81/100 | Created: 2026-06-24

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: first-order thermal decomposition with experimental scatter ---
// Temperatures spanning 300–600 K; ln(k) values include realistic lab scatter
const temperatures = [300, 325, 350, 375, 400, 425, 450, 475, 500, 550, 600];
const lnK = [-9.3, -6.5, -4.6, -2.4, -1.2, 0.3, 1.8, 2.6, 4.0, 5.4, 7.1];
const invT = temperatures.map(T => 1 / T);

// --- Linear regression: ln(k) = ln(A) − (Ea/R)·(1/T) ---
function linReg(xs, ys) {
    const n = xs.length;
    const sx = xs.reduce((a, b) => a + b, 0);
    const sy = ys.reduce((a, b) => a + b, 0);
    const sxy = xs.reduce((a, x, i) => a + x * ys[i], 0);
    const sxx = xs.reduce((a, x) => a + x * x, 0);
    const m = (n * sxy - sx * sy) / (n * sxx - sx * sx);
    const b = (sy - m * sx) / n;
    const yMean = sy / n;
    const ssTot = ys.reduce((a, y) => a + (y - yMean) ** 2, 0);
    const ssRes = xs.reduce((a, x, i) => a + (ys[i] - (m * x + b)) ** 2, 0);
    return { slope: m, intercept: b, r2: 1 - ssRes / ssTot };
}

const reg = linReg(invT, lnK);
const eaOverR = Math.round(-reg.slope);               // K
const ea = (-reg.slope * 8.314 / 1000).toFixed(1);   // kJ/mol

// Fit line from slightly extended x range
const xLo = Math.min(...invT) * 0.97;
const xHi = Math.max(...invT) * 1.03;
const fitLine = [
    [xLo, reg.slope * xLo + reg.intercept],
    [xHi, reg.slope * xHi + reg.intercept]
];

// Scatter data as [1/T, ln(k)] pairs
const scatterPoints = invT.map((x, i) => [x, lnK[i]]);

// --- Chart ---
Highcharts.chart("container", {
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
        text: "Linear fit — Ea/R = " + eaOverR.toLocaleString() + " K | Ea ≈ " + ea + " kJ/mol | R² = " + reg.r2.toFixed(3),
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
                    "<br><span style=\"font-size:11px;color:" + t.inkSoft + "\">" + T + " K</span>";
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
            type: "line",
            name: "Arrhenius fit",
            data: fitLine,
            color: t.palette[2],
            lineWidth: 2.5,
            zIndex: 1,
            showInLegend: true
        },
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
        }
    ]
});
