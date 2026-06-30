// anyplot.ai
// errorbar-basic: Basic Error Bar Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.0
// Quality: 86/100 | Created: 2026-06-30

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Enzyme activity measurements across temperature conditions (mean ± SD, n=12 per group)
const measurements = [
    { label: "20°C", mean: 18.4, error: 2.3 },
    { label: "25°C", mean: 31.7, error: 3.1 },
    { label: "30°C", mean: 52.3, error: 4.2 },
    { label: "35°C", mean: 67.8, error: 3.8 },
    { label: "37°C", mean: 74.5, error: 5.1 },
    { label: "40°C", mean: 71.2, error: 4.9 },
    { label: "45°C", mean: 48.6, error: 6.3 },
    { label: "50°C", mean: 22.1, error: 3.7 },
];

const categories = measurements.map(function (d) { return d.label; });
const means = measurements.map(function (d) { return d.mean; });

Highcharts.chart("container", {
    chart: {
        type: "line",
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" },
        events: {
            render: function () {
                const c = this;
                const series = c.series[0];

                // Clean up error bars from previous renders
                if (c._errorBars) {
                    c._errorBars.forEach(function (el) { el.destroy(); });
                }
                c._errorBars = [];

                series.points.forEach(function (point, i) {
                    const px = point.plotX + c.plotLeft;
                    const yH = c.yAxis[0].toPixels(measurements[i].mean + measurements[i].error);
                    const yL = c.yAxis[0].toPixels(measurements[i].mean - measurements[i].error);
                    const cap = 10;
                    const col = t.palette[0];
                    const sw = 2.5;

                    // Vertical stem
                    c._errorBars.push(
                        c.renderer.path(["M", px, yH, "L", px, yL])
                            .attr({ stroke: col, "stroke-width": sw, zIndex: 3 })
                            .add()
                    );
                    // Top cap
                    c._errorBars.push(
                        c.renderer.path(["M", px - cap, yH, "L", px + cap, yH])
                            .attr({ stroke: col, "stroke-width": sw, zIndex: 3 })
                            .add()
                    );
                    // Bottom cap
                    c._errorBars.push(
                        c.renderer.path(["M", px - cap, yL, "L", px + cap, yL])
                            .attr({ stroke: col, "stroke-width": sw, zIndex: 3 })
                            .add()
                    );
                });
            }
        }
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: "errorbar-basic · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" }
    },
    subtitle: {
        text: "Error bars represent ± 1 standard deviation",
        style: { color: t.inkSoft, fontSize: "14px" }
    },
    xAxis: {
        categories: categories,
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
        title: {
            text: "Temperature",
            style: { color: t.inkSoft, fontSize: "16px" }
        }
    },
    yAxis: {
        min: 0,
        title: {
            text: "Enzyme Activity (nmol/min)",
            style: { color: t.inkSoft, fontSize: "16px" }
        },
        gridLineColor: t.grid,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } }
    },
    legend: { enabled: false },
    tooltip: { enabled: false },
    plotOptions: {
        series: { animation: false },
        line: {
            lineWidth: 0,
            states: { hover: { lineWidth: 0 } },
            marker: {
                enabled: true,
                radius: 7,
                symbol: "circle",
                lineWidth: 2,
                lineColor: t.pageBg,
                fillColor: t.palette[0]
            }
        }
    },
    series: [{
        name: "Mean Enzyme Activity",
        data: means
    }]
});
