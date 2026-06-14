// anyplot.ai
// bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-14
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;
const THEME = window.ANYPLOT_THEME;

// Zone colors follow fitness convention (semantic exception to ordinal Imprint order):
// Z1 grey (recovery), Z2 blue (endurance), Z3 green (aerobic),
// Z4 ochre (threshold), Z5 red (maximum)
const zoneColors = [
    THEME === "light" ? "#6B6A63" : "#A8A79F",  // Z1 Recovery  — Imprint muted anchor
    "#4467A3",                                    // Z2 Endurance — Imprint blue
    "#009E73",                                    // Z3 Aerobic   — Imprint brand green
    "#BD8233",                                    // Z4 Threshold — Imprint ochre
    "#AE3030",                                    // Z5 Maximum   — Imprint matte red
];

// Data: 60-minute criterium road race
const zones = [
    { label: "Z1",  name: "Recovery",  minutes: 8,  hrLow:  95, hrHigh: 124 },
    { label: "Z2",  name: "Endurance", minutes: 20, hrLow: 125, hrHigh: 148 },
    { label: "Z3",  name: "Aerobic",   minutes: 17, hrLow: 149, hrHigh: 163 },
    { label: "Z4",  name: "Threshold", minutes:  9, hrLow: 164, hrHigh: 178 },
    { label: "Z5",  name: "Maximum",   minutes:  6, hrLow: 179, hrHigh: 190 },
];

function toMMSS(minutes) {
    const m = Math.floor(minutes);
    const s = Math.round((minutes % 1) * 60);
    return `${m}:${String(s).padStart(2, "0")}`;
}

const seriesData = zones.map((z, i) => ({
    y: z.minutes,
    color: zoneColors[i],
    name: `${z.label} ${z.name}`,
}));

Highcharts.chart("container", {
    chart: {
        type: "column",
        backgroundColor: "transparent",
        animation: false,
        style: { fontFamily: "inherit" },
        spacingTop: 24,
        spacingBottom: 32,
        spacingLeft: 20,
        spacingRight: 20,
    },
    credits: { enabled: false },
    title: {
        text: "bar-heart-rate-zones · javascript · highcharts · anyplot.ai",
        style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
        margin: 8,
    },
    subtitle: {
        text: "60-minute criterium road race · distribution of intensity",
        style: { color: t.inkSoft, fontSize: "14px" },
        margin: 20,
    },
    xAxis: {
        categories: zones.map(z =>
            `${z.label} ${z.name}<br><span style="font-size:11px">${z.hrLow}–${z.hrHigh} bpm</span>`
        ),
        lineColor: t.inkSoft,
        tickColor: "transparent",
        labels: {
            useHTML: true,
            style: { color: t.inkSoft, fontSize: "14px", textAlign: "center" },
            y: 20,
        },
        gridLineWidth: 0,
    },
    yAxis: {
        title: {
            text: "Time (minutes)",
            style: { color: t.inkSoft, fontSize: "16px" },
        },
        gridLineColor: t.grid,
        labels: { style: { color: t.inkSoft, fontSize: "14px" } },
        min: 0,
        tickInterval: 5,
    },
    legend: { enabled: false },
    tooltip: { enabled: false },
    plotOptions: {
        series: { animation: false },
        column: {
            borderWidth: 0,
            borderRadius: 5,
            pointPadding: 0.12,
            groupPadding: 0.2,
            dataLabels: {
                enabled: true,
                formatter: function () {
                    return toMMSS(this.y);
                },
                style: {
                    color: t.ink,
                    fontSize: "18px",
                    fontWeight: "700",
                    textOutline: "none",
                },
                verticalAlign: "top",
                y: -28,
            },
        },
    },
    series: [{
        name: "Time in Zone",
        data: seriesData,
        colorByPoint: true,
    }],
});
