// anyplot.ai
// ecdf-basic: Basic ECDF Plot
// Library: highcharts 12.6.0 | JavaScript 22.23.0
// Quality: 87/100 | Created: 2026-06-25

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG random number generator
function lcg(seed) {
    let s = seed >>> 0;
    return () => {
        s = (Math.imul(1664525, s) + 1013904223) >>> 0;
        return s / 4294967296;
    };
}

// Box-Muller transform — normally distributed samples
function normalSamples(rng, mu, sigma, n) {
    const out = [];
    while (out.length < n) {
        const u1 = Math.max(rng(), 1e-10);
        const u2 = rng();
        const mag = sigma * Math.sqrt(-2 * Math.log(u1));
        out.push(mu + mag * Math.cos(2 * Math.PI * u2));
        if (out.length < n) out.push(mu + mag * Math.sin(2 * Math.PI * u2));
    }
    return out;
}

// ECDF as [x, proportion] step-function points (right-continuous convention)
// startX is a virtual point at proportion=0 before the first data value
function ecdfSeries(data, startX) {
    const sorted = [...data].sort((a, b) => a - b);
    const n = sorted.length;
    const pts = [[startX, 0]];
    sorted.forEach((x, i) => pts.push([x, (i + 1) / n]));
    return pts;
}

// Plant height (cm) under two growing conditions — 100 plants each
const standard = normalSamples(lcg(42), 15.0, 3.0, 100);
const enhanced = normalSamples(lcg(137), 18.5, 2.5, 100);

const allX = [...standard, ...enhanced];
const xMin = Math.min(...allX);
const xMax = Math.max(...allX);
const startX = xMin - (xMax - xMin) * 0.04;

const seriesStandard = ecdfSeries(standard, startX);
const seriesEnhanced = ecdfSeries(enhanced, startX);

// Title fits within 67 chars — use default 22px
const titleText = 'Plant Heights · ecdf-basic · javascript · highcharts · anyplot.ai';

Highcharts.chart('container', {
    chart: {
        type: 'line',
        backgroundColor: 'transparent',
        animation: false,
        style: { fontFamily: 'inherit' },
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: titleText,
        style: { color: t.ink, fontSize: '22px', fontWeight: '600' },
    },
    xAxis: {
        title: {
            text: 'Plant Height (cm)',
            style: { color: t.inkSoft, fontSize: '16px' },
        },
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineColor: t.grid,
        labels: { style: { color: t.inkSoft, fontSize: '14px' } },
    },
    yAxis: {
        title: {
            text: 'Cumulative Proportion',
            style: { color: t.inkSoft, fontSize: '16px' },
        },
        min: 0,
        max: 1,
        tickInterval: 0.25,
        gridLineColor: t.grid,
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        labels: {
            style: { color: t.inkSoft, fontSize: '14px' },
            formatter() { return `${Math.round(this.value * 100)}%`; },
        },
    },
    legend: {
        enabled: true,
        itemStyle: { color: t.inkSoft, fontSize: '14px' },
        itemHoverStyle: { color: t.ink },
    },
    plotOptions: {
        series: {
            animation: false,
            step: 'right',
            lineWidth: 2.5,
            marker: { enabled: false },
        },
    },
    series: [
        { name: 'Standard Nutrients', data: seriesStandard, color: t.palette[0] },
        { name: 'Enhanced Nutrients', data: seriesEnhanced, color: t.palette[1] },
    ],
});
