// anyplot.ai
// bifurcation-basic: Bifurcation Diagram for Dynamical Systems
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-17

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data: logistic map x(n+1) = r * x(n) * (1 - x(n)) -------------------
const R_MIN = 2.5;
const R_MAX = 4.0;
const N_R = 1000;
const TRANSIENT = 200;
const STABLE = 100;

const data = [];
for (let i = 0; i <= N_R; i++) {
    const r = R_MIN + (R_MAX - R_MIN) * (i / N_R);
    let x = 0.5;
    for (let j = 0; j < TRANSIENT; j++) x = r * x * (1 - x);
    for (let j = 0; j < STABLE; j++) {
        x = r * x * (1 - x);
        data.push([r, x]);
    }
}

// Brand green (#009E73) at partial opacity for density-based visualization
const seriesColor = "rgba(0, 158, 115, 0.30)";

// --- Chart -----------------------------------------------------------------
Highcharts.chart("container", {
    chart: {
        type: "scatter",
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" }
    },
    credits: { enabled: false },
    title: {
        text: "bifurcation-basic · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" }
    },
    xAxis: {
        title: {
            text: "Growth Rate (r)",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        min: R_MIN,
        max: R_MAX,
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } }
    },
    yAxis: {
        title: {
            text: "Population (x)",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        min: 0,
        max: 1,
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } }
    },
    legend: { enabled: false },
    tooltip: { enabled: false },
    plotOptions: {
        series: {
            animation: false,
            enableMouseTracking: false,
            turboThreshold: 0
        },
        scatter: {
            marker: {
                radius: 0.7,
                symbol: "circle",
                lineWidth: 0
            }
        }
    },
    series: [{
        name: "x(r)",
        data: data,
        color: seriesColor
    }]
});
