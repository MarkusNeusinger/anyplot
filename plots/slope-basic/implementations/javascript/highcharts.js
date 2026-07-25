// anyplot.ai
// slope-basic: Basic Slope Chart (Slopegraph)
// Library: highcharts 12.6.0 | JavaScript 22.23.1
// Quality: 89/100 | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Customer satisfaction score (0-100) for 10 products, two survey waves.
const products = [
    { name: "CloudSync",   start: 62, end: 78 },
    { name: "DataVault",   start: 88, end: 91 },
    { name: "PixelPro",    start: 74, end: 65 },
    { name: "NetGuard",    start: 55, end: 72 },
    { name: "FlowStream",  start: 80, end: 76 },
    { name: "CoreLogic",   start: 69, end: 84 },
    { name: "ByteWave",    start: 91, end: 88 },
    { name: "GridPoint",   start: 58, end: 61 },
    { name: "LinkHub",     start: 77, end: 59 },
    { name: "TaskFlow",    start: 66, end: 82 },
];

const INCREASE = t.palette[0]; // brand green — profit/up/gain
const DECREASE = t.palette[4]; // matte red — loss/down
const FLAT = t.muted;

const lineOf = (p) => (p.end > p.start ? INCREASE : p.end < p.start ? DECREASE : FLAT);

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
    chart: {
        type: "line",
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" },
        marginLeft: 170,
        marginRight: 170,
    },
    credits: { enabled: false },
    title: {
        text: "slope-basic · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
    },
    xAxis: {
        categories: ["Survey Wave 1", "Survey Wave 2"],
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineWidth: 0,
        minPadding: 0.08,
        maxPadding: 0.08,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    },
    yAxis: {
        title: {
            text: "Customer Satisfaction Score",
            style: { color: t.inkSoft, fontSize: "16px" },
        },
        min: 40,
        max: 100,
        gridLineWidth: 0,
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    },
    legend: {
        enabled: true,
        align: "center",
        verticalAlign: "bottom",
        itemStyle: { color: t.inkSoft, fontSize: "14px", fontWeight: "normal" },
        itemHoverStyle: { color: t.ink },
    },
    plotOptions: {
        series: {
            animation: false,
            enableMouseTracking: false,
            marker: { enabled: true, radius: 5, symbol: "circle" },
            lineWidth: 2,
            dataLabels: {
                enabled: true,
                crop: false,
                overflow: "allow",
                style: { fontSize: "14px", fontWeight: "normal", textOutline: "none" },
            },
        },
    },
    series: [
        // Legend-only entries — real product lines below are excluded from the legend
        // since 10 individual names would overwhelm it; color already carries the story.
        { name: "Improved", type: "line", color: INCREASE, data: [], marker: { enabled: true } },
        { name: "Declined", type: "line", color: DECREASE, data: [], marker: { enabled: true } },
        ...products.map((p) => ({
            name: p.name,
            showInLegend: false,
            color: lineOf(p),
            data: [
                {
                    y: p.start,
                    dataLabels: {
                        align: "right",
                        x: -12,
                        color: t.inkSoft,
                        format: `${p.name} · ${p.start}`,
                    },
                },
                {
                    y: p.end,
                    dataLabels: {
                        align: "left",
                        x: 12,
                        color: t.inkSoft,
                        format: `${p.end} · ${p.name}`,
                    },
                },
            ],
        })),
    ],
});
