// anyplot.ai
// scatter-basic: Basic Scatter Plot
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 84/100 | Created: 2026-06-25

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// Data — marketing spend vs sales revenue, 120 companies, r ≈ 0.7
// LCG for deterministic generation (no seeded RNG in browser)
let seed = 42;
function lcg() {
    seed = (seed * 1664525 + 1013904223) & 0xffffffff;
    return (seed >>> 0) / 0xffffffff;
}
function randn() {
    const u = lcg() + 1e-10;
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * lcg());
}

const N = 120;
const data = [];
for (let i = 0; i < N; i++) {
    const spend = 10 + lcg() * 90;
    const revenue = 200 + 8 * spend + randn() * 100;
    data.push([
        Math.round(spend * 10) / 10,
        Math.round(revenue * 10) / 10
    ]);
}

// Chart
Highcharts.chart("container", {
    chart: {
        type: "scatter",
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" }
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: "scatter-basic · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" }
    },
    xAxis: {
        title: {
            text: "Marketing Spend ($ thousands)",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        gridLineWidth: 1,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } }
    },
    yAxis: {
        title: {
            text: "Sales Revenue ($ thousands)",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } }
    },
    legend: { enabled: false },
    plotOptions: {
        series: { animation: false },
        scatter: {
            opacity: 0.7,
            marker: {
                radius: 5,
                lineWidth: 1,
                lineColor: t.pageBg
            }
        }
    },
    series: [{
        name: "Companies",
        data: data
    }]
});
