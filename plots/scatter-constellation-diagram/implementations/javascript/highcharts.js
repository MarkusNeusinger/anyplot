// anyplot.ai
// scatter-constellation-diagram: Digital Modulation Constellation Diagram
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 89/100 | Created: 2026-06-18
//# anyplot-orientation: square
// anyplot.ai
// scatter-constellation-diagram: Digital Modulation Constellation Diagram
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-18

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG for reproducible Gaussian noise (Box-Muller)
let seed = 42195;
function lcg() {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 0x100000000;
}
function randn() {
    const u1 = lcg() || 1e-10;
    const u2 = lcg();
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// 16-QAM ideal constellation points at {-3,-1,+1,+3} × {-3,-1,+1,+3}
const LEVELS = [-3, -1, 1, 3];
const idealPoints = [];
for (const iVal of LEVELS) {
    for (const qVal of LEVELS) {
        idealPoints.push({ x: iVal, y: qVal });
    }
}

// Received symbols: 64 per ideal point with additive Gaussian noise (SNR ≈ 20 dB)
const NOISE_STD = 0.12;
const PER_POINT = 64;
const received = [];
let sumSqErr = 0;
for (const { x: ip, y: qp } of idealPoints) {
    for (let k = 0; k < PER_POINT; k++) {
        const iRx = ip + randn() * NOISE_STD;
        const qRx = qp + randn() * NOISE_STD;
        received.push({ x: iRx, y: qRx });
        sumSqErr += (iRx - ip) ** 2 + (qRx - qp) ** 2;
    }
}

// EVM = sqrt(mean squared error / mean signal power) × 100%
// Mean signal power for 16-QAM at ±1,±3: mean(I²+Q²) = 10
const AVG_SIGNAL_POWER = 10;
const evmPct = (Math.sqrt(sumSqErr / received.length / AVG_SIGNAL_POWER) * 100).toFixed(1);

// Decision boundaries for 16-QAM (midpoints between adjacent symbol levels)
const BOUNDARIES = [-2, 0, 2];
const makeDecisionLine = (val) => ({
    value: val,
    color: t.inkSoft,
    dashStyle: 'Dash',
    width: 1.2,
    zIndex: 2,
});

Highcharts.chart('container', {
    chart: {
        type: 'scatter',
        backgroundColor: 'transparent',
        animation: false,
        style: { fontFamily: 'inherit' },
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
        text: 'scatter-constellation-diagram · javascript · highcharts · anyplot.ai',
        style: { color: t.ink, fontSize: '21px', fontWeight: '600' },
    },
    subtitle: {
        text: `16-QAM · EVM = ${evmPct}%`,
        style: { color: t.inkSoft, fontSize: '14px' },
    },
    xAxis: {
        title: {
            text: 'In-Phase (I)',
            style: { color: t.inkSoft, fontSize: '16px' },
        },
        min: -4.5,
        max: 4.5,
        tickInterval: 1,
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineWidth: 0,
        labels: { style: { color: t.inkSoft, fontSize: '14px' } },
        plotLines: BOUNDARIES.map(makeDecisionLine),
    },
    yAxis: {
        title: {
            text: 'Quadrature (Q)',
            style: { color: t.inkSoft, fontSize: '16px' },
        },
        min: -4.5,
        max: 4.5,
        tickInterval: 1,
        lineColor: t.inkSoft,
        tickColor: t.inkSoft,
        gridLineWidth: 0,
        labels: { style: { color: t.inkSoft, fontSize: '14px' } },
        plotLines: BOUNDARIES.map(makeDecisionLine),
    },
    legend: {
        itemStyle: { color: t.inkSoft, fontSize: '14px' },
        itemHoverStyle: { color: t.ink },
        backgroundColor: t.elevatedBg,
        borderColor: t.grid,
        borderRadius: 3,
        borderWidth: 1,
    },
    plotOptions: {
        series: { animation: false, enableMouseTracking: false },
        scatter: { marker: { symbol: 'circle' } },
    },
    series: [
        {
            name: 'Received Symbols',
            data: received,
            color: t.palette[0],
            marker: {
                radius: 3,
                fillColor: t.palette[0] + '66',
                lineWidth: 0,
            },
        },
        {
            name: 'Ideal Points',
            data: idealPoints,
            color: t.palette[4],
            marker: {
                symbol: 'diamond',
                radius: 11,
                fillColor: t.palette[4],
                lineWidth: 2,
                lineColor: t.elevatedBg,
            },
        },
    ],
});
