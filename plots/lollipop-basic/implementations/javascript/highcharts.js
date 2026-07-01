// anyplot.ai
// lollipop-basic: Basic Lollipop Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.0
// Quality: 87/100 | Created: 2026-07-01

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Data — Q1 units sold by tech product category (thousands), sorted ascending
const data = [
    { category: "Smart Watch", value: 12 },
    { category: "Tablet",      value: 18 },
    { category: "Drone",       value: 24 },
    { category: "Speaker",     value: 31 },
    { category: "Camera",      value: 38 },
    { category: "Monitor",     value: 45 },
    { category: "Keyboard",    value: 52 },
    { category: "Headphones",  value: 63 },
    { category: "Laptop",      value: 78 },
    { category: "Smartphone",  value: 94 },
];

const categories = data.map(d => d.category);
const stemValues = data.map(d => d.value);

// Scatter points — top performer gets a larger dot for emphasis
const dotValues = data.map((d, i) => ({
    y: d.value,
    marker: i === data.length - 1 ? { radius: 12 } : undefined,
}));

Highcharts.chart("container", {
    chart: {
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" },
        spacing: [40, 30, 40, 30],
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: "lollipop-basic · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
        margin: 30,
    },
    xAxis: {
        categories: categories,
        title: {
            text: "Product Category",
            style: { color: t.inkSoft, fontSize: "16px" },
        },
        lineColor: t.inkSoft,
        tickColor: "transparent",
        gridLineWidth: 0,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    },
    yAxis: {
        title: {
            text: "Units Sold (thousands)",
            style: { color: t.inkSoft, fontSize: "16px" },
        },
        gridLineColor: t.grid,
        lineColor: "transparent",
        tickColor: "transparent",
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
        min: 0,
    },
    legend: { enabled: false },
    plotOptions: {
        series: { animation: false },
        column: {
            borderWidth: 0,
            pointWidth: 3,
            groupPadding: 0,
            pointPadding: 0,
            enableMouseTracking: false,
        },
        scatter: {
            marker: {
                radius: 9,
                symbol: "circle",
                lineWidth: 2,
                lineColor: t.pageBg,
            },
            dataLabels: {
                enabled: true,
                formatter: function () { return this.y + "K"; },
                style: {
                    color: t.ink,
                    fontSize: "11px",
                    fontWeight: "400",
                    textOutline: "none",
                },
                verticalAlign: "bottom",
                y: -14,
            },
        },
    },
    tooltip: {
        formatter: function () {
            return "<b>" + categories[this.x] + "</b><br/>Units Sold: <b>" + this.y + "K</b>";
        },
    },
    series: [
        {
            type: "column",
            name: "Stem",
            data: stemValues,
            color: t.palette[0],
        },
        {
            type: "scatter",
            name: "Units Sold",
            data: dotValues,
            color: t.palette[0],
        },
    ],
});
