// anyplot.ai
// recurrence-basic: Recurrence Plot for Nonlinear Time Series
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 86/100 | Created: 2026-06-10

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Logistic map in chaotic regime (r = 3.82, x0 = 0.4)
const N = 200;
const r = 3.82;
const ts = new Array(N);
ts[0] = 0.4;
for (let i = 1; i < N; i++) {
    ts[i] = r * ts[i - 1] * (1 - ts[i - 1]);
}

// Time-delay embedding: dimension d=2, delay tau=1
// Embedded vector at index i: [ts[i], ts[i+1]]
const M = N - 1;
const emb = new Array(M);
for (let i = 0; i < M; i++) {
    emb[i] = [ts[i], ts[i + 1]];
}

// Binary recurrence matrix: mark (i,j) where distance < epsilon
const eps = 0.15;
const epsSq = eps * eps;
const recData = [];
for (let i = 0; i < M; i++) {
    for (let j = 0; j < M; j++) {
        const dx = emb[i][0] - emb[j][0];
        const dy = emb[i][1] - emb[j][1];
        if (dx * dx + dy * dy < epsSq) {
            recData.push([i, j]);
        }
    }
}

// Chart
Highcharts.chart("container", {
    chart: {
        type: "scatter",
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" },
        spacing: [20, 20, 20, 10]
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: "recurrence-basic · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" }
    },
    xAxis: {
        title: {
            text: "Time Index i",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
        min: 0,
        max: M - 1,
        endOnTick: false
    },
    yAxis: {
        title: {
            text: "Time Index j",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
        min: 0,
        max: M - 1,
        endOnTick: false
    },
    legend: { enabled: false },
    tooltip: { enabled: false },
    plotOptions: {
        series: { animation: false },
        scatter: {
            turboThreshold: 100000,
            marker: {
                radius: 2,
                symbol: "square",
                states: { hover: { enabled: false } }
            }
        }
    },
    series: [{
        name: "Recurrent",
        data: recData,
        color: t.palette[0]
    }]
});
